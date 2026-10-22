"""ux9 cold-round fixes: help <unknown>, refusal exit code, --yes hint."""
import subprocess

import pytest

from agent_coord.__main__ import main
from agent_coord.client.language import confirm, retype
from agent_coord.helpers.errors import CoordError
from agent_coord.install.office import help_text


def test_help_unknown_is_one_line_with_closest(capsys):
    assert help_text("tag") == "mill help: no such topic 'tag'; closest: mill help label\n"
    assert main(["help", "tag"]) == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err.count("\n") == 1


def test_help_known_command_unchanged():
    assert help_text("label").startswith("# mill label")


def test_one_liner_keeps_the_command_exit_code():
    rc = subprocess.run(["bash", "-c", 'sleep 30 >/dev/null 2>&1 & trap "kill $!" EXIT; exit 3']).returncode
    assert rc == 3


def test_no_terminal_prompt_says_add_yes(monkeypatch):
    monkeypatch.setattr("agent_coord.client.language._tty", lambda: False)
    for fn in (lambda: confirm("create roster x?", yes=False), lambda: retype("x", "retire", yes=False)):
        with pytest.raises(CoordError) as e:
            fn()
        assert str(e.value).endswith("add --yes") and "\n" not in str(e.value)
