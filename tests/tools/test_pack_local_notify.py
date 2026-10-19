"""tools/pack_local.py --notify uses the current send form (mill send desk NAME --body-file)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _mod():
    spec = importlib.util.spec_from_file_location("pack_local", ROOT / "tools" / "pack_local.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_notify_cmd_parses_with_the_mill_send_verb(tmp_path) -> None:
    from agent_coord.__main__ import _build_parser

    mod = _mod()
    cmd = mod.notify_cmd("mill", tmp_path / "b.txt")
    assert cmd[:4] == ["mill", "send", "desk", "build-validator"]
    args = _build_parser().parse_args(cmd[1:])
    assert args.cmd == "send"
    assert args.body_file == str(tmp_path / "b.txt")
    assert args.roster == "the-mill"


def test_notify_writes_the_body_file_and_sends(monkeypatch, tmp_path) -> None:
    mod = _mod()
    seen: dict = {}

    def run(cmd, **kw):
        seen["cmd"] = cmd
        seen["body"] = Path(cmd[cmd.index("--body-file") + 1]).read_text(encoding="utf-8")

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/mill")
    monkeypatch.setattr(mod.subprocess, "run", run)
    mod.notify_build_validator(sha="abc1234", version="0.7.5", wheel=tmp_path / "the_mill-0.7.5-py3-none-any.whl")
    assert seen["cmd"][1:4] == ["send", "desk", "build-validator"]
    assert "the-mill 0.7.5" in seen["body"] and "abc1234" in seen["body"]
    assert "Re-measure" in seen["body"] and "Remasure" not in seen["body"]
    assert len(seen["body"]) <= 4096
    # positional body text is gone: the old form put the body after the desk name
    assert seen["body"] not in seen["cmd"]


def test_notify_skips_without_mill(monkeypatch, capsys, tmp_path) -> None:
    mod = _mod()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    mod.notify_build_validator(sha="a", version="v", wheel=tmp_path / "w.whl")
    assert "skipped" in capsys.readouterr().out
