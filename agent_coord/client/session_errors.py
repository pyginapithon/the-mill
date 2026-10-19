"""Shared mill session / Bearer error copy (cp1252-safe ASCII)."""
from __future__ import annotations

import os

# When join.token_hash was cleared or the local token no longer matches.
SESSION_INVALID_REJOIN = (
    "invalid or expired Bearer; mill connect DESK to rejoin"
)

# Join refused: the office door (invite / directory / iam) needs a credential.
# A cold agent uses the seat welcome link; an invite office needs its invite key.
SESSION_JOIN_DENIED = (
    "join refused: this office door needs a valid invite or seat; "
    "mill join <welcome-link> (ask an Admin to mint a seat)"
)

# Missing Bearer on a gated verb.
SESSION_TOKEN_REQUIRED = (
    "mill access token required; mill connect DESK "
    "(writes ~/.mill/session/<desk>.token)"
)

# Bearer ok but desk has no live Hub /ws (kicked, dropped, never connected).
# Kept for WS-side checks when a socket is not seated.
SESSION_WS_REQUIRED = (
    "disconnected: no active Hub /ws for this desk; mill connect DESK to reconnect"
)

# HTTP desk-acting verbs are cut: verbs run as JSON RPC on the sitting /ws only.
SESSION_WS_RPC_ONLY = (
    "desk-acting verbs use live /ws JSON RPC; mill connect, then verb on that socket"
)

# mill_ws_call needs the sitting mill connect localhost bridge (no second /ws).
# Match is the verb process parent pid, not the host active file.
# A fresh shell, a subshell, or the next tool call has a different parent, so
# "connect again, then retry" misses the same way (#179). Name the same-parent
# rule and a one-shot recipe for this OS. A second connect supersedes the first.
# The #121 retry compares str(e) to SESSION_WS_BRIDGE_REQUIRED, so the raised
# text and this constant stay the same string.
_BRIDGE_PREFIX = (
    "no sitting mill connect for this process; "
    "this verb must be a child of the shell that started mill connect (same parent process). "
)
_BRIDGE_SUFFIX = "The connect is the desk's identity; a command outside one has none."
# Every mill command runs this way: connect and the verb share one parent (0.7.x).
ONE_LINER = "bash -c 'mill connect DESK >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill VERB ARGS'"
_BASH_RECIPE = "Run it as: " + ONE_LINER + " (connect alone in the foreground just blocks). "
_PS_RECIPE = (
    "Run it as: $c = Start-Process mill -ArgumentList 'connect','DESK' -PassThru -NoNewWindow; "
    "mill VERB ARGS; Stop-Process $c.Id (connect alone in the foreground just blocks). "
)


def bridge_hint(os_name: str | None = None) -> str:
    name = os.name if os_name is None else str(os_name)
    recipe = _PS_RECIPE if name == "nt" else _BASH_RECIPE
    return _BRIDGE_PREFIX + recipe + _BRIDGE_SUFFIX


SESSION_WS_BRIDGE_REQUIRED = bridge_hint()

# The bridge or starting file is still here, but that connect process is gone (#228).
# Shell-neutral, and different from the sitting-miss hint (#236).
SESSION_CONNECT_DIED = (
    "disconnected: the mill connect for this process died. "
    "Start mill connect again in this same shell, then retry the verb."
)

