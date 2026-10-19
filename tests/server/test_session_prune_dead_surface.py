"""Session cleanup: dead HERE seats pruned; Wall skips no-hash agents."""
from __future__ import annotations

import inspect


def test_reset_rpc_supports_dead_prune():
    from agent_coord.server.api.mill import rpc

    src = inspect.getsource(rpc._h_reset)
    assert 'body.get("dead")' in src or 'body.get("prune_dead")' in src
    assert "prune_dead" in src


def test_cli_reset_has_dead_flag():
    from pathlib import Path

    main = Path("agent_coord/__main__.py").read_text(encoding="utf-8")
    assert '"--dead"' in main or "'--dead'" in main
    assert "prune" in main.lower() or "token_hash" in main
