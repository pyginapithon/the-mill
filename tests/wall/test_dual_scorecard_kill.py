"""kill-scorecard-md: no SCORECARD.md; Wall agent_kpi is only Last SoR. No live mill."""
from __future__ import annotations

from pathlib import Path

from agent_coord.lib.observe import load_line, markdown_kpis, snapshot

ROOT = Path(__file__).resolve().parents[2]

LIVE_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "install" / "HOST.md",
    ROOT / "docs" / "JOIN.md",
    ROOT / "docs" / "protocol" / "usecases.md",
]

FORBIDDEN = (
    "first table on the wall",
    "first table of `SCORECARD.md`",
    "first table = wall",
    "coord = SCORECARD.md first table",
    "Live file is this repo",
    "Numbers: [SCORECARD.md]",
    "auditor writes SCORECARD Last",
    "docs/SCORECARD.md",
    "docs/PRODUCT.md",
    "docs/PRODUCT-V1.md",
    "docs/RESTART.md",
    "docs/VISION.md",
    "docs/STORY-WALL-CONSCIOUSNESS.md",
    "docs/WALL-UI-LOCK.md",
    "docs/SPEND-INSTRUMENTATION.md",
)


def test_scorecard_md_gone():
    assert not (ROOT / "docs" / "DESIGN.md").exists()
    assert not (ROOT / "docs" / "RUNBOOK.md").exists()
    assert not (ROOT / "docs" / "SCORECARD.md").exists()
    assert not (ROOT / "agent_coord" / "web" / "briefings").exists()
    assert not (ROOT / "docs" / "SCORECARDS.md").exists()
    assert not (ROOT / "docs" / "PRODUCT.md").exists()
    assert not (ROOT / "docs" / "PRODUCT-V1.md").exists()
    assert not (ROOT / "docs" / "RESTART.md").exists()
    assert not (ROOT / "docs" / "VISION.md").exists()
    assert not (ROOT / "docs" / "STORY-WALL-CONSCIOUSNESS.md").exists()
    assert not (ROOT / "docs" / "WALL-UI-LOCK.md").exists()
    assert not (ROOT / "docs" / "SPEND-INSTRUMENTATION.md").exists()


def test_live_docs_do_not_point_at_deleted_md():
    hits = []
    for path in LIVE_PATHS:
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        for phrase in FORBIDDEN:
            if phrase.lower() in low:
                hits.append(f"{path.relative_to(ROOT)}: {phrase}")
    assert not hits, "stale pointers remain:\n" + "\n".join(hits)


def test_join_does_not_point_at_scorecard_table():
    join = (ROOT / "docs" / "JOIN.md").read_text(encoding="utf-8")
    assert "mill connect" in join
    assert "first table on the wall" not in join


def test_snapshot_scorecards_from_book_not_markdown():
    """Empty agent_kpi => empty wall scorecards without SCORECARD.md."""
    here = ROOT
    board = load_line("mill", here)
    assert not board.get("has_scorecard")
    empty_floor = {
        "events": [],
        "mailbox": [],
        "locks": [],
        "agents": [],
        "kpis": [],
        "needs": [],
        "issues": [],
        "spend": [],
        "projects": [],
    }
    view = snapshot(empty_floor, None)
    assert view.get("scorecards") == {}
    assert not view.get("kpis")


def test_markdown_kpis_parser_still_seeds_from_last_table_shape():
    """kpi-import seed parser still understands Last|Target tables (deprecated)."""
    text = "| KPI | Last | Target |\n|---|---|---|\n| False steal | 0 | **0** |\n"
    rows = markdown_kpis(text)
    assert rows and rows[0]["kpi"] == "false-steal"
    assert rows[0]["value"] == "0"
