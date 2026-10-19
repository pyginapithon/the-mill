"""Bridge parent match skips Windows console-script launchers (agent-ux 1214)."""
from __future__ import annotations

import os

from agent_coord.lib.proc import shell_parent_pid

SHELL = 500

# pid -> (parent pid, exe)
TREE = {
    SHELL: (4, "pwsh.exe"),
    # mill connect via launcher: pwsh -> mill.exe -> python.exe
    601: (SHELL, "mill.exe"),
    602: (601, "python.exe"),
    # mill todo via launcher: a fresh mill.exe each call
    611: (SHELL, "mill.exe"),
    612: (611, "python.exe"),
    # python -m agent_coord: pwsh -> python.exe
    621: (SHELL, "python.exe"),
    # venv: pwsh -> mill.exe -> venv python.exe (redirector) -> base python.exe
    631: (SHELL, "mill.exe"),
    632: (631, "python.exe"),
    633: (632, "python.exe"),
    # agent-coord alias launcher
    641: (SHELL, "Agent-Coord.EXE"),
}


def _win(ppid: int, *, in_venv: bool = False) -> int:
    return shell_parent_pid(ppid, platform="win32", table=TREE, in_venv=in_venv, python_exe="python.exe")


def test_mill_exe_connect_and_verb_agree_on_shell():
    # connect (python 602, parent 601) and verb (python 612, parent 611)
    assert _win(601) == SHELL
    assert _win(611) == SHELL


def test_python_m_parent_is_shell_already():
    assert _win(SHELL) == SHELL


def test_mixed_launchers_agree():
    assert _win(601) == _win(SHELL)


def test_case_insensitive_alias_launcher():
    assert _win(641) == SHELL


def test_venv_redirector_skipped_only_in_venv():
    assert _win(632, in_venv=True) == SHELL
    # Outside a venv a python parent is a real program (e.g. a harness): keep it.
    assert _win(632, in_venv=False) == 632


def test_shell_not_skipped():
    assert _win(SHELL, in_venv=True) == SHELL


def test_unknown_pid_falls_back():
    assert _win(9999) == 9999


def test_empty_table_falls_back():
    assert shell_parent_pid(601, platform="win32", table={}) == 601


def test_cycle_and_hop_limit_safe():
    loop = {1: (1, "mill.exe"), 2: (3, "mill.exe"), 3: (2, "mill.exe")}
    assert shell_parent_pid(1, platform="win32", table=loop, in_venv=False, python_exe="python.exe") == 1
    out = shell_parent_pid(2, platform="win32", table=loop, in_venv=False, python_exe="python.exe")
    assert out in (2, 3)


def test_noop_on_linux_and_mac():
    for plat in ("linux", "darwin"):
        assert shell_parent_pid(601, platform=plat, table=TREE) == 601


def test_default_is_getppid_off_windows(monkeypatch):
    monkeypatch.setattr(os, "getppid", lambda: 4242)
    if os.name != "nt":
        assert shell_parent_pid() == 4242


def test_bridge_written_by_mill_exe_connect_found_by_mill_exe_verb(tmp_path, monkeypatch):
    """End to end on the bridge file: both sides resolve the shell pid."""
    from agent_coord.client import ws

    path = tmp_path / "desk-a.ws.rpc"
    monkeypatch.setattr(ws, "rpc_bridge_path", lambda desk: path)
    monkeypatch.setattr(ws, "_rpc_bridge_files", lambda: [path])
    monkeypatch.setattr(ws, "_pid_alive", lambda pid: True)
    # connect side: python 602 whose parent is launcher 601
    monkeypatch.setattr(ws, "_shell_ppid", lambda: _win(601))
    ws.write_rpc_bridge("desk-a", port=1234, secret="s", pid=602)
    # verb side: python 612 whose parent is launcher 611
    monkeypatch.setattr(ws, "_shell_ppid", lambda: _win(611))
    row = ws.bridge_for_parent()
    assert row is not None and row["desk"] == "desk-a"
    # A verb from a different shell must not match
    monkeypatch.setattr(ws, "_shell_ppid", lambda: 777)
    assert ws.bridge_for_parent() is None
