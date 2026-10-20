"""watch and unwatch hold take the resource name, like watch todo ROSTER/NEED (#327)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent_coord.client.language import card_ref
from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc


def test_client_passes_a_hold_name_through():
    assert card_ref("deploy", "hold", "watch") == "deploy"
    assert card_ref("docs/a.md", "hold", "unwatch") == "docs/a.md"
    assert card_ref("85", "hold", "watch") == 85


def test_client_still_refuses_names_for_other_kinds():
    with pytest.raises(CoordError, match="give the score id"):
        card_ref("deploy", "score", "watch")
    with pytest.raises(CoordError):
        card_ref("", "hold", "watch")


def test_cli_watch_hold_by_name(monkeypatch):
    from agent_coord.__main__ import _build_parser
    from agent_coord.client.language import translate
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x="": "me")
    for verb in ("watch", "unwatch"):
        a = translate(_build_parser().parse_args([verb, "hold", "deploy"]))
        body = outbound.body_from_args(a)
        assert body["type"] == "hold" and body["ref"] == "deploy" and "id" not in body


def _holds(monkeypatch, rows):
    monkeypatch.setattr("agent_coord.server.records.hold.find", lambda cn, **kw: list(rows))


def test_server_resolves_hold_name_to_id(monkeypatch):
    _holds(monkeypatch, [{"resource": "deploy", "desk": "w3", "id": 85, "updated": "t"}])
    assert rpc._card_ref_id(MagicMock(), {"type": "hold", "ref": "deploy"}, "add") == 85


def test_server_released_hold_still_resolves(monkeypatch):
    _holds(monkeypatch, [{"resource": "deploy", "desk": None, "id": 85, "updated": "t"}])
    assert rpc._card_ref_id(MagicMock(), {"type": "hold", "ref": "deploy"}, "remove") == 85


def test_server_unknown_hold_name_is_refused(monkeypatch):
    _holds(monkeypatch, [])
    with pytest.raises(CoordError, match="no hold named nope"):
        rpc._card_ref_id(MagicMock(), {"type": "hold", "ref": "nope"}, "add")


def test_server_names_still_refused_for_score(monkeypatch):
    with pytest.raises(CoordError, match="only a todo .ROSTER/NEED. or a hold .its name. goes by name"):
        rpc._card_ref_id(MagicMock(), {"type": "score", "ref": "x"}, "add")
