-- Existing book only. Not in apply_order.txt. A fresh wipe uses tables.sql.
-- One run brings name, the payload type columns, hold, mail_to, and
-- activity.affiliation_id to the tables.sql shape. A second run leaves that
-- shape in place. Watcher type name is removed.

DROP TRIGGER IF EXISTS activity_del_watchers;

DELIMITER //

CREATE TRIGGER activity_del_watchers AFTER DELETE ON activity
FOR EACH ROW
BEGIN
  IF IFNULL(@mill_keep_name_watchers, 0) = 0 AND OLD.type <> 'mail' THEN
    DELETE FROM watcher WHERE type = OLD.type AND id = OLD.id;
  END IF;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS mill_name_type_backfill;

DELIMITER //

CREATE PROCEDURE mill_name_type_backfill()
BEGIN
  DECLARE v_nopfx INT DEFAULT 0;
  DECLARE v_collide INT DEFAULT 0;
  DECLARE v_empty INT DEFAULT 0;
  DECLARE v_hold_dup INT DEFAULT 0;
  DECLARE v_payload INT DEFAULT 0;
  DECLARE v_n INT DEFAULT 0;
  DECLARE v_watch INT DEFAULT 0;
  DECLARE v_after INT DEFAULT 0;
  DECLARE v_ctype VARCHAR(255) DEFAULT '';
  DECLARE v_pk VARCHAR(64) DEFAULT '';
  DECLARE v_nullable VARCHAR(3) DEFAULT '';
  DECLARE v_rule VARCHAR(32) DEFAULT '';
  DECLARE v_idx VARCHAR(255) DEFAULT '';

  SELECT COLUMN_TYPE INTO v_ctype
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND COLUMN_NAME = 'type';
  SET v_ctype = IFNULL(v_ctype, '');

  IF (SELECT COUNT(*) FROM name WHERE id = 1) <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name id 1 is missing';
  END IF;

  SELECT COUNT(*) INTO v_hold_dup FROM (
    SELECT resource_id FROM hold GROUP BY resource_id HAVING COUNT(*) > 1
  ) d;
  IF v_hold_dup > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'hold resource_id collides';
  END IF;

  IF v_ctype = '' THEN
    SELECT COUNT(*) INTO v_nopfx FROM name
     WHERE name NOT REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';
  ELSEIF v_ctype LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_nopfx FROM name
     WHERE (type = 'name' OR type IS NULL)
       AND name NOT REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';
  END IF;
  IF v_nopfx > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'name.type is null; a row has no known prefix';
  END IF;

  SELECT COUNT(*) INTO v_empty FROM name
   WHERE name REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)$';
  IF v_empty > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name is empty after the prefix strip';
  END IF;

  SELECT COUNT(*) INTO v_collide FROM (
    SELECT 1 FROM name
    GROUP BY
      CASE
        WHEN name LIKE 'LABEL\_%' THEN 'label'
        WHEN name LIKE 'PROJ\_%' THEN 'project'
        WHEN name LIKE 'DESK\_%' THEN 'desk'
        WHEN name LIKE 'ROLE\_%' THEN 'role'
        WHEN name LIKE 'TREE\_%' THEN 'tree'
        WHEN name LIKE 'RES\_%' THEN 'res'
        ELSE type
      END,
      CASE
        WHEN name LIKE 'LABEL\_%' THEN SUBSTRING(name, 7)
        WHEN name LIKE 'PROJ\_%' THEN SUBSTRING(name, 6)
        WHEN name LIKE 'DESK\_%' THEN SUBSTRING(name, 6)
        WHEN name LIKE 'ROLE\_%' THEN SUBSTRING(name, 6)
        WHEN name LIKE 'TREE\_%' THEN SUBSTRING(name, 6)
        WHEN name LIKE 'RES\_%' THEN SUBSTRING(name, 5)
        ELSE name
      END
    HAVING COUNT(*) > 1
  ) d;
  IF v_collide > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'name (type, name) collides after the prefix strip';
  END IF;

  SET v_payload = 0;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM label WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tree' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM tree WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM mail WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM mail_to WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'todo' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM todo WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'join' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM `join` WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM hold WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'score' AND COLUMN_NAME = 'type')
     LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_n FROM score WHERE type = 'name';
    SET v_payload = v_payload + v_n;
  END IF;
  IF v_payload > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'payload type name row remains';
  END IF;

  SELECT COUNT(*) INTO v_n
    FROM activity a
    LEFT JOIN name n ON n.id = a.affiliation_id
   WHERE a.affiliation_id IS NOT NULL AND n.id IS NULL;
  IF v_n > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'activity affiliation is missing';
  END IF;

  IF v_ctype = '' THEN
    ALTER TABLE name
      ADD COLUMN type ENUM('desk','project','role','label','tree','res') NULL AFTER id;
    UPDATE name
       SET type = CASE
         WHEN name LIKE 'LABEL\_%' THEN 'label'
         WHEN name LIKE 'PROJ\_%' THEN 'project'
         WHEN name LIKE 'DESK\_%' THEN 'desk'
         WHEN name LIKE 'ROLE\_%' THEN 'role'
         WHEN name LIKE 'TREE\_%' THEN 'tree'
         WHEN name LIKE 'RES\_%' THEN 'res'
         ELSE type
       END
     WHERE type IS NULL
       AND name REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';
    SELECT COUNT(*) INTO v_n FROM name WHERE type IS NULL;
    IF v_n > 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'name.type is null; a row has no known prefix';
    END IF;
  END IF;

  IF v_ctype LIKE '%''name''%' THEN
    ALTER TABLE name
      MODIFY type ENUM('name','desk','project','role','label','tree','res') NOT NULL DEFAULT 'name';
    UPDATE name
       SET type = CASE
         WHEN name LIKE 'LABEL\_%' THEN 'label'
         WHEN name LIKE 'PROJ\_%' THEN 'project'
         WHEN name LIKE 'DESK\_%' THEN 'desk'
         WHEN name LIKE 'ROLE\_%' THEN 'role'
         WHEN name LIKE 'TREE\_%' THEN 'tree'
         WHEN name LIKE 'RES\_%' THEN 'res'
         ELSE type
       END
     WHERE type = 'name'
       AND name REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';
    SELECT COUNT(*) INTO v_n FROM name WHERE type = 'name' OR type IS NULL;
    IF v_n > 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'name.type is null; a row has no known prefix';
    END IF;
  END IF;

  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND INDEX_NAME = 'idx_name') > 0 THEN
    ALTER TABLE name DROP INDEX idx_name;
  END IF;

  UPDATE name
     SET name = CASE
       WHEN name LIKE 'LABEL\_%' THEN SUBSTRING(name, 7)
       WHEN name LIKE 'PROJ\_%' THEN SUBSTRING(name, 6)
       WHEN name LIKE 'DESK\_%' THEN SUBSTRING(name, 6)
       WHEN name LIKE 'ROLE\_%' THEN SUBSTRING(name, 6)
       WHEN name LIKE 'TREE\_%' THEN SUBSTRING(name, 6)
       WHEN name LIKE 'RES\_%' THEN SUBSTRING(name, 5)
       ELSE name
     END
   WHERE name REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';

  SELECT COUNT(*) INTO v_n FROM name
   WHERE name = '' OR name REGEXP '^(LABEL_|PROJ_|DESK_|ROLE_|TREE_|RES_)';
  SELECT COUNT(*) INTO v_collide FROM (
    SELECT type, name FROM name GROUP BY type, name HAVING COUNT(*) > 1
  ) d;
  IF v_n > 0 OR v_collide > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'name (type, name) collides after the prefix strip';
  END IF;

  ALTER TABLE name
    MODIFY type ENUM('desk','project','role','label','tree','res') NOT NULL;

  SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ',') INTO v_pk
    FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND INDEX_NAME = 'PRIMARY';
  IF v_pk = 'type,id' THEN
    IF (SELECT COUNT(*) FROM information_schema.STATISTICS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND INDEX_NAME = 'idx_id') = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name primary key has no idx_id';
    END IF;
    ALTER TABLE name DROP PRIMARY KEY, ADD PRIMARY KEY (id);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND INDEX_NAME = 'idx_id') > 0 THEN
    ALTER TABLE name DROP INDEX idx_id;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND INDEX_NAME = 'idx_type') = 0 THEN
    ALTER TABLE name ADD UNIQUE KEY idx_type (type, name);
  END IF;

  SELECT COLUMN_TYPE INTO v_ctype
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity' AND COLUMN_NAME = 'type';
  IF IFNULL(v_ctype, '') LIKE '%''name''%' THEN
    SELECT COUNT(*) INTO v_watch FROM watcher WHERE type = 'name';
    SET @mill_keep_name_watchers = 1;
    DELETE FROM activity WHERE type = 'name';
    SET @mill_keep_name_watchers = NULL;
    SELECT COUNT(*) INTO v_after FROM watcher WHERE type = 'name';
    IF v_watch <> v_after THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'name watchers changed';
    END IF;
  END IF;

  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold'
         AND CONSTRAINT_NAME = 'fk_hold_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE hold DROP FOREIGN KEY fk_hold_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'join'
         AND CONSTRAINT_NAME = 'fk_join_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE `join` DROP FOREIGN KEY fk_join_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label'
         AND CONSTRAINT_NAME = 'fk_label_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE label DROP FOREIGN KEY fk_label_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail'
         AND CONSTRAINT_NAME = 'fk_mail_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE mail DROP FOREIGN KEY fk_mail_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'score'
         AND CONSTRAINT_NAME = 'fk_score_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE score DROP FOREIGN KEY fk_score_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'todo'
         AND CONSTRAINT_NAME = 'fk_todo_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE todo DROP FOREIGN KEY fk_todo_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tree'
         AND CONSTRAINT_NAME = 'fk_tree_activity' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE tree DROP FOREIGN KEY fk_tree_activity;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to'
         AND CONSTRAINT_NAME = 'fk_mail_to_mail' AND CONSTRAINT_TYPE = 'FOREIGN KEY') > 0 THEN
    ALTER TABLE mail_to DROP FOREIGN KEY fk_mail_to_mail;
  END IF;

  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE activity MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE label MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tree' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE tree MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL;
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE mail MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'mail';
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE mail_to MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'mail';
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'todo' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE todo MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'todo';
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'join' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE `join` MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'join';
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE hold MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'hold';
  END IF;
  IF (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'score' AND COLUMN_NAME = 'type')
     <> 'enum(''mail'',''todo'',''join'',''hold'',''score'')' THEN
    ALTER TABLE score MODIFY type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'score';
  END IF;

  -- #216: mail, todo, join, hold, score are not re-linked to activity (payload first).
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label'
         AND CONSTRAINT_NAME = 'fk_label_activity') = 0 THEN
    ALTER TABLE label ADD CONSTRAINT fk_label_activity
      FOREIGN KEY (type, id) REFERENCES activity (type, id) ON DELETE CASCADE;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tree'
         AND CONSTRAINT_NAME = 'fk_tree_activity') = 0 THEN
    ALTER TABLE tree ADD CONSTRAINT fk_tree_activity
      FOREIGN KEY (type, id) REFERENCES activity (type, id);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to'
         AND CONSTRAINT_NAME = 'fk_mail_to_mail') = 0 THEN
    ALTER TABLE mail_to ADD CONSTRAINT fk_mail_to_mail
      FOREIGN KEY (type, id) REFERENCES mail (type, id) ON DELETE CASCADE;
  END IF;

  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to' AND COLUMN_NAME = 'affiliation_id') > 0 THEN
    IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to'
           AND CONSTRAINT_NAME = 'fk_mail_to_affiliation') > 0 THEN
      ALTER TABLE mail_to DROP FOREIGN KEY fk_mail_to_affiliation;
    END IF;
    IF (SELECT COUNT(*) FROM information_schema.STATISTICS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail_to' AND INDEX_NAME = 'idx_affiliation') > 0 THEN
      ALTER TABLE mail_to DROP INDEX idx_affiliation;
    END IF;
    ALTER TABLE mail_to DROP COLUMN affiliation_id;
  END IF;

  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND COLUMN_NAME = 'affiliation_id') > 0 THEN
    IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold'
           AND CONSTRAINT_NAME = 'fk_hold_affiliation') > 0 THEN
      ALTER TABLE hold DROP FOREIGN KEY fk_hold_affiliation;
    END IF;
    SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ',') INTO v_idx
      FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND INDEX_NAME = 'idx_hold';
    IF v_idx IS NOT NULL AND v_idx <> 'resource_id' THEN
      ALTER TABLE hold DROP INDEX idx_hold;
    END IF;
    ALTER TABLE hold DROP COLUMN affiliation_id;
  END IF;

  SELECT IS_NULLABLE INTO v_nullable
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND COLUMN_NAME = 'desk_id';
  IF v_nullable = 'NO' THEN
    ALTER TABLE hold MODIFY desk_id BIGINT UNSIGNED NULL;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
       WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'hold' AND INDEX_NAME = 'idx_hold') = 0 THEN
    ALTER TABLE hold ADD UNIQUE KEY idx_hold (resource_id);
  END IF;

  SELECT IS_NULLABLE INTO v_nullable
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity' AND COLUMN_NAME = 'affiliation_id';
  IF v_nullable = 'YES' THEN
    UPDATE activity SET affiliation_id = 1 WHERE affiliation_id IS NULL;
    IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity'
           AND CONSTRAINT_NAME = 'fk_activity_affiliation') > 0 THEN
      ALTER TABLE activity DROP FOREIGN KEY fk_activity_affiliation;
    END IF;
    ALTER TABLE activity MODIFY affiliation_id BIGINT UNSIGNED NOT NULL DEFAULT 1;
    ALTER TABLE activity ADD CONSTRAINT fk_activity_affiliation
      FOREIGN KEY (affiliation_id) REFERENCES name (id) ON DELETE RESTRICT;
  ELSE
    SELECT DELETE_RULE INTO v_rule
      FROM information_schema.REFERENTIAL_CONSTRAINTS
     WHERE CONSTRAINT_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'fk_activity_affiliation';
    IF IFNULL(v_rule, '') <> 'RESTRICT' THEN
      IF v_rule IS NOT NULL AND v_rule <> '' THEN
        ALTER TABLE activity DROP FOREIGN KEY fk_activity_affiliation;
      END IF;
      ALTER TABLE activity ADD CONSTRAINT fk_activity_affiliation
        FOREIGN KEY (affiliation_id) REFERENCES name (id) ON DELETE RESTRICT;
    END IF;
  END IF;

  SELECT COLUMN_TYPE INTO v_ctype
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'watcher' AND COLUMN_NAME = 'type';
  IF IFNULL(v_ctype, '') LIKE '%''name''%' THEN
    DELETE FROM watcher WHERE type = 'name';
    ALTER TABLE watcher
      MODIFY type ENUM('todo','join','hold','score') NOT NULL;
  END IF;

  SET @mill_keep_name_watchers = NULL;
END //

DELIMITER ;

CALL mill_name_type_backfill();
DROP PROCEDURE IF EXISTS mill_name_type_backfill;

DROP TRIGGER IF EXISTS activity_del_watchers;

DELIMITER //

CREATE TRIGGER activity_del_watchers AFTER DELETE ON activity
FOR EACH ROW
BEGIN
  IF OLD.type <> 'mail' THEN
    DELETE FROM watcher WHERE type = OLD.type AND id = OLD.id;
  END IF;
END //

DELIMITER ;
