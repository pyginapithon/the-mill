"""#619 a wake allowlist refusal names the allowed prefixes and the exact
host-Admin step to add one. Row F68 (desk-webhook)."""
from __future__ import annotations

import pytest

from agent_coord.server import wake

DEFAULT = "api2.cursor.sh/automations/webhook/"
PATH = "/automations/webhook/secret-route-id"


def _refusal(raw: str) -> str:
    with pytest.raises(wake.WakeRefused) as ei:
        wake.check_url(raw)
    return str(ei.value)


@pytest.fixture
def file_cfg(monkeypatch, tmp_path):
    monkeypatch.delenv("AGENT_COORD_WAKE_HOSTS", raising=False)
    cfg = tmp_path / "config.toml"
    cfg.write_text("", encoding="utf-8")
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(cfg))
    return cfg


def test_unknown_host_names_allowed_prefixes_and_the_config_line(file_cfg):
    text = _refusal("https://hooks.example.com" + PATH)
    assert "allowed: " + DEFAULT in text
    assert 'wake_hosts = "' + DEFAULT + ',hooks.example.com/<webhook path prefix>/"' in text
    assert "AGENT_COORD_CONFIG" in text  # where the wall reads it here
    assert "no restart" in text
    assert "secret-route-id" not in text and PATH not in text


def test_default_config_file_is_named_when_no_override(monkeypatch, tmp_path):
    monkeypatch.delenv("AGENT_COORD_WAKE_HOSTS", raising=False)
    monkeypatch.delenv("AGENT_COORD_CONFIG", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    text = _refusal("https://hooks.example.com" + PATH)
    assert "~/.mill/config.toml" in text and str(tmp_path) not in text


def test_env_override_names_the_env_and_a_restart(monkeypatch):
    monkeypatch.setenv("AGENT_COORD_WAKE_HOSTS", DEFAULT)
    text = _refusal("https://hooks.example.com" + PATH)
    assert "AGENT_COORD_WAKE_HOSTS=" + DEFAULT + ",hooks.example.com/<webhook path prefix>/" in text
    assert "restart mill-wall" in text
    assert "config.toml" not in text  # the env wins over the file, so the file is not the step


def test_wrong_path_on_an_allowed_host_names_its_prefixes_and_the_step(file_cfg):
    text = _refusal("https://api2.cursor.sh/other/secret-route-id")
    assert "allowed on api2.cursor.sh: /automations/webhook/" in text
    assert "copy the webhook URL from the routine again" in text
    assert 'wake_hosts = "' + DEFAULT + ',api2.cursor.sh/<webhook path prefix>/"' in text
    assert "secret-route-id" not in text and "/other/" not in text


def test_two_prefixes_are_all_named(monkeypatch, file_cfg):
    file_cfg.write_text('wake_hosts = "a.example.com/hooks/,b.example.com/w/"\n', encoding="utf-8")
    text = _refusal("https://c.example.com" + PATH)
    assert "allowed: a.example.com/hooks/, b.example.com/w/" in text
    assert 'wake_hosts = "a.example.com/hooks/,b.example.com/w/,c.example.com/<webhook path prefix>/"' in text
