"""mill --version names the commit of a build that is not a release (#538). Regression row F61 (dev-version).

A build from a main sha keeps the last release's number until the bump; the
version line adds +g<sha7> when the commit is known: a git checkout, or a pip
install from a git URL (direct_url.json vcs_info). A release install prints
the bare number, so the CLI smoke check (-V equals the dist version) holds.
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from agent_coord.__main__ import main
from agent_coord.install import packver


class _Dist:
    def __init__(self, direct):
        self.direct = direct

    def read_text(self, name):
        return json.dumps(self.direct) if name == "direct_url.json" and self.direct is not None else None


def _no_checkout(monkeypatch):
    monkeypatch.setattr(packver, "_checkout_root", lambda: None)


def test_release_install_prints_the_bare_number(monkeypatch):
    _no_checkout(monkeypatch)
    monkeypatch.setattr(packver, "_dist", lambda: _Dist(None))
    assert packver.version_line() == packver.package_version()


def test_install_from_a_local_folder_has_no_commit(monkeypatch):
    _no_checkout(monkeypatch)
    monkeypatch.setattr(packver, "_dist", lambda: _Dist({"url": "file:///tmp/src", "dir_info": {}}))
    assert packver.version_line() == packver.package_version()


def test_install_from_a_git_url_names_the_commit(monkeypatch):
    _no_checkout(monkeypatch)
    sha = "d83656b2ae028e571acbf20e54b39c81434e10dc"
    monkeypatch.setattr(packver, "_dist", lambda: _Dist(
        {"url": "https://github.com/pyginapithon/the-mill", "vcs_info": {"vcs": "git", "commit_id": sha}}))
    assert packver.version_line() == packver.package_version() + "+gd83656b"


def test_a_checkout_names_its_head(monkeypatch, tmp_path):
    monkeypatch.setattr(packver, "_checkout_root", lambda: tmp_path)
    monkeypatch.setattr(packver, "_git_head", lambda root: "abc1234" if root == tmp_path else "")
    assert packver.version_line().endswith("+gabc1234")


def test_bad_or_missing_metadata_never_breaks_the_line(monkeypatch):
    _no_checkout(monkeypatch)

    class Bad:
        def read_text(self, name):
            return "{not json"

    monkeypatch.setattr(packver, "_dist", lambda: Bad())
    assert packver.version_line() == packver.package_version()
    monkeypatch.setattr(packver, "_dist", lambda: None)
    assert packver.version_line() == packver.package_version()


def test_the_flag_prints_the_version_line(monkeypatch):
    monkeypatch.setattr(packver, "version_line", lambda: "9.9.9+g1234567")
    for flag in ("--version", "-V"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            assert main([flag]) == 0
        assert buf.getvalue() == "9.9.9+g1234567\n"
