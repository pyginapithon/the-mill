"""Reply and send warnings list offline desks on one line (#152)."""
from __future__ import annotations

from agent_coord.server.api.mill.rpc import _offline_warning

_TAIL = "(not on Hub / no recent join); mail is stored until they connect"


def test_one_desk_keeps_the_single_line():
    text = _offline_warning(["builder"])
    assert text == f"desk 'builder' looks offline {_TAIL}"
    assert "\n" not in text


def test_many_desks_collapse_to_one_line():
    names = ["build-ui", "gardener", "shipper", "validator", "wall-ui"]
    text = _offline_warning(names)
    assert "\n" not in text
    assert text.count("offline") == 1
    assert text.startswith("desks ")
    assert text.endswith(_TAIL)
    for name in names:
        assert repr(name) in text
