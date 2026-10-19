-- 0.7.0 roster migration. Existing books only; not in apply_order.txt.
-- A fresh book uses tables.sql. Hard break: no aliases, no old-client support.
--
-- 1. Refuse when a project and a role share a name (an Admin renames one first).
-- 2. name.type: project and role become one type, roster. A roster is an
--    unordered list of desks; every member is equal (no rank, no order).
-- 3. Rename the old tag column to roster_id on activity, mail, todo and score,
--    with its indexes and foreign keys. No column is dropped.
-- 4. Drop the old watcher routine name and the orphans mill_wake and mill_heartbeat. migrate.py reloads
--    every routine after this file.
-- A second run finds nothing to do and changes nothing.

DROP PROCEDURE IF EXISTS mill_migrate_070_roster;

DELIMITER //

CREATE PROCEDURE mill_migrate_070_roster()
BEGIN
  DECLARE v_ctype VARCHAR(255) DEFAULT '';
  DECLARE v_clash TEXT DEFAULT NULL;
  DECLARE v_msg VARCHAR(255) DEFAULT '';

  SELECT COLUMN_TYPE INTO v_ctype
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'name' AND COLUMN_NAME = 'type';
  SET v_ctype = IFNULL(v_ctype, '');

  -- 1. Same-name project and role: refuse and list them.
  IF v_ctype LIKE '%''project''%' THEN
    SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR ',') INTO v_clash
      FROM (
        SELECT name FROM name
         WHERE type IN ('project', 'role')
         GROUP BY name
        HAVING COUNT(DISTINCT type) > 1
      ) c;
    IF v_clash IS NOT NULL THEN
      SET v_msg = LEFT(CONCAT('roster 070: rename one of each same-name project/role first: ', v_clash), 255);
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    -- 2. One name type.
    ALTER TABLE name MODIFY COLUMN type
      ENUM('desk','project','role','roster','label','tree','res') NOT NULL;
    UPDATE name SET type = 'roster' WHERE type IN ('project', 'role');
    ALTER TABLE name MODIFY COLUMN type
      ENUM('desk','roster','label','tree','res') NOT NULL;
  END IF;

  -- 3. Column, index and FK renames. Drop the FK, rename, add it back.
  IF EXISTS (SELECT 1 FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity'
                AND COLUMN_NAME = 'affiliation_id') THEN
    IF EXISTS (SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'activity'
                  AND CONSTRAINT_NAME = 'fk_activity_affiliation') THEN
      ALTER TABLE activity DROP FOREIGN KEY fk_activity_affiliation;
    END IF;
    ALTER TABLE activity RENAME COLUMN affiliation_id TO roster_id;
    IF EXISTS (SELECT 1 FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'activity'
                  AND INDEX_NAME = 'idx_affiliation') THEN
      ALTER TABLE activity RENAME INDEX idx_affiliation TO idx_roster;
    END IF;
    ALTER TABLE activity ADD CONSTRAINT fk_activity_roster
      FOREIGN KEY (roster_id) REFERENCES name (id) ON DELETE RESTRICT;
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail'
                AND COLUMN_NAME = 'affiliation_id') THEN
    IF EXISTS (SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'mail'
                  AND CONSTRAINT_NAME = 'fk_mail_affiliation') THEN
      ALTER TABLE mail DROP FOREIGN KEY fk_mail_affiliation;
    END IF;
    ALTER TABLE mail RENAME COLUMN affiliation_id TO roster_id;
    IF EXISTS (SELECT 1 FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail'
                  AND INDEX_NAME = 'idx_mail_affiliation') THEN
      ALTER TABLE mail RENAME INDEX idx_mail_affiliation TO idx_mail_roster;
    END IF;
    ALTER TABLE mail ADD CONSTRAINT fk_mail_roster
      FOREIGN KEY (roster_id) REFERENCES name (id) ON DELETE RESTRICT;
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'todo'
                AND COLUMN_NAME = 'affiliation_id') THEN
    IF EXISTS (SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'todo'
                  AND CONSTRAINT_NAME = 'fk_todo_affiliation') THEN
      ALTER TABLE todo DROP FOREIGN KEY fk_todo_affiliation;
    END IF;
    ALTER TABLE todo RENAME COLUMN affiliation_id TO roster_id;
    IF EXISTS (SELECT 1 FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'todo'
                  AND INDEX_NAME = 'idx_affiliation') THEN
      ALTER TABLE todo RENAME INDEX idx_affiliation TO idx_roster;
    END IF;
    ALTER TABLE todo ADD CONSTRAINT fk_todo_roster
      FOREIGN KEY (roster_id) REFERENCES name (id) ON DELETE RESTRICT;
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'score'
                AND COLUMN_NAME = 'affiliation_id') THEN
    IF EXISTS (SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'score'
                  AND CONSTRAINT_NAME = 'fk_score_affiliation') THEN
      ALTER TABLE score DROP FOREIGN KEY fk_score_affiliation;
    END IF;
    ALTER TABLE score RENAME COLUMN affiliation_id TO roster_id;
    ALTER TABLE score ADD CONSTRAINT fk_score_roster
      FOREIGN KEY (roster_id) REFERENCES name (id) ON DELETE RESTRICT;
  END IF;
END //

DELIMITER ;

CALL mill_migrate_070_roster();
DROP PROCEDURE IF EXISTS mill_migrate_070_roster;
DROP PROCEDURE IF EXISTS mill_watcher_affiliation;
-- Orphans from older packs: no source file creates them and nothing calls them.
-- mill_wake names the pre-0.7.0 column. A migrated book then has the same
-- routine set as a fresh tables.sql book.
DROP PROCEDURE IF EXISTS mill_wake;
DROP PROCEDURE IF EXISTS mill_heartbeat;
