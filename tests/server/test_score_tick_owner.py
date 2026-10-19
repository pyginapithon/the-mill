"""score_tick never looks Admin up as a desk; fallback resolves rosters by name."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]


def test_office_kpis_use_admin_upsert_desk_kpis_use_desk():
    from agent_coord.server import score_tick as st

    admin_calls, desk_calls = [], []
    cn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    cn.cursor.return_value = cur
    with patch("agent_coord.server.records.connect", return_value=cn), patch(
        "agent_coord.server.records.score.admin_upsert",
        side_effect=lambda _c, kpi, *a: admin_calls.append(kpi) or [{"id": 1}],
    ), patch(
        "agent_coord.server.records.score.upsert",
        side_effect=lambda _c, roster, desk, kpi, *a: desk_calls.append((roster, desk, kpi)) or [{"id": 2}],
    ), patch("agent_coord.server.records.db.call", return_value=[]):
        out = st.publish({st.KPI_TICKS: 1, "desks": {"d1": {st.KPI_TICKS: 1}}})
    assert out["ok"] is True and "fallback" not in out
    assert set(st.DESK_KPIS) | set(st.HOST_KPIS) <= set(admin_calls)
    assert desk_calls and all(desk == "d1" and roster == st.ROSTER for roster, desk, _ in desk_calls)
    assert all(desk != st.OWNER for _, desk, _ in desk_calls)


def test_no_upsert_names_admin_as_a_desk():
    src = (ROOT / "agent_coord" / "server" / "score_tick.py").read_text(encoding="utf-8")
    assert "ROSTER, OWNER, kpi" not in src and "ROSTER,\n                OWNER," not in src
    assert "desk_id=2" not in src


def test_fallback_resolves_rosters_by_name():
    from agent_coord.server import score_tick as st

    cur = MagicMock()
    cur.fetchone.return_value = (11, 22)
    cn = MagicMock()
    cn.cursor.return_value = cur
    st._publish_sql(cn, {st.KPI_TICKS: 3})
    updates = [c for c in cur.execute.call_args_list if "UPDATE score" in c.args[0]]
    assert len(updates) == 3
    assert all(c.args[1][-2:] == (11, 22) for c in updates)


def test_fallback_without_rosters_fails_closed():
    import pytest

    from agent_coord.server import score_tick as st

    cur = MagicMock()
    cur.fetchone.return_value = (1, None)
    cn = MagicMock()
    cn.cursor.return_value = cur
    with pytest.raises(RuntimeError, match="roster missing"):
        st._publish_sql(cn, {})
    assert not cn.commit.called


def test_regression_row_f19_documented():
    doc = (ROOT / "docs" / "protocol" / "records.md").read_text(encoding="utf-8")
    assert "Regression row F19 (score-tick-admin-roster)" in doc
    sql = (ROOT / "agent_coord" / "server" / "sql" / "sp_score.sql").read_text(encoding="utf-8")
    assert "DROP PROCEDURE IF EXISTS mill_score_admin_upsert;" in sql
    wipe = (ROOT / "agent_coord" / "server" / "sql" / "wipe.sql").read_text(encoding="utf-8")
    assert "DROP PROCEDURE IF EXISTS mill_score_admin_upsert;" in wipe
