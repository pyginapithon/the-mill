"""Bootstrap py_gate: refuse older than 3.10, allow 3.10+ (inject version; no live mill).

JOB: ootb-py-gate-import
SoR: docs/acceptance/ACCEPTANCE-OOTB-DOGFOOD-FIX-FIRST.md P0 #3
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.lib.py_gate import (
    MIN,
    exit_if_too_old,
    gate_message,
    python_too_old,
)


PKG = Path(__file__).resolve().parents[2] / "agent_coord"


@pytest.mark.parametrize("ver", [(3, 8), (3, 9), (2, 7), (3,), ()])
def test_python_too_old_refuses(ver):
    assert python_too_old(version=ver) is True


@pytest.mark.parametrize("ver", [(3, 10), (3, 11), (3, 12), (4, 0)])
def test_python_too_old_allows(ver):
    assert python_too_old(version=ver) is False


def test_gate_message_points_uv_312():
    msg = gate_message(version=(3, 8))
    assert "3.8" in msg
    assert "3.10" in msg
    assert "uv" in msg.lower()
    assert "3.12" in msg
    assert MIN == (3, 10)


def test_exit_if_too_old_exits_2(capsys):
    with pytest.raises(SystemExit) as ei:
        exit_if_too_old(version=(3, 8))
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "uv" in err.lower()
    assert "3.12" in err
    assert "TypeError" not in err
    assert "Traceback" not in err


def test_exit_if_too_old_allows_310_plus():
    assert exit_if_too_old(version=(3, 10)) is None
    assert exit_if_too_old(version=(3, 12)) is None


def _assert_no_union_pipe(src, label):
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        if "|" in code:
            raise AssertionError("%s:%d contains | : %r" % (label, i, line))


def test_py_gate_source_no_union_pipe():
    src = (PKG / "lib" / "py_gate.py").read_text(encoding="utf-8")
    _assert_no_union_pipe(src, "py_gate.py")


def test_init_preamble_gate_before_coord_import():
    src = (PKG / "__init__.py").read_text(encoding="utf-8")
    body = src
    dq = chr(34) * 3
    sq = chr(39) * 3
    if body.startswith(dq) or body.startswith(sq):
        q = body[:3]
        end = body.find(q, 3)
        assert end != -1
        body = body[end + 3 :]
    lines = [ln for ln in body.splitlines() if ln.strip()]
    assert lines[0].startswith("import sys"), lines[:5]
    joined = "\n".join(lines[:12])
    assert "sys.version_info" in joined
    assert "SystemExit" in joined or "sys.exit" in joined
    gate_at = src.find("sys.version_info")
    assert gate_at != -1
    assert "from .coord import" not in src
    assert "agent_coord.server" not in src[: src.find("from agent_coord.helpers")]
    _assert_no_union_pipe(src[:gate_at], "__init__.py preamble")


def test_main_calls_gate_before_coord():
    src = (PKG / "__main__.py").read_text(encoding="utf-8")
    gate_at = src.find("exit_if_too_old")
    err_at = src.find("helpers.errors import CoordError")
    assert gate_at != -1 and err_at != -1 and gate_at < err_at
    assert "from .coord import" not in src
