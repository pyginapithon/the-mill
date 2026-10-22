DROP PROCEDURE IF EXISTS mill_name_delete;
DROP PROCEDURE IF EXISTS mill_name_rename;
DROP PROCEDURE IF EXISTS mill_name_reclaim;
DROP PROCEDURE IF EXISTS mill_name_host;

DELIMITER //

CREATE PROCEDURE mill_name_host(IN p_type VARCHAR(16), IN p_name VARCHAR(64))
BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_del DATETIME(6);
  SET v_id = MILL_NAME_GET(p_type, p_name);
  IF v_id IS NOT NULL THEN
    SELECT v_id AS id, TRIM(p_name) AS name, p_type AS name_type, 'exists' AS op;
  ELSE
    SET v_id = MILL_NAME_PUT(p_type, p_name);
    SELECT v_id AS id, TRIM(p_name) AS name, p_type AS name_type, 'created' AS op;
  END IF;
END //

CREATE PROCEDURE mill_name_delete(IN p_type VARCHAR(16), IN p_name VARCHAR(64))
BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_del DATETIME(6);
  SELECT id, deleted INTO v_id, v_del
    FROM name WHERE type = p_type AND name = TRIM(p_name) LIMIT 1;
  IF v_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name not found';
  END IF;
  IF v_id = 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'cannot delete Office';
  END IF;
  IF v_id = 2 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'cannot delete Admin';
  END IF;
  IF v_del IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name already retired';
  END IF;
  UPDATE name SET deleted = MILL_NOW() WHERE id = v_id;
  IF p_type = 'desk' THEN
    -- #608: a retired desk keeps no seat. Same stamp as mill_join_reset.
    UPDATE `join` SET token_hash = NULL, doing = '', time_disconnect = MILL_NOW()
     WHERE desk_id = v_id AND token_hash IS NOT NULL;
    -- #618: and no webhook wake.
    UPDATE `join` SET delivery_mode = IF(delivery_mode = 'webhook', 'websocket', delivery_mode),
           endpoint_url = NULL, endpoint_key = NULL, wake_on = 'all'
     WHERE desk_id = v_id AND endpoint_url IS NOT NULL;
  END IF;
  SELECT v_id AS id, TRIM(p_name) AS name, p_type AS name_type, 'deleted' AS op;
END //

CREATE PROCEDURE mill_name_rename(
  IN p_type VARCHAR(16),
  IN p_old VARCHAR(64),
  IN p_new VARCHAR(64)
)
BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_del DATETIME(6);
  DECLARE v_hit BIGINT UNSIGNED;
  SELECT id, deleted INTO v_id, v_del
    FROM name WHERE type = p_type AND name = TRIM(p_old) LIMIT 1;
  IF v_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name not found';
  END IF;
  IF v_del IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name retired: mill reclaim first';
  END IF;
  -- #722: the reserved rosters keep their names (the Admin guards read id 2).
  IF v_id = 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'cannot rename Office';
  END IF;
  IF v_id = 2 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'cannot rename Admin';
  END IF;
  SELECT id INTO v_hit
    FROM name WHERE type = p_type AND name = TRIM(p_new) LIMIT 1;
  IF v_hit IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name in use';
  END IF;
  UPDATE name SET name = TRIM(p_new) WHERE id = v_id;
  SELECT v_id AS id, TRIM(p_new) AS name, p_type AS name_type, 'renamed' AS op;
END //

CREATE PROCEDURE mill_name_reclaim(IN p_type VARCHAR(16), IN p_name VARCHAR(64))
BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  DECLARE v_del DATETIME(6);
  SELECT id, deleted INTO v_id, v_del
    FROM name WHERE type = p_type AND name = TRIM(p_name) LIMIT 1;
  IF v_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name not found';
  END IF;
  IF v_del IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name is live (not retired)';
  END IF;
  IF EXISTS (
    -- Block only a live seat: token set AND (the name is that desk OR the desk is a member of the name).
    SELECT 1 FROM `join`
     WHERE token_hash IS NOT NULL AND token_hash <> ''
       AND (desk_id = v_id
            OR desk_id IN (SELECT desk_id FROM member WHERE name_id = v_id))
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'name in use: mill reset first, then mill reclaim';
  END IF;
  UPDATE name SET deleted = NULL WHERE id = v_id;
  SELECT v_id AS id, TRIM(p_name) AS name, p_type AS name_type, 'reclaimed' AS op,
         (SELECT COUNT(*) FROM member WHERE name_id = v_id OR desk_id = v_id) AS members;
END //

DELIMITER ;
