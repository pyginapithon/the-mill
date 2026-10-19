"""#398 session filename = sha256(desk_id)[:16]; slug only in .desk sidecar."""
from __future__ import annotations

from pathlib import Path

from agent_coord.client.tokens import (
    read_session_token,
    session_file_stem,
    write_session_token,
)


def test_stem_opaque_no_desk_name():
    stem = session_file_stem(42)
    assert len(stem) == 16
    assert stem.isalnum()
    assert "builder" not in stem
    assert "DESK" not in stem
    assert stem == session_file_stem("42")


def test_write_hashed_and_read_by_owner(tmp_path: Path):
    path = write_session_token("builder", "secret-tok", dest=tmp_path, desk_id=99)
    assert path.name == f"{session_file_stem(99)}.token"
    assert "builder" not in path.name
    meta = path.with_suffix(".desk")
    assert meta.is_file()
    assert meta.read_text(encoding="utf-8").strip() == "builder"
    assert read_session_token("builder", dest=tmp_path) == "secret-tok"
    assert read_session_token("builder", dest=tmp_path, desk_id=99) == "secret-tok"
    assert not (tmp_path / "session" / "builder.token").exists()


def test_legacy_write_without_desk_id(tmp_path: Path):
    path = write_session_token("alpha", "legacy-tok", dest=tmp_path)
    assert path.name == "alpha.token"
    assert read_session_token("alpha", dest=tmp_path) == "legacy-tok"
