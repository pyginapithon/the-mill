"""Kimi / Moonshot - stub for volunteers.

Intended: mill here HINT then kimi CLI or Moonshot HTTP. Exact argv/URL TBD.
"""
from __future__ import annotations

from typing import Any

VENDOR = "kimi"


def poke(hint: dict[str, Any]) -> None:
    raise NotImplementedError(
        "kimi: mill here WS is live; volunteer: kimi run or HTTP after HINT "
        f"{hint!r}"
    )
