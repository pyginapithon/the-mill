# -*- coding: utf-8 -*-
from agent_coord.server.mcp_mill import handle, _tools


def test_mcp_initialize_and_tools_list() -> None:
    init = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init["result"]["serverInfo"]["name"] == "mill"
    listed = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {t["name"] for t in listed["result"]["tools"]}
    assert names == {"mill_wait"}
    assert any(t["name"] == "mill_wait" for t in _tools())


def test_grok_mcp_toml_prefers_mill_on_path(monkeypatch) -> None:
    from agent_coord.server.mcp_mill import grok_mcp_toml

    monkeypatch.setattr("shutil.which", lambda n: r"C:\bin\mill.exe" if n == "mill" else None)
    monkeypatch.setattr("agent_coord.server.mcp_mill._mill_has_mcp", lambda p: True)
    text = grok_mcp_toml("build-ui", "grok-build")
    assert "mill mcp" in text.replace('"', " ").replace(",", " ") or 'args = ["mcp"]' in text
    assert "build-ui" in text
    assert "PYTHONPATH" not in text


def test_mcp_wait_requires_owner(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    out = handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "mill_wait", "arguments": {"timeout_s": 1}},
        }
    )
    text = out["result"]["content"][0]["text"]
    assert "owner" in text.lower()
    assert out["result"]["isError"] is True
