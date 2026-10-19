"""sql/ script splitter: DELIMITER is client-only."""
from __future__ import annotations

from agent_coord.install.migrate import split_script, sql_apply_order


def test_split_delimiter_procedure() -> None:
    blob = """
DROP PROCEDURE IF EXISTS mill_x;
DELIMITER //
CREATE PROCEDURE mill_x()
BEGIN
  SELECT 1;
END //
DELIMITER ;
SELECT 2;
"""
    stmts = split_script(blob)
    assert any("CREATE PROCEDURE mill_x" in s for s in stmts)
    assert any(s.strip() == "SELECT 2" or s.strip() == "SELECT 2;" for s in stmts)
    assert all("DELIMITER" not in s.upper() for s in stmts)


def test_apply_order_starts_with_wipe() -> None:
    names = [p.name for p in sql_apply_order()]
    assert names[0] == "wipe.sql"
    assert "tables.sql" in names
    assert "tables.sql" in names
    assert "fn_now.sql" in names
    assert "sp_mail.sql" in names
