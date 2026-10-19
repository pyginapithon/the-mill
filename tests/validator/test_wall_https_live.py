# -*- coding: utf-8 -*-
"""Live HTTPS Wall probes: boot stamp + lean v1 parts (mill_live)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.mill_live

# Loose body ceilings (decompressed). Floor aggregator is huge; v1 parts stay lean.
_MAX_BOOT_BODY = 80_000  # board HTML can be tens of KB; still << floor
_MAX_V1_BODY = 50_000


def test_wall_get_boot_stamp(http_client, mill_base_url: str) -> None:
    r = http_client.get(mill_base_url + "/")
    body_len = len(r.content)
    assert r.status_code == 200, f"GET / status={r.status_code} len={body_len}"
    assert str(r.url).startswith("https://"), f"must use https, got {r.url}"
    assert ":80" not in str(r.url).split("?", 1)[0], f"must not use :80: {r.url}"
    # Boot stamp: mill headers + wall-asset-id meta (alive Wall, not empty proxy).
    assert r.headers.get("x-mill-api") or r.headers.get("x-mill-version"), (
        f"missing mill boot headers; keys={list(r.headers.keys())} len={body_len}"
    )
    text = r.text
    assert "wall-asset-id" in text or "The Mill" in text, (
        f"boot HTML missing stamp markers; len={body_len}"
    )
    assert body_len < _MAX_BOOT_BODY, (
        f"GET / body too large: {body_len}B (max {_MAX_BOOT_BODY})"
    )


def test_wall_v1_agents_lean(http_client, mill_base_url: str) -> None:
    path = "/api/v1/agents?project=Office&limit=50"
    r = http_client.get(mill_base_url + path)
    body_len = len(r.content)
    assert r.status_code == 200, f"agents status={r.status_code} len={body_len}"
    assert str(r.url).startswith("https://"), f"must use https, got {r.url}"
    assert "http://" not in str(r.url) and ":80/" not in str(r.url), (
        f"must not use http://:80: {r.url}"
    )
    assert body_len < _MAX_V1_BODY, (
        f"v1 agents body {body_len}B not <<50KB (max {_MAX_V1_BODY})"
    )
    data = r.json()
    assert "agents" in data or "parts" in data, (
        f"unexpected agents payload keys={list(data)[:12]} len={body_len}"
    )


def test_wall_v1_scores_lean(http_client, mill_base_url: str) -> None:
    path = "/api/v1/scores?project=Office&limit=20"
    r = http_client.get(mill_base_url + path)
    body_len = len(r.content)
    assert r.status_code == 200, f"scores status={r.status_code} len={body_len}"
    assert str(r.url).startswith("https://"), f"must use https, got {r.url}"
    assert body_len < _MAX_V1_BODY, (
        f"v1 scores body {body_len}B not <<50KB (max {_MAX_V1_BODY})"
    )