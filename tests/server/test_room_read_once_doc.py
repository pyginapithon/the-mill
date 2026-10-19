"""F20 doc row and the no-cast-for-a-yes/no rule in mail-thread."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_regression_row_f20_documented():
    doc = (ROOT / "docs" / "protocol" / "verbs.md").read_text(encoding="utf-8")
    assert "Regression row F20 (room-read-once)" in doc


def test_mail_thread_does_not_build_the_cast_for_a_yes_no():
    src = (ROOT / "agent_coord" / "server" / "api" / "mill" / "rpc.py").read_text(encoding="utf-8")
    start = src.index("def _h_mail_thread(")
    body = src[start : src.index("\ndef ", start + 10)]
    assert "room_participants(" not in body
    assert "room_participant(" in body and "RoomRead(" in body
    assert "room_mail_nodes(" not in body and "room_tree_id(" not in body
