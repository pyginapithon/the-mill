"""tools/probe_deleted_rows.py (#160) with a fake sitting connect. No SQL."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from agent_coord.client.outbound import PROBE, VERBS, WALL
from agent_coord.server.api.mill.rpc import HANDLERS

ROOT = Path(__file__).resolve().parents[2]


def _tool():
    spec = importlib.util.spec_from_file_location("probe_deleted_rows", ROOT / "tools" / "probe_deleted_rows.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_probe_is_wall_rpc_not_a_skill_verb() -> None:
    assert "probe-delete" in PROBE
    assert "probe-delete" in WALL and "probe-delete" in HANDLERS
    assert "probe-delete" not in VERBS


def test_probe_is_not_a_mill_subcommand() -> None:
    src = (ROOT / "agent_coord" / "__main__.py").read_text(encoding="utf-8")
    assert "probe-delete" not in src


class _Fake:
    def __init__(self):
        self.sent = []

    def __call__(self, body):
        self.sent.append(dict(body))
        v = body["verb"]
        if v == "open":
            return {"ok": True, "result": {"id": 41, "project_id": body["project"]}}
        if v == "score":
            return {"ok": True, "result": [{"id": 42}]}
        if v == "probe-delete":
            return {"ok": True, "result": {"type": body["type"], "id": body["id"], "state": "deleted", "deleted": "x"}}
        if v == "trail":
            return {"ok": True, "result": {"nodes": [{"kind": "todo", "id": 41, "state": "deleted"}]}}
        raise AssertionError(v)


def test_run_makes_and_deletes_fixture_rows(capsys) -> None:
    mod = _tool()
    fake = _Fake()
    assert mod.main(["run", "--project", "t-0a1b2c3d"], call=fake) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["project"] == "t-0a1b2c3d"
    assert out["todo"]["id"] == 41 and out["score"]["id"] == 42
    verbs = [b["verb"] for b in fake.sent]
    assert verbs == ["open", "score", "probe-delete", "probe-delete", "trail"]
    assert all(b.get("project") == "t-0a1b2c3d" for b in fake.sent if b["verb"] in ("open", "score"))


def test_run_default_project_is_fresh_fixture(capsys) -> None:
    mod = _tool()
    fake = _Fake()
    assert mod.main(["run"], call=fake) == 0
    proj = json.loads(capsys.readouterr().out)["project"]
    assert mod.FIXTURE.match(proj)


def test_run_refuses_real_project_without_sending(capsys) -> None:
    mod = _tool()
    fake = _Fake()
    assert mod.main(["run", "--project", "the-mill"], call=fake) == 2
    assert fake.sent == []
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_office_refusal_is_exit_1(capsys) -> None:
    mod = _tool()

    def refuse(body):
        raise RuntimeError("probe-delete: todo 7 was not made by this desk; refused")

    assert mod.main(["delete", "--type", "todo", "--id", "7"], call=refuse) == 1
    assert "not made by this desk" in json.loads(capsys.readouterr().out)["error"]


def test_run_flags_a_row_that_did_not_go_deleted(capsys) -> None:
    mod = _tool()
    fake = _Fake()

    def half(body):
        out = fake(body)
        if body["verb"] == "trail":
            return {"ok": True, "result": {"nodes": [{"kind": "todo", "id": 41, "state": "open"}]}}
        return out

    assert mod.main(["run", "--project", "t-0a1b2c3d"], call=half) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
