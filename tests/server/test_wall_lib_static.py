"""Wall board href lib/*.js must resolve to wall_ui/lib/*."""
from __future__ import annotations

from agent_coord.server.middleware import WALL_UI_LIB, _safe_static


def test_safe_static_lib_prefix_maps_to_wall_ui_lib():
    for name in (
        "lib/data.js",
        "lib/tabs.js",
        "lib/theme.js",
        "lib/theme.css",
        "lib/keys.js",
        "lib/popup.js",
        "lib/table.js",
        "lib/graph.js",
    ):
        found = _safe_static(name)
        assert found is not None, name
        assert found.is_file(), name
        assert found.parent.resolve() == WALL_UI_LIB.resolve(), (name, found)


def test_safe_static_mail_js_still_under_default():
    found = _safe_static("mail/mail.js")
    assert found is not None and found.is_file()
    assert found.name == "mail.js"
