# -*- coding: utf-8 -*-
"""Invite mint carries CA PEM bytes. Cold join stores that PEM and does not install an OS trust store."""
from __future__ import annotations

import base64
import json
from pathlib import Path



def _skill_line() -> str:
    text = Path("docs/protocol/skill.md").read_text(encoding="utf-8")
    for raw in text.splitlines():
        if len(raw) > 80 and not any(ch in raw for ch in "\"\\`"):
            return raw
    raise AssertionError("skill.md has no long line to compare")


def test_mint_payload_has_ca_pem_not_fetch_url_or_skill_body(monkeypatch, tmp_path) -> None:
    from agent_coord.server.admin import seats as seats_mod

    pem = "-----BEGIN CERTIFICATE-----\nMIIBTESTCA\n-----END CERTIFICATE-----\n"
    cafile = tmp_path / "ca.crt"
    cafile.write_text(pem, encoding="utf-8")
    monkeypatch.setattr("agent_coord.install.host.mill_ca_crt", lambda dest=None: cafile)

    def fake_upsert(cn, project, desk, role="", token_hash=None, doing=None):
        return [{"owner": desk, "desk_id": 1}]

    monkeypatch.setattr("agent_coord.server.records.join.upsert", fake_upsert)
    monkeypatch.setattr("agent_coord.server.records.member.put_office", lambda *a, **k: None)
    row = seats_mod.mint_seat(
        object(),
        desk="bot-a",
        created_by="admin",
        mill_url="https://wall.example",
    )
    blob = json.dumps(row)
    assert row["ca"] == pem
    assert "BEGIN CERTIFICATE" in row["ca"]
    assert "/ca.crt" not in blob
    assert "/api/ca.crt" not in blob
    assert "ca_url" not in row
    skill_line = _skill_line()
    assert skill_line not in blob
    assert "skill.md" not in blob
    assert "join_argv" not in row  # #620: the link goes in a file, never argv
    url = row["invite_url"]
    assert url.startswith("https://wall.example/welcome?")
    assert "desk=bot-a" in url
    assert "project=the-mill" in url
    assert "seat=" + row["seat"] in url
    assert "pem=" in url
    # One line in the link file: no whitespace inside the URL.
    assert not any(ch.isspace() for ch in url)



_OS_TRUST = (
    "certutil",
    "add-trusted-cert",
    "update-ca-certificates",
    "update-ca-trust",
    "sudo",
    "_os_trust_command",
    "_trust_mill_ca_current_user",
)


def _reject_os_trust(argv, *args, **kwargs):
    import subprocess

    blob = argv if isinstance(argv, str) else " ".join(str(part) for part in argv)
    for bad in _OS_TRUST:
        if bad in blob:
            raise AssertionError("join invoked an OS trust command: " + blob)
    real = getattr(_reject_os_trust, "_real", None)
    if real is None:
        raise AssertionError("join invoked a process before the real runner was saved: " + blob)
    return real(argv, *args, **kwargs)


import subprocess as _subprocess

_reject_os_trust._real = _subprocess.run


def test_join_does_not_invoke_os_trust(monkeypatch, tmp_path) -> None:
    import inspect

    from agent_coord.client.offices import join_office
    from agent_coord.install import host as hostmod

    src = inspect.getsource(hostmod.mill_join) + chr(10) + inspect.getsource(join_office)
    for bad in _OS_TRUST:
        assert bad not in src
    monkeypatch.setattr("agent_coord.install.host.subprocess.run", _reject_os_trust)
    monkeypatch.setattr("subprocess.run", _reject_os_trust)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "directory")
    from agent_coord.client.offices import bind_cli_office

    bind_cli_office("")
    pem = "-----BEGIN CERTIFICATE-----" + chr(10) + "MIIBTESTCA" + chr(10) + "-----END CERTIFICATE-----" + chr(10)
    row = hostmod.mill_join(
        "https://wall.example",
        dest=tmp_path / "config.toml",
        ca_pem=pem,
        seat="sekret_once",
        desk="bot-a",
    )
    assert row["ok"] is True
    assert (tmp_path / "ssl" / "ca.crt").read_text(encoding="utf-8") == pem
    from urllib.parse import urlencode
    import base64 as _b64
    wel = "https://203.0.113.10/welcome?" + urlencode(
        {
            "desk": "bot-a",
            "seat": "sekret_once",
            "pem": _b64.b64encode(pem.encode("utf-8")).decode("ascii"),
        }
    )
    office = join_office(wel, "Offsite", dest=tmp_path)
    assert office["ok"] is True
    assert (tmp_path / "203.0.113.10" / "ca.crt").read_text(encoding="utf-8") == pem


def test_join_uses_mint_ca_and_names_skill(monkeypatch, tmp_path) -> None:
    from agent_coord.client.offices import bind_cli_office
    from agent_coord.install import host as hostmod

    def boom(*_a, **_k):
        raise AssertionError("join fetched a CA URL")

    monkeypatch.setattr("agent_coord.client.http.fetch_mill_ca", boom)
    monkeypatch.setattr("agent_coord.install.host.subprocess.run", _reject_os_trust)
    monkeypatch.setattr("subprocess.run", _reject_os_trust)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "directory")
    bind_cli_office("")
    pem = "-----BEGIN CERTIFICATE-----" + chr(10) + "MIIBTESTCA" + chr(10) + "-----END CERTIFICATE-----" + chr(10)
    cfg = tmp_path / "config.toml"
    row = hostmod.mill_join(
        "https://wall.example",
        dest=cfg,
        ca_pem=pem,
        seat="sekret_once",
        desk="bot-a",
    )
    assert row["ok"] is True
    assert row["skill"].replace(chr(92), "/").endswith("docs/protocol/skill.md")
    body = _skill_line()
    assert body not in row["note"]
    assert body not in row["skill"]
    assert (tmp_path / "ssl" / "ca.crt").read_text(encoding="utf-8") == pem
    tok = (tmp_path / "session" / "bot-a.token").read_text(encoding="utf-8").strip()
    assert tok == "sekret_once"
    # 0.7.x: the only connect advice is the next: line, naming just the desk.
    assert row.get("next") in (None, "next: bash -c 'mill connect bot-a >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill inbox'")
    assert "mill connect" not in json.dumps({k: v for k, v in row.items() if k not in ("note", "next")})
    assert "certutil" not in json.dumps(row)
    assert "sudo" not in json.dumps(row)
