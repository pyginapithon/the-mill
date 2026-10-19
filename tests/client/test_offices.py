"""Multi-mill client layout. Legacy session/ stays when no office is selected."""
from __future__ import annotations

from agent_coord.client.offices import (
    bind_cli_office,
    current_office,
    host_key,
    join_office,
    looks_like_host,
    prefer_dns,
    pull_office_flag,
    read_alias,
    list_aliases,
    write_alias,
    write_global_active,
)
from agent_coord.client.tokens import read_active_desk, read_session_token, write_active_desk, write_session_token


def _reject_join_process(argv, *args, **kwargs):
    blob = argv if isinstance(argv, str) else " ".join(str(part) for part in argv)
    for bad in (
        "certutil",
        "add-trusted-cert",
        "update-ca-certificates",
        "update-ca-trust",
        "sudo",
    ):
        if bad in blob:
            raise AssertionError("join invoked an OS trust command: " + blob)
    return _reject_join_process._real(argv, *args, **kwargs)


import subprocess as _subprocess

_reject_join_process._real = _subprocess.run


def test_list_aliases_is_local(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "203.0.113.10")
    write_alias("lan", "198.51.100.10")
    write_global_active("lan")
    (tmp_path / "203.0.113.10").mkdir()
    (tmp_path / "203.0.113.10" / "url").write_text("https://203.0.113.10\n", encoding="utf-8")
    rows = list_aliases()
    assert [row["name"] for row in rows] == ["lan", "Offsite"]
    assert rows[0]["active"] is True
    assert rows[1]["url"] == "https://203.0.113.10"
    assert "DESK_" not in str(rows)


def test_local_servers_group_aliases(tmp_path, monkeypatch):
    from agent_coord.client.offices import local_servers

    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "203.0.113.10")
    write_alias("cloud-mill", "203.0.113.10")
    write_alias("lan", "198.51.100.10")
    write_global_active("lan")
    rows = local_servers()
    assert [row["host"] for row in rows] == ["198.51.100.10", "203.0.113.10"]
    by_host = {row["host"]: row for row in rows}
    assert by_host["198.51.100.10"]["aliases"] == ["lan"]
    assert by_host["198.51.100.10"]["active"] is True
    assert by_host["203.0.113.10"]["aliases"] == ["cloud-mill", "Offsite"]


def test_prefer_dns_over_matching_ip(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "office.example")
    monkeypatch.setattr(
        "agent_coord.client.offices.socket.gethostbyname",
        lambda name: "192.0.2.10" if name == "office.example" else name,
    )
    assert prefer_dns("192.0.2.10") == "office.example"
    assert prefer_dns("office.example") == "office.example"
    assert looks_like_host("the-mill") is False
    assert looks_like_host("192.0.2.10") is True


def test_route_file_follows_office(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    from agent_coord.client.route_chain import route_path

    write_alias("lan", "198.51.100.10")
    bind_cli_office("lan")
    try:
        path = route_path("build-cloud")
        assert path.name == "route"
        assert path.parent.name == "build-cloud"
        assert "198.51.100.10" in str(path)
    finally:
        bind_cli_office("")


def test_browser_trust_note_names_the_prompt():
    from agent_coord.install.host import browser_trust_note

    fresh = browser_trust_note(["trusted mill CA in CurrentUser Root (ok)"])
    assert "Accept that prompt" in fresh
    assert "Restart the browser" in fresh
    assert "wall.crt" in fresh
    again = browser_trust_note(["mill CA already in CurrentUser Root (ABCD...)"])
    assert "already trusted" in again


def test_host_key_strips_scheme_and_default_port():
    assert host_key("https://203.0.113.10/?invite=abc") == "203.0.113.10"
    assert host_key("https://office.example:8443/") == "office.example:8443"
    assert host_key("") == ""


def test_pull_office_flag_before_or_after_verb():
    name, rest = pull_office_flag(["todo", "--office", "Offsite", "--owner", "build-cloud"])
    assert name == "Offsite"
    assert rest == ["todo", "--owner", "build-cloud"]
    name, rest = pull_office_flag(["--office=lan", "connect"])
    assert name == "lan"
    assert rest == ["connect"]


def test_legacy_session_when_no_office(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    bind_cli_office("")
    write_session_token("build-cloud", "sekrit")
    assert (tmp_path / "session" / "build-cloud.token").is_file()
    assert read_session_token("build-cloud") == "sekrit"
    assert not (tmp_path / "alias").exists()


def test_office_token_is_per_host(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "203.0.113.10")
    bind_cli_office("Offsite")
    try:
        write_session_token("build-cloud", "sekrit")
        write_active_desk("build-cloud")
        path = tmp_path / "203.0.113.10" / "build-cloud" / "token"
        assert path.read_text(encoding="utf-8").strip() == "sekrit"
        assert read_session_token("build-cloud") == "sekrit"
        assert (tmp_path / "203.0.113.10" / "active").read_text(encoding="utf-8").strip() == "build-cloud"
        assert not (tmp_path / "session").exists()
    finally:
        bind_cli_office("")


def test_active_alias_selects_office_after_flag_clears(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "203.0.113.10")
    bind_cli_office("Offsite")
    try:
        write_active_desk("build-cloud")
        write_global_active("Offsite")
    finally:
        bind_cli_office("")
    assert current_office() == "Offsite"
    assert read_active_desk() == "build-cloud"
    assert read_alias("Offsite") == "203.0.113.10"


def test_office_connect_adopts_legacy_token(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    bind_cli_office("")
    write_session_token("build-cloud", "sekrit", desk_id=218)
    write_alias("lan", "198.51.100.10")
    bind_cli_office("lan")
    try:
        assert read_session_token("build-cloud") == "sekrit"
        path = tmp_path / "198.51.100.10" / "build-cloud" / "token"
        assert path.read_text(encoding="utf-8").strip() == "sekrit"
        assert read_session_token("build-cloud") == "sekrit"
    finally:
        bind_cli_office("")


def test_alias_refuses_a_different_host(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    write_alias("Offsite", "203.0.113.10")
    try:
        write_alias("Offsite", "198.51.100.10")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_join_office_does_not_write_legacy_config(tmp_path, monkeypatch):
    import base64
    from urllib.parse import urlencode

    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.host.subprocess.run", _reject_join_process)
    pem = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"
    wel = "https://203.0.113.10/welcome?" + urlencode(
        {
            "desk": "bot-a",
            "seat": "sek",
            "project": "the-mill",
            "pem": base64.b64encode(pem.encode("utf-8")).decode("ascii"),
        }
    )
    row = join_office(wel, "Offsite", dest=tmp_path)
    assert row["ok"] is True
    assert row["host"] == "203.0.113.10"
    assert "BEGIN CERTIFICATE" in (tmp_path / "203.0.113.10" / "ca.crt").read_text(encoding="utf-8")
    assert (tmp_path / "203.0.113.10" / "url").read_text(encoding="utf-8").strip() == "https://203.0.113.10"
    assert not (tmp_path / "config.toml").exists()
