"""mail-to fail-closed + send unknown desk."""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.book import Book
from unittest.mock import MagicMock, patch


def test_send_unknown_desk_errors():
    c = MagicMock(spec=Book)
    c._cn = MagicMock()
    body = {"dst": "no-such-desk-xyz", "body": "hello", "src": "builder"}
    with patch("agent_coord.client.outbound.addressing.parse_mail_to", return_value=[
        {"kind": "desk", "dst": "no-such-desk-xyz"}
    ]), patch("agent_coord.server.records.name.get", return_value=None):
        with pytest.raises(CoordError) as ei:
            rpc._h_send(c, body, "agent-coord", "builder")
    assert "no-such-desk-xyz" in str(ei.value)
    assert "not in the name table" in str(ei.value)


def test_send_empty_mail_to_refused_after_insert():
    c = MagicMock(spec=Book)
    cn = MagicMock()
    c._cn = cn
    body = {"dst": "builder", "body": "hello", "src": "repo"}
    with patch("agent_coord.client.outbound.addressing.parse_mail_to", return_value=[
        {"kind": "desk", "dst": "builder"}
    ]), patch("agent_coord.server.records.name.get", return_value=19), patch(
        "agent_coord.server.records.name.ensure_roster"
    ), patch(
        "agent_coord.server.records.mail.insert", return_value=[{"id": 99}]
    ), patch(
        "agent_coord.server.records.mail.dest_count", return_value=0
    ):
        with pytest.raises(CoordError) as ei:
            rpc._h_send(c, body, "agent-coord", "repo")
    assert "empty mail_to" in str(ei.value).lower() or "orphan" in str(ei.value).lower()
