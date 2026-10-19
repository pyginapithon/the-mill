"""F33 (skill-copy): tools/check_skill_copy.py: a desk skill copy that drifts from docs/protocol/skill.md fails."""
from __future__ import annotations

from tools import check_skill_copy as csc


def _src(tmp_path):
    src = tmp_path / "skill.md"
    src.write_text("---\nname: mill-desk\n---\n# Mill desk tools\nline\n", encoding="utf-8")
    return src


def test_repo_has_no_drifted_copy():
    assert csc.main([]) == 0


def test_same_copy_passes_and_crlf_is_the_same(tmp_path, capsys):
    src = _src(tmp_path)
    lf = tmp_path / "lf.md"
    lf.write_bytes(src.read_bytes())
    crlf = tmp_path / "crlf.md"
    crlf.write_bytes(src.read_bytes().replace(b"\n", b"\r\n"))
    assert csc.main(["--source", str(src), str(lf), str(crlf)]) == 0
    assert "2 copies, 0 differ" in capsys.readouterr().out


def test_drifted_copy_fails_with_diff_and_sync_line(tmp_path, capsys):
    src = _src(tmp_path)
    cp = tmp_path / "SKILL.md"
    cp.write_text(src.read_text(encoding="utf-8").replace("line", "old line"), encoding="utf-8")
    assert csc.main(["--source", str(src), str(cp)]) == 1
    out = capsys.readouterr().out
    assert "DRIFT" in out and "+old line" in out and "sync: cp " in out


def test_missing_copy_fails(tmp_path, capsys):
    src = _src(tmp_path)
    assert csc.main(["--source", str(src), str(tmp_path / "nope.md")]) == 1
    assert "MISSING" in capsys.readouterr().out


def test_bad_source_is_usage_error(tmp_path):
    assert csc.main(["--source", str(tmp_path / "none.md")]) == 2


def test_front_matter_name_marks_a_copy():
    assert csc._front_name("---\nname: mill-desk\ndescription: x\n---\nbody\n")
    assert not csc._front_name("---\nname: model-grok-bot\n---\nname: mill-desk\n")
    assert not csc._front_name("name: mill-desk\n")
