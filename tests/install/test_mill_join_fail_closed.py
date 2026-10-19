"""#486 mill join must not ok:true when Wall CA missing."""
from __future__ import annotations

from agent_coord.install import host as hostmod


def _reject_join_process(argv, *args, **kwargs):
    blob = argv if isinstance(argv, str) else " ".join(str(part) for part in argv)
    raise AssertionError("join invoked a process: " + blob)


def test_mill_join_fail_closed_when_ca_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agent_coord.client.http.fetch_mill_ca", lambda url, dest=None, invite="", expect_fp="": None
    )
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr(
        "agent_coord.server.admin.door.invite_from_request", lambda *a, **k: ""
    )
    row = hostmod.mill_join("https://127.0.0.1:9/", dest=tmp_path / "config.toml")
    assert row.get("ok") is False
    blob = (row.get("note") or "") + " ".join(row.get("trust") or [])
    assert "fail" in blob.lower() or "unreachable" in blob.lower()


def test_mill_join_ok_when_ca_fetched(monkeypatch, tmp_path):
    ca = tmp_path / "mill-ca.crt"
    ca.write_text("CERT", encoding="utf-8")
    monkeypatch.setattr(
        "agent_coord.client.http.fetch_mill_ca", lambda url, dest=None, invite="", expect_fp="": ca
    )
    monkeypatch.setattr(hostmod.subprocess, "run", _reject_join_process)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr(
        "agent_coord.server.admin.door.invite_from_request", lambda *a, **k: ""
    )
    cfg = tmp_path / "config.toml"
    row = hostmod.mill_join("https://wall.example/", dest=cfg)
    assert row.get("ok") is True
    assert cfg.is_file()
