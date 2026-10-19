"""Wall floor mailbox uses lean public MAIL (mail_tos), not sender desk_id as dst."""
from __future__ import annotations


def test_floor_mailbox_uses_public_mail():
    import inspect
    from agent_coord.server.records import floor as fl

    src = inspect.getsource(fl.floor)
    assert "public_mail" in src
    assert 'r.get("desk_id") or r.get("dst")' not in src
