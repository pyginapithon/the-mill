-- Stable short fingerprint for floor parts. Callers build p_material;
-- this function only hashes. Deterministic, no SQL.

DROP FUNCTION IF EXISTS MILL_FP;

DELIMITER //
CREATE FUNCTION MILL_FP(p_material VARCHAR(512)) RETURNS CHAR(16)
  DETERMINISTIC
  NO SQL
BEGIN
  RETURN LOWER(LEFT(SHA2(IFNULL(p_material, ''), 256), 16));
END //
DELIMITER ;
