"""Mail dual-read party / who display helpers."""
from __future__ import annotations


def format_read_who(desk: str, party: str, vendor: str = "") -> str:
    """Display identity: desk:human or desk:agent[:vendor]."""
    desk = (desk or "").strip()
    party = (party or "").strip().lower()
    vendor = (vendor or "").strip().lower()
    if party == "human":
        return f"{desk}:human"
    if vendor:
        return f"{desk}:agent:{vendor}"
    return f"{desk}:agent"


def normalize_read_party(party: str | None) -> str:
    from agent_coord.helpers.errors import CoordError

    p = (party or "agent").strip().lower()
    if p not in ("agent", "human"):
        raise CoordError("read party must be agent or human")
    return p
