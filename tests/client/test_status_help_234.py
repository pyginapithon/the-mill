"""mill -h lists only wall verbs the server handles (#234)."""
from __future__ import annotations

import io
import re
import sys

from agent_coord.__main__ import main
from agent_coord.client.outbound import WALL, canonical_verb
from agent_coord.server.api.mill.rpc import HANDLERS

# Host commands. They are printed in help and are not mill-wall verbs.
_LOCAL = frozenset(
    {
        "briefing",
        "help",
        "init",
        "score-add",
        "score-tick",
        "wall",
        "update",
        "install",
        "uninstall",
        "connect",
        "route",
        "watch",
        "mcp",
        "mcp-config",
        "wall-check",
        "wall-src",
        "local",
    }
)
_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def _help_verbs() -> list[str]:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        try:
            main(["-h"])
        except SystemExit as exc:
            assert exc.code in (0, None)
    finally:
        sys.stdout = old
    names: list[str] = []
    for line in buf.getvalue().splitlines():
        if not line.startswith("    ") or line.startswith("     "):
            continue
        word = line.strip().split()[0]
        if _NAME.match(word):
            names.append(word)
    return names


def test_help_wall_verbs_are_handlers() -> None:
    names = _help_verbs()
    # #254: status folded into hold --peek.
    assert "status" not in names
    assert "hold" in names
    missing = []
    for name in names:
        if name in _LOCAL:
            continue
        # 0.7.x CLI words that translate onto a wall verb (agent_coord/client/language.py).
        cli = {"unlabel": "label-remove", "watch": "add", "unwatch": "remove", "connect-wait": "connect", "connected": "session"}
        if name == "connect-wait":
            continue
        canon = "open" if name == "create" else canonical_verb(cli.get(name, name))
        if canon not in HANDLERS or canon not in WALL:
            missing.append("%s -> %s" % (name, canon))
    assert missing == []
