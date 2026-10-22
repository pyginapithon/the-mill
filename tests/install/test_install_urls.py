"""Install one-liners and live links point at the GitHub repo, not the GitLab archive.

The GitLab project is a frozen read-only archive. A shipped doc or script that
fetches from it would install a stale tree, so no tracked file may point at
the project there or use the GitLab raw form. Forbidden strings are assembled
at run time so this file passes its own scan.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD_PROJECT = "gitlab" + ".com/pyginapithon"
GITLAB_RAW = "/-/" + "raw/"
RAW = "https://raw.githubusercontent.com/si4ai/the-mill/main/scripts/"


def _tracked() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [p for p in out.decode("utf-8", "replace").split("\0") if p]


def test_no_tracked_file_points_at_the_gitlab_archive() -> None:
    bad = []
    for rel in _tracked():
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        for needle in (OLD_PROJECT, GITLAB_RAW):
            if needle in text:
                bad.append(f"{rel}: {needle}")
    assert not bad, bad


def test_install_one_liners_use_github_raw() -> None:
    for rel in ("README.md", "docs/install/HOST.md", "docs/protocol/usecases.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert RAW + "install.cmd" in text, rel
        assert RAW + "bootstrap.sh" in text, rel
    for rel in ("scripts/install.cmd", "agent_coord/install/scripts/install.cmd"):
        assert RAW + "bootstrap.ps1" in (ROOT / rel).read_text(encoding="utf-8"), rel


# #810: the repo moved from the personal account to the si4ai org. The old
# path still redirects, but links and one-liners name the org. Assembled so
# this file passes its own scan.
OLD_GITHUB = ("github.com/", "githubusercontent.com/")
OLD_OWNER_REPO = "pygin" + "apithon/the-mill"


def test_no_tracked_file_points_at_the_old_github_owner() -> None:
    bad = []
    for rel in _tracked():
        path = ROOT / rel
        if not path.is_file() or rel == "CHANGELOG.md":
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        for host in OLD_GITHUB:
            if host + OLD_OWNER_REPO in text:
                bad.append(f"{rel}: {host}")
    assert not bad, bad


def test_pyproject_urls_name_the_org_repo() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.urls]" in text
    assert 'Source = "https://github.com/si4ai/the-mill"' in text
    assert 'Issues = "https://github.com/si4ai/the-mill/issues"' in text
