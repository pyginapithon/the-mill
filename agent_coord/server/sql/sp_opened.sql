-- opened table is gone. mill_opened_* stamps mail_to.opened (receipt).

DROP PROCEDURE IF EXISTS mill_opened_insert;
DROP PROCEDURE IF EXISTS mill_opened_select;
DROP PROCEDURE IF EXISTS mill_mail_open;

DELIMITER //

CREATE PROCEDURE mill_mail_open(
  IN p_mail BIGINT UNSIGNED,
  IN p_desk VARCHAR(64)
)
BEGIN
  DECLARE v_ts DATETIME(6);
  DECLARE v_desk BIGINT UNSIGNED;
  DECLARE v_n INT DEFAULT 0;
  DECLARE v_prev DATETIME(6);
  DECLARE v_receipt TINYINT DEFAULT 0;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  SET v_ts = MILL_NOW();
  SET v_desk = MILL_NAME_GET('desk', p_desk);
  SET v_prev = (
    SELECT opened FROM mail_to
     WHERE type = 'mail' AND id = p_mail AND desk_id = v_desk
     LIMIT 1
  );
  SET v_receipt = IFNULL((
    SELECT receipt FROM mail_to
     WHERE type = 'mail' AND id = p_mail AND desk_id = v_desk
     LIMIT 1
  ), 0);
  UPDATE mail_to
     SET opened = v_ts
   WHERE type = 'mail' AND id = p_mail AND desk_id = v_desk;
  SET v_n = ROW_COUNT();
  IF v_n > 0 THEN
    UPDATE activity SET updated = v_ts WHERE type = 'mail' AND id = p_mail;
  END IF;
  COMMIT;
  SELECT p_mail AS id, v_ts AS updated, p_mail AS mail_id, v_desk AS desk_id, v_n AS n,
         v_receipt AS receipt, v_ts AS opened,
         IF(v_prev IS NULL AND v_n > 0 AND v_receipt <> 0, 1, 0) AS push_receipt,
         m.created AS created, m.body AS body, sn.name AS sender, sn.type AS sender_type, dn.name AS desk, dn.type AS desk_type
    FROM mail m
    JOIN name sn ON sn.id = m.desk_id
    LEFT JOIN name dn ON dn.id = v_desk
   WHERE m.id = p_mail;
END //

CREATE PROCEDURE mill_opened_insert(
  IN p_mail BIGINT UNSIGNED,
  IN p_desk VARCHAR(64)
)
BEGIN
  CALL mill_mail_open(p_mail, p_desk);
END //

CREATE PROCEDURE mill_opened_select(
  IN p_mail BIGINT UNSIGNED,
  IN p_desk VARCHAR(64)
)
BEGIN
  SELECT 'mail' AS type, t.id, t.created, t.opened AS updated, t.desk_id AS desk_id,
         t.id AS mail_id, 1 AS n, dn.name AS desk, dn.type AS desk_type
    FROM mail_to t
    LEFT JOIN name dn ON dn.id = t.desk_id
   WHERE t.opened IS NOT NULL
     AND (p_mail IS NULL OR p_mail = 0 OR t.id = p_mail)
     AND (p_desk IS NULL OR p_desk = '' OR t.desk_id = MILL_NAME_GET('desk', p_desk));
END //

DELIMITER ;
