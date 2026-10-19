# -*- coding: utf-8 -*-
from agent_coord.install import host_from_wall_url

def _reject_join_process(argv, *args, **kwargs):
    blob = argv if isinstance(argv, str) else " ".join(str(part) for part in argv)
    raise AssertionError("join invoked a process: " + blob)


from agent_coord.server.netbind import preferred_office_host


def test_host_from_wall_url_any_lan():
    assert host_from_wall_url("https://203.0.113.8/#session") == "203.0.113.8"
    assert host_from_wall_url("203.0.113.8") == "203.0.113.8"
    assert host_from_wall_url("https://office.local:443/") == "office.local"


def test_mill_join_accepts_localhost_and_lan():
    assert host_from_wall_url("127.0.0.1") == "127.0.0.1"
    assert host_from_wall_url("198.51.100.81") == "198.51.100.81"


def test_preferred_office_host_lan_or_localhost():
    h = preferred_office_host()
    assert h.startswith("192.168.1.") or h == "127.0.0.1"


def test_mill_join_url_only_no_mysql_user(tmp_path, monkeypatch):
    import inspect

    from agent_coord.install import mill_join

    cafile = tmp_path / "ca.crt"
    cafile.write_text("CERT", encoding="utf-8")
    monkeypatch.setattr(
        "agent_coord.client.http.fetch_mill_ca",
        lambda url, dest=None, invite="", expect_fp="": cafile,
    )
    monkeypatch.setattr("agent_coord.install.host.subprocess.run", _reject_join_process)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    dest = tmp_path / "config.toml"
    row = mill_join("https://203.0.113.8/", dest=dest)
    text = dest.read_text(encoding="utf-8")
    assert "mill_url" in text
    assert "password" not in text
    assert row.get("ok") is True
    assert "mysql.connector" not in inspect.getsource(mill_join)


def test_mill_join_keeps_existing_book_password(tmp_path, monkeypatch):
    from agent_coord.install import mill_join

    cafile = tmp_path / "ca.crt"
    cafile.write_text("CERT", encoding="utf-8")
    monkeypatch.setattr(
        "agent_coord.client.http.fetch_mill_ca",
        lambda url, dest=None, invite="", expect_fp="": cafile,
    )
    monkeypatch.setattr("agent_coord.install.host.subprocess.run", _reject_join_process)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    dest = tmp_path / "config.toml"
    dest.write_text('host = "127.0.0.1"\npassword = "root"\n', encoding="utf-8")
    row = mill_join("https://203.0.113.8/", dest=dest)
    text = dest.read_text(encoding="utf-8")
    assert row.get("ok") is True
    assert "mill_url" in text
    assert 'password = "root"' in text
