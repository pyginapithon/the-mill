DROP PROCEDURE IF EXISTS mill_join_upsert;
DROP PROCEDURE IF EXISTS mill_join_delete;
DROP PROCEDURE IF EXISTS mill_join_reset;
DROP PROCEDURE IF EXISTS mill_join_select;
DROP PROCEDURE IF EXISTS mill_join_doing;
DROP PROCEDURE IF EXISTS mill_join_connect;
DROP PROCEDURE IF EXISTS mill_join_socket;
DROP PROCEDURE IF EXISTS mill_join_lan;
DROP PROCEDURE IF EXISTS mill_join_wake_arm;
DROP PROCEDURE IF EXISTS mill_join_wake_off;
DROP PROCEDURE IF EXISTS mill_join_wake_state;
DROP PROCEDURE IF EXISTS mill_join_wake_target;

DELIMITER //

CREATE PROCEDURE mill_join_upsert(
  IN p_project    VARCHAR(64),
  IN p_desk       VARCHAR(64),
  IN p_role       VARCHAR(64),
  IN p_token_hash CHAR(64),
  IN p_doing      VARCHAR(512)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_proj BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  DECLARE v_have CHAR(64);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_proj = MILL_NAME_PUT('roster', p_project);
  SET v_desk = MILL_NAME_PUT('desk', p_desk);
  SET v_id = NULL;
  SET v_have = NULL;
  SELECT id, token_hash INTO v_id, v_have FROM `join` WHERE desk_id = v_desk LIMIT 1;
  IF v_have IS NOT NULL AND p_token_hash IS NOT NULL AND v_have <> p_token_hash THEN
    ROLLBACK;
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'desk live: token required (no steal)';
  END IF;
  IF v_id IS NULL THEN
    INSERT INTO `join` (updated, desk_id, token_hash, doing, delivery_mode)
    VALUES (v_ts, v_desk, p_token_hash, LEFT(IFNULL(p_doing, ''), 512), 'websocket');
    SET v_id = LAST_INSERT_ID();
  ELSE
    UPDATE `join`
       SET updated = v_ts,
           token_hash = IFNULL(p_token_hash, token_hash),
           doing = IF(p_doing IS NULL, doing, LEFT(p_doing, 512)),
           delivery_mode = IF(delivery_mode = 'polling', 'websocket', delivery_mode)
     WHERE id = v_id;
  END IF;
  INSERT IGNORE INTO member (name_id, desk_id) VALUES (1, v_desk);
  IF ROW_COUNT() = 1 THEN
    UPDATE name SET n = n + 1 WHERE id = 1;
  END IF;
  IF v_proj IS NOT NULL AND v_proj <> 1 THEN
    INSERT IGNORE INTO member (name_id, desk_id) VALUES (v_proj, v_desk);
    IF ROW_COUNT() = 1 THEN
      UPDATE name SET n = n + 1 WHERE id = v_proj;
    END IF;
  END IF;
  IF p_role IS NOT NULL AND p_role <> '' THEN
    IF LOWER(IFNULL(p_role, '')) = 'admin' THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Admin is not granted by join';
    END IF;
    SET @v_role := MILL_NAME_PUT('roster', p_role);
    INSERT IGNORE INTO member (name_id, desk_id) VALUES (@v_role, v_desk);
    IF ROW_COUNT() = 1 THEN
      UPDATE name SET n = n + 1 WHERE id = @v_role;
    END IF;
  END IF;
  CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  CALL mill_watcher_put('join', v_id, v_desk);
  COMMIT;
  SELECT v_id AS id, v_ts AS updated, v_desk AS desk_id, p_desk AS owner;
END //

CREATE PROCEDURE mill_join_delete(
  IN p_project VARCHAR(64),
  IN p_desk    VARCHAR(64)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  UPDATE `join` SET doing = '' WHERE desk_id = v_desk;
  SET v_id = (SELECT id FROM `join` WHERE desk_id = v_desk LIMIT 1);
  IF v_id IS NOT NULL THEN
    CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  END IF;
  COMMIT;
  SELECT p_desk AS owner, 'clocked-out' AS op;
END //

CREATE PROCEDURE mill_join_reset(
  IN p_project VARCHAR(64),
  IN p_desk    VARCHAR(64)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  -- #608: a retired desk resolves too, so reset still revokes its seat.
  SELECT id INTO v_desk FROM name WHERE type = 'desk' AND name = TRIM(p_desk) LIMIT 1;
  -- #96: reset is a disconnect stamp. Never DELETE join or its activity.
  -- #618: a reset seat keeps no webhook wake; the next holder arms its own.
  UPDATE `join` SET token_hash = NULL, doing = '', time_disconnect = v_ts,
         delivery_mode = IF(delivery_mode = 'webhook', 'websocket', delivery_mode),
         endpoint_url = NULL, endpoint_key = NULL
   WHERE desk_id = v_desk;
  SET v_id = (SELECT id FROM `join` WHERE desk_id = v_desk LIMIT 1);
  IF v_id IS NOT NULL THEN
    -- NULL roster: keep the seat's activity roster (not 1/Office).
    CALL mill_activity_put('join', v_id, v_ts, v_desk, NULL, MILL_WEIGHT('join'), NULL);
  END IF;
  COMMIT;
  SELECT p_desk AS owner, 'reset' AS op;
END //

CREATE PROCEDURE mill_join_select(IN p_project VARCHAR(64))
BEGIN
  DECLARE v_proj BIGINT UNSIGNED;
  IF p_project IS NULL OR p_project = '' THEN
    SELECT h.type, h.id, h.created, h.updated, h.desk_id, h.token_hash, h.doing,
           h.delivery_mode, h.endpoint_url, h.lan_ip, h.time_connect, h.time_disconnect,
           dsk.name AS desk, dsk.type AS desk_type,
           IF(ra.id IS NULL, NULL, JSON_OBJECT(
             'type', ra.type,
             'id', ra.id,
             'roster_id', ra.roster_id,
             'roster', aff.name,
             'roster_type', aff.type,
             'thing', CASE ra.type
               WHEN 'mail' THEN LEFT(ml.body, 80)
               WHEN 'todo' THEN LEFT(td.body, 80)
               WHEN 'hold' THEN hr.name
               WHEN 'score' THEN sc.kpi
               WHEN 'join' THEN jd.name
               ELSE NULL
             END
           )) AS recent_activity
    FROM `join` h
    LEFT JOIN name dsk ON dsk.id = h.desk_id
    LEFT JOIN LATERAL (
      SELECT type, id, roster_id, updated
      FROM activity USE INDEX (idx_desk_updated)
      WHERE desk_id = h.desk_id
      ORDER BY updated DESC
      LIMIT 1
    ) ra ON TRUE
    LEFT JOIN name aff ON aff.id = ra.roster_id
    LEFT JOIN mail ml ON ra.type = 'mail' AND ml.id = ra.id
    LEFT JOIN todo td ON ra.type = 'todo' AND td.id = ra.id
    LEFT JOIN hold ho ON ra.type = 'hold' AND ho.id = ra.id
    LEFT JOIN name hr ON hr.id = ho.resource_id
    LEFT JOIN score sc ON ra.type = 'score' AND sc.id = ra.id
    LEFT JOIN `join` js ON ra.type = 'join' AND js.id = ra.id
    LEFT JOIN name jd ON jd.id = js.desk_id
    ORDER BY h.updated DESC;
  ELSE
    SET v_proj = MILL_NAME_GET('roster', p_project);
    IF v_proj IS NULL THEN
      SET v_proj = 0;
    END IF;
    SELECT h.type, h.id, h.created, h.updated, h.desk_id, h.token_hash, h.doing,
           h.delivery_mode, h.endpoint_url, h.lan_ip, h.time_connect, h.time_disconnect,
           dsk.name AS desk, dsk.type AS desk_type,
           IF(ra.id IS NULL, NULL, JSON_OBJECT(
             'type', ra.type,
             'id', ra.id,
             'roster_id', ra.roster_id,
             'roster', aff.name,
             'roster_type', aff.type,
             'thing', CASE ra.type
               WHEN 'mail' THEN LEFT(ml.body, 80)
               WHEN 'todo' THEN LEFT(td.body, 80)
               WHEN 'hold' THEN hr.name
               WHEN 'score' THEN sc.kpi
               WHEN 'join' THEN jd.name
               ELSE NULL
             END
           )) AS recent_activity
    FROM `join` h
    JOIN member m ON m.desk_id = h.desk_id AND m.name_id = v_proj
    LEFT JOIN name dsk ON dsk.id = h.desk_id
    LEFT JOIN LATERAL (
      SELECT type, id, roster_id, updated
      FROM activity USE INDEX (idx_desk_updated)
      WHERE desk_id = h.desk_id
      ORDER BY updated DESC
      LIMIT 1
    ) ra ON TRUE
    LEFT JOIN name aff ON aff.id = ra.roster_id
    LEFT JOIN mail ml ON ra.type = 'mail' AND ml.id = ra.id
    LEFT JOIN todo td ON ra.type = 'todo' AND td.id = ra.id
    LEFT JOIN hold ho ON ra.type = 'hold' AND ho.id = ra.id
    LEFT JOIN name hr ON hr.id = ho.resource_id
    LEFT JOIN score sc ON ra.type = 'score' AND sc.id = ra.id
    LEFT JOIN `join` js ON ra.type = 'join' AND js.id = ra.id
    LEFT JOIN name jd ON jd.id = js.desk_id
    ORDER BY h.updated DESC;
  END IF;
END //

CREATE PROCEDURE mill_join_connect(
  IN p_desk VARCHAR(64)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_id = NULL;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  SELECT id INTO v_id FROM `join` WHERE desk_id = v_desk LIMIT 1;
  IF v_id IS NULL THEN
    ROLLBACK;
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'mill connect: desk has not joined';
  END IF;
  CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  COMMIT;
  SELECT v_id AS id, v_ts AS updated, v_desk AS desk_id;
END //

CREATE PROCEDURE mill_join_doing(
  IN p_project VARCHAR(64),
  IN p_desk    VARCHAR(64),
  IN p_doing   VARCHAR(512)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_id = NULL;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  UPDATE `join`
     SET updated = v_ts,
         doing = LEFT(IFNULL(p_doing, ''), 512)
   WHERE desk_id = v_desk;
  SELECT id INTO v_id FROM `join` WHERE desk_id = v_desk LIMIT 1;
  IF v_id IS NOT NULL THEN
    CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  END IF;
  COMMIT;
  SELECT v_id AS id, v_ts AS updated, v_desk AS desk_id, IFNULL(p_doing, '') AS doing;
END //

CREATE PROCEDURE mill_join_socket(
  IN p_desk VARCHAR(64),
  IN p_up   TINYINT
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  IF p_up = 1 THEN
    UPDATE `join` SET time_connect = v_ts, time_disconnect = NULL WHERE desk_id = v_desk;
  ELSE
    UPDATE `join` SET time_disconnect = v_ts WHERE desk_id = v_desk;
  END IF;
  SET v_id = (SELECT id FROM `join` WHERE desk_id = v_desk LIMIT 1);
  IF v_id IS NOT NULL THEN
    CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  END IF;
  COMMIT;
  SELECT v_id AS id, v_ts AS updated, v_desk AS desk_id, p_up AS up;
END //

CREATE PROCEDURE mill_join_lan(
  IN p_desk VARCHAR(64),
  IN p_ip   VARCHAR(45)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_desk BIGINT UNSIGNED;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  UPDATE `join` SET lan_ip = LEFT(IFNULL(p_ip, ''), 45) WHERE desk_id = v_desk;
  SET v_id = (SELECT id FROM `join` WHERE desk_id = v_desk LIMIT 1);
  IF v_id IS NOT NULL AND IFNULL(p_ip, '') <> '' THEN
    CALL mill_activity_put('join', v_id, v_ts, v_desk, 1, MILL_WEIGHT('join'), NULL);
  END IF;
  COMMIT;
  SELECT v_id AS id, v_ts AS updated, v_desk AS desk_id, p_ip AS lan_ip;
END //

-- #618 webhook wake. The URL is checked by the wall before arm (https, host
-- allowlist, no IP literal). updated = updated: arming is not a heartbeat.
CREATE PROCEDURE mill_join_wake_arm(
  IN p_desk VARCHAR(64),
  IN p_url  VARCHAR(512),
  IN p_key  VARCHAR(512),
  IN p_wake_on VARCHAR(16)
)
BEGIN
  DECLARE v_desk BIGINT UNSIGNED;
  IF IFNULL(p_url, '') = '' OR IFNULL(p_key, '') = '' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'wake arm: url and key required';
  END IF;
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  IF v_desk IS NULL OR NOT EXISTS (SELECT 1 FROM `join` WHERE desk_id = v_desk) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'wake: desk has not joined';
  END IF;
  IF IFNULL(p_wake_on, 'all') NOT IN ('all', 'addressed') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'wake arm: wake_on is all or addressed';
  END IF;
  UPDATE `join`
     SET delivery_mode = 'webhook', endpoint_url = p_url, endpoint_key = p_key,
         wake_on = IFNULL(p_wake_on, 'all'), updated = updated
   WHERE desk_id = v_desk;
  SELECT TRIM(p_desk) AS desk, 'webhook' AS delivery_mode, IFNULL(p_wake_on, 'all') AS wake_on;
END //

CREATE PROCEDURE mill_join_wake_off(
  IN p_desk VARCHAR(64)
)
BEGIN
  DECLARE v_desk BIGINT UNSIGNED;
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  IF v_desk IS NULL OR NOT EXISTS (SELECT 1 FROM `join` WHERE desk_id = v_desk) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'wake: desk has not joined';
  END IF;
  UPDATE `join`
     SET delivery_mode = IF(delivery_mode = 'webhook', 'websocket', delivery_mode),
         endpoint_url = NULL, endpoint_key = NULL, wake_on = 'all', updated = updated
   WHERE desk_id = v_desk;
  SELECT TRIM(p_desk) AS desk, 'off' AS wake;
END //

-- What a reader may see: armed or not and the host. Never the path or the key.
CREATE PROCEDURE mill_join_wake_state(
  IN p_desk VARCHAR(64)
)
BEGIN
  SELECT TRIM(p_desk) AS desk,
         (j.delivery_mode = 'webhook' AND j.endpoint_url IS NOT NULL AND j.endpoint_key IS NOT NULL) AS armed,
         IF(j.endpoint_url IS NULL, NULL,
            SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(j.endpoint_url, '://', -1), '/', 1), ':', 1)) AS host,
         j.wake_on
    FROM `join` j
    JOIN name d ON d.id = j.desk_id AND d.type = 'desk' AND d.deleted IS NULL
   WHERE d.name = TRIM(p_desk)
   LIMIT 1;
END //

-- POST time only: the one read that returns the key. A live, armed desk only.
CREATE PROCEDURE mill_join_wake_target(
  IN p_desk VARCHAR(64)
)
BEGIN
  SELECT j.endpoint_url, j.endpoint_key
    FROM `join` j
    JOIN name d ON d.id = j.desk_id AND d.type = 'desk' AND d.deleted IS NULL
   WHERE d.name = TRIM(p_desk)
     AND j.delivery_mode = 'webhook'
     AND j.endpoint_url IS NOT NULL
     AND j.endpoint_key IS NOT NULL
   LIMIT 1;
END //

DELIMITER ;
