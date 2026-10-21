"""#623 wake URL dot segments: check_url refuses a path with a . or .. segment, or an
encoded slash, backslash or dot, before the allowlist prefix check, so a URL
under the allowed prefix cannot climb out of it. Checked at arm and at POST.
Row F70 (wake-dot-path)."""
from __future__ import annotations

import pytest

from agent_coord.server import wake
from tests.server.webhook_fixtures import HOOK_HOST, HOOK_KEY, arm, opener

BASE = "https://api2.cursor.sh/automations/webhook/"


@pytest.mark.parametrize(
    "tail",
    [
        "../../other/x",
        "./x",
        "x/../../../admin",
        "x/..",
        "%2e%2e/%2e%2e/other",
        "%2E%2E/other",
        ".%2e/other",
        "%252e%252e/other",
        "x%2f..%2f..%2fother",
        "x%2Fy",
        "..%5c..%5cother",
        "x\\..\\other",
    ],
)
def test_dot_segments_and_encoded_variants_are_refused(monkeypatch, tail):
    monkeypatch.delenv("AGENT_COORD_WAKE_HOSTS", raising=False)
    with pytest.raises(wake.WakeRefused) as ei:
        wake.check_url(BASE + tail)
    text = str(ei.value)
    assert "dot segment" in text and "copy the webhook URL from the routine again" in text
    assert tail not in text


@pytest.mark.parametrize("tail", ["00000000-0000-4000-8000-000000000000", "a.b/c..d", "v1.2"])
def test_plain_dots_inside_a_segment_are_fine(monkeypatch, tail):
    monkeypatch.delenv("AGENT_COORD_WAKE_HOSTS", raising=False)
    url, host = wake.check_url(BASE + tail)
    assert url == BASE + tail and host == "api2.cursor.sh"


def test_the_desk_side_shape_check_refuses_it_too():
    with pytest.raises(wake.WakeRefused):
        wake.check_url(BASE + "../x", allow_only=False)


def test_post_time_recheck_refuses_a_stored_dot_path(monkeypatch):
    """A row armed before this check (or written by hand) is refused at POST time."""
    bad = f"https://{HOOK_HOST}/automations/webhook/../../latest/meta-data"
    arm(monkeypatch, armed={"d1": (bad, HOOK_KEY)})
    calls = []
    with opener(lambda req, timeout: calls.append(req)):
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 1}) == "error"
    assert calls == []
