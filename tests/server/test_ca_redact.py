"""PEM redaction covers base64 CA and pem= on welcome links (#172 / #253)."""
from __future__ import annotations

import base64


def test_seal_redacts_base64_ca_and_pem_query():
    from agent_coord.server.glance import seal

    pem = "-----BEGIN CERTIFICATE-----\nMIIBTESTCA\n-----END CERTIFICATE-----\n"
    blob = base64.b64encode(pem.encode("utf-8")).decode("ascii")
    url = "https://wall.example/welcome?desk=bot&seat=sekrit&pem=" + blob
    out = seal({"join_argv": ["mill", "join", url], "ca": pem, "note": "keep"})
    assert "ca" not in out or out.get("ca") == "[redacted]"
    joined = " ".join(out["join_argv"])
    assert "sekrit" not in joined
    assert blob not in joined
    assert "pem=[redacted]" in joined or "pem=" + blob not in joined
    assert "MIIBTESTCA" not in str(out)


def test_join_without_served_ca_hints_remint(monkeypatch, tmp_path):
    from agent_coord.install.host import mill_join

    monkeypatch.setattr("agent_coord.client.http.fetch_mill_ca", lambda *a, **k: None)
    row = mill_join("https://203.0.113.9", dest=tmp_path / "config.toml")
    assert row["ok"] is False
    note = row.get("note") or row.get("error") or ""
    assert "CA" in note or "ca" in note.lower()
    assert not (tmp_path / "config.toml").exists()
