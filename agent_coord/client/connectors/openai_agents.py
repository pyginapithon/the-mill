"""OpenAI Agents - stub for volunteers.

Intended: mill webhook POST {type,id,hint} into an OpenAPI Action. Schema TBD.
"""
from __future__ import annotations

from typing import Any

VENDOR = "openai-agents"


def poke(hint: dict[str, Any]) -> None:
    raise NotImplementedError(
        "openai-agents: mill webhook fan-out is live; volunteer: Action URL after HINT "
        f"{hint!r}"
    )
