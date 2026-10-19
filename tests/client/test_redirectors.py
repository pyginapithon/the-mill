# -*- coding: utf-8 -*-
import json
import subprocess
import sys

from agent_coord.client.route_chain import (
    bind_exit,
    add_route,
    list_lines,
    load_routes,
    rm_route,
    route_key,
    route_path,
    save_routes,
    try_route,
)


def test_file_keeps_add_order(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_routes(
        "builder",
        [
            ("*", "python desk.py"),
            ("mail:MAIL", "python on_mail.py"),
        ],
    )
    got = load_routes("builder")
    assert [key for key, _ in got] == ["*", "mail:MAIL"]
    assert route_path("builder").name == "builder.route"
    assert list_lines("builder")[0].startswith("* python desk.py")
    assert "suppress" not in list_lines("builder")[0]


def test_replace_keeps_place(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    add_route("builder", "*", "python first.py")
    add_route("builder", "todo:TODO", "python todo.py")
    add_route("builder", "*", "python second.py")
    got = load_routes("builder")
    assert [key for key, _ in got] == ["*", "todo:TODO"]
    assert got[0][1] == "python second.py"


def test_rm_one_key_leaves_the_rest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    add_route("builder", "todo:TODO", "python todo.py")
    add_route("builder", "*", "python desk.py")
    rm_route("builder", "todo:TODO")
    assert [key for key, _ in load_routes("builder")] == ["*"]
    try:
        rm_route("builder", "todo:TODO")
    except KeyError:
        pass
    else:
        raise AssertionError("missing key must fail")
    assert [key for key, _ in load_routes("builder")] == ["*"]


def test_empty_value_suppresses(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    ran: list[str] = []
    monkeypatch.setattr(
        "agent_coord.client.route_chain.run_program",
        lambda cmd, msg: ran.append(cmd) or ("handled", 0),
    )
    save_routes("builder", [("mail:MAIL", ""), ("*", "python desk.py")])
    assert try_route("builder", {"kind": "mail", "id": 3}) == "suppress"
    assert ran == []
    assert list_lines("builder")[0] == "mail:MAIL suppress"


def test_missing_is_next(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    assert try_route("builder", {"type": "mail", "hint": "MAIL", "route": "mail:MAIL"}) == "next"


def test_ping_does_not_enter(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_routes("builder", [("*", "python desk.py")])
    monkeypatch.setattr(
        "agent_coord.client.route_chain.run_program",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawn")),
    )
    assert try_route("builder", {"type": "heartbeat", "hint": "PING"}) == "suppress"


def test_letter_key_is_mail(tmp_path, monkeypatch) -> None:
    assert route_key({"kind": "mail", "id": 9}) == "mail:MAIL"
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    seen: list[str] = []

    def fake_run(cmd, msg):
        seen.append(route_key(msg))
        return "handled", 0

    monkeypatch.setattr("agent_coord.client.route_chain.run_program", fake_run)
    save_routes("builder", [("mail:MAIL", "python on_mail.py")])
    assert try_route("builder", {"kind": "mail", "id": 9}) == "handled"
    assert seen == ["mail:MAIL"]


def test_try_route_waits_and_handles(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    seen = {}

    class FakeProc:
        returncode = 0

        def communicate(self, data=None, timeout=None):
            seen["raw"] = data
            return b"handled\n", b""

    def fake_popen(argv, **kw):
        seen["argv"] = argv
        seen["stdout"] = kw.get("stdout")
        return FakeProc()

    monkeypatch.setattr("agent_coord.client.route_chain.subprocess.Popen", fake_popen)
    save_routes("builder", [("mail:MAIL", "python on_mail.py")])
    decision = try_route(
        "builder",
        {"type": "mail", "id": 3, "hint": "MAIL", "route": "mail:MAIL", "desk": "builder"},
    )
    assert decision == "handled"
    assert json.loads(seen["raw"].decode("utf-8"))["id"] == 3
    assert seen["argv"][0] == "python"


def test_real_not_mine_reaches_the_next_program(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    nxt = tmp_path / "next.py"
    done = tmp_path / "done.py"
    nxt.write_text("import sys\nsys.stdin.read()\nprint('not-mine')\n", encoding="utf-8")
    done.write_text("import sys\nsys.stdin.read()\nprint('handled')\n", encoding="utf-8")
    py = sys.executable
    save_routes(
        "builder",
        [
            ("*", subprocess.list2cmdline([py, str(nxt)])),
            ("todo:TODO", subprocess.list2cmdline([py, str(done)])),
        ],
    )
    assert try_route("builder", {"type": "todo", "hint": "TODO", "id": 1}) == "handled"


def test_real_nonzero_writes_the_exit_line(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    bad = tmp_path / "bad.py"
    bad.write_text("import sys\nsys.stdin.read()\nraise SystemExit(4)\n", encoding="utf-8")
    py = sys.executable
    save_routes("builder", [("todo:TODO", subprocess.list2cmdline([py, str(bad)]))])
    exits: list[dict] = []
    with bind_exit(exits.append):
        assert try_route("builder", {"type": "todo", "hint": "TODO", "id": 6}) == "handled"
    assert exits == [{"exit": 1, "frame": {"route": "todo:TODO", "id": 6, "exit": 4}}]
