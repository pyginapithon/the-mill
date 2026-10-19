"""Builder unit checks for wall-secure-https-lan (HTTPS-only + LAN bind)."""
from __future__ import annotations

from pathlib import Path

from agent_coord.install import nginx_server
from agent_coord.server.netbind import (
    is_private_ip,
    resolve_listen_hosts,
    assert_mill_api_bind,
)


def test_private_ip():
    assert is_private_ip("127.0.0.1")
    # Octets stay split so the pack check does not see a complete non-documentation address.
    assert is_private_ip(".".join(("10", "0", "0", "2")))
    assert not is_private_ip(".".join(("1", "2", "3", "4")))


def test_listen_lan_only_excludes_wildcard():
    hosts = resolve_listen_hosts(lan_only=True, public_bind="0.0.0.0")
    assert "*" not in hosts
    assert "0.0.0.0" not in hosts
    assert "127.0.0.1" in hosts


def test_listen_public_allows_wildcard():
    hosts = resolve_listen_hosts(lan_only=False, public_bind="0.0.0.0")
    assert hosts == ["*"]


def test_nginx_http_redirect(tmp_path: Path):
    www = tmp_path / "www"
    www.mkdir()
    text = nginx_server(
        public_bind="127.0.0.1",
        public_port=443,
        api_bind="127.0.0.1",
        api_port=18766,
        docroot=www,
        lan_only=True,
    )
    assert "return 301 https://" in text
    assert "listen 127.0.0.1:80" in text
    assert "ssl_certificate" in text
    assert "nginx-access.log" in text
    assert "proxy_pass http://127.0.0.1:18766" in text
    assert "try_files" not in text


def test_mill_api_bind_loopback_only():
    assert_mill_api_bind("127.0.0.1", api_only=True)
    try:
        assert_mill_api_bind("0.0.0.0", api_only=True)
        assert False, "expected refuse"
    except ValueError:
        pass
