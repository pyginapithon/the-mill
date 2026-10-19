"""#489 clear leftover config node when owner is set."""
from __future__ import annotations


def test_clear_shared_node_if_owner(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        'mill_url = "https://wall.example/"\nnode = "other-desk"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("agent_coord.config.config_path", lambda: cfg)
    from agent_coord.config import clear_shared_node_if_owner, load_file

    assert clear_shared_node_if_owner("DESK_builder") is True
    assert not load_file(cfg).get("node")
    assert clear_shared_node_if_owner("DESK_builder") is False
    assert clear_shared_node_if_owner("") is False
