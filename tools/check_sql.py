"""Compare pack SQL routine names to the live mill book.

Usage (on the wall host, pack installed, mill config in the usual place):

  python tools/check_sql.py
  python tools/check_sql.py --sql path/to/agent_coord/server/sql

Skips wipe.sql and tables.sql. Prints names and presence only.
Does not apply SQL and does not print config. Exit 1 when a pack routine
is missing. The comparison is case-sensitive, so MILL_NOW and mill_now differ.
Extra live routines are listed and do not fail the check.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import re
import sys
from pathlib import Path

SKIP = frozenset({"wipe.sql", "tables.sql"})
CREATE = re.compile(
    r"CREATE\s+(?:PROCEDURE|FUNCTION)\s+`?(mill_[A-Za-z0-9_]+)`?",
    re.I,
)
TABLES = ("human", "human_desk", "human_member")


def sql_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit)
    import agent_coord

    return Path(agent_coord.__file__).resolve().parent / "server" / "sql"


def pack_routines(root: Path) -> list[str]:
    order = (root / "apply_order.txt").read_text(encoding="utf-8").splitlines()
    found: list[str] = []
    for name in order:
        name = name.strip()
        if not name or name.startswith("#") or name in SKIP:
            continue
        text = (root / name).read_text(encoding="utf-8")
        found.extend(CREATE.findall(text))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare pack SQL to the live book.")
    parser.add_argument("--sql", default="", help="agent_coord/server/sql directory")
    args = parser.parse_args(argv)
    root = sql_root(args.sql)
    expected = pack_routines(root)
    exp = set(expected)

    import mysql.connector
    from agent_coord.config import mysql_kwargs

    cn = mysql.connector.connect(**mysql_kwargs())
    cur = cn.cursor(buffered=True)
    try:
        cur.execute("SELECT DATABASE()")
        database = cur.fetchone()[0]
        cur.execute(
            "SELECT ROUTINE_NAME FROM information_schema.ROUTINES "
            "WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME LIKE 'mill\\_%'"
        )
        live = {row[0] for row in cur.fetchall()}
        cur.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (%s, %s, %s)",
            TABLES,
        )
        tables = {row[0] for row in cur.fetchall()}
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'join' "
            "AND COLUMN_NAME = 'directory_sub'"
        )
        directory_sub = int(cur.fetchone()[0]) > 0
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'mail' "
            "AND CONSTRAINT_NAME = 'fk_mail_roster'"
        )
        mail_fk = int(cur.fetchone()[0]) > 0
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tree' "
            "AND INDEX_NAME = 'idx_type_lft'"
        )
        tree_idx = int(cur.fetchone()[0]) > 0
    finally:
        cur.close()
        cn.close()

    try:
        package = importlib.metadata.version("the-mill")
    except importlib.metadata.PackageNotFoundError:
        package = "unknown"
    missing = sorted(exp - live)
    extra = sorted(live - exp)
    print(f"package {package}")
    print(f"database {database}")
    print(f"sql {root}")
    print(f"pack_routines {len(exp)}")
    print(f"live_routines {len(live)}")
    print("missing " + (",".join(missing) or "none"))
    print("extra " + (",".join(extra) or "none"))
    for name in TABLES:
        print(f"table {name} {'yes' if name in tables else 'no'}")
    print("join.directory_sub " + ("yes" if directory_sub else "no"))
    print("fk_mail_roster " + ("yes" if mail_fk else "no"))
    print("tree.idx_type_lft " + ("yes" if tree_idx else "no"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
