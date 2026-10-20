"""GitHub Actions supply-chain rules as checks, not prose.

Every third-party action is pinned to a full commit SHA, no workflow uses
pull_request_target, no job runs on a self-hosted runner, every workflow sets
top-level permissions, and every job that scans history clones it in full.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows"
USES_RE = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
SHA_REF_RE = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def _code(p: Path) -> str:
    """Workflow text without comment lines (comments may name banned words)."""
    return "\n".join(ln for ln in p.read_text(encoding="utf-8").splitlines() if not ln.lstrip().startswith("#"))


def _workflows() -> list[Path]:
    return sorted(WF.glob("*.yml")) + sorted(WF.glob("*.yaml"))


def test_workflows_exist() -> None:
    names = {p.name for p in _workflows()}
    assert {"ci.yml", "release.yml", "codeql.yml"} <= names, names


def test_actions_pinned_to_full_sha() -> None:
    bad = []
    for p in _workflows():
        for ref in USES_RE.findall(p.read_text(encoding="utf-8")):
            if ref.startswith("./"):
                continue
            if not SHA_REF_RE.match(ref):
                bad.append(f"{p.name}: {ref}")
    assert not bad, bad


def test_no_pull_request_target_or_self_hosted() -> None:
    for p in _workflows():
        text = _code(p)
        assert "pull_request_target" not in text, p.name
        assert "self-hosted" not in text, p.name


def test_top_level_permissions_set() -> None:
    for p in _workflows():
        text = p.read_text(encoding="utf-8")
        assert re.search(r"^permissions:", text, re.M), p.name


def _job(text: str, name: str) -> str:
    body = text.split(f"\n  {name}:\n", 1)[1]
    nxt = re.search(r"\n  [a-z_]+:\n", body)
    return body[: nxt.start()] if nxt else body


def test_history_jobs_clone_full_history() -> None:
    """check_pack and both pytest jobs scan commit messages; shallow fails closed."""
    text = (WF / "ci.yml").read_text(encoding="utf-8")
    for name in ("check_pack", "pytest_no_sql", "pytest_sql"):
        job = _job(text, name)
        assert job.count("fetch-depth: 0") == job.count("actions/checkout@"), name
        assert "fetch-depth: 0" in job, name


def test_publish_jobs_use_oidc_not_tokens() -> None:
    """No stored publish token. The only secret is the #339 private-name list."""
    text = _code(WF / "release.yml")
    assert "id-token: write" in text
    assert set(re.findall(r"secrets\.(\w+)", text)) == {"MILL_PRIVATE_NAMES"}
    assert "secrets." not in _job(text, "publish_pypi")
    assert "password:" not in text


def _on(text: str) -> str:
    """The top-level on: block of a workflow."""
    return text.split("\non:\n", 1)[1].split("\n\n", 1)[0]


def test_release_runs_only_on_v_tags_or_by_hand() -> None:
    """S-9: a push to main or a PR never starts release.yml."""
    on = _on((WF / "release.yml").read_text(encoding="utf-8"))
    assert re.search(r'^  push:\n    tags: \["v\*"\]$', on, re.M), on
    assert "branches" not in on and "pull_request" not in on and "schedule" not in on
    assert set(re.findall(r"^  (\w+):", on, re.M)) == {"push", "workflow_dispatch"}


def test_publish_jobs_are_gated_by_environment_and_event() -> None:
    text = _code(WF / "release.yml")
    pypi = _job(text, "publish_pypi")
    assert "name: pypi" in pypi and "startsWith(github.ref, 'refs/tags/v')" in pypi
    assert "testpypi" not in text.casefold() and "test.pypi.org" not in text
    jobs = set(re.findall(r"^  (\w+):\n    ", text.split("\njobs:\n", 1)[1], re.M))
    assert jobs == {"ci", "verify", "publish_pypi"}, jobs


def test_publish_job_is_oidc_in_pypi_env_with_pinned_action() -> None:
    pypi = _job(_code(WF / "release.yml"), "publish_pypi")
    assert "id-token: write" in pypi and "name: pypi" in pypi
    assert re.search(r"uses: pypa/gh-action-pypi-publish@[0-9a-f]{40}", pypi), pypi
    assert "password" not in pypi and "secrets." not in pypi and "repository-url" not in pypi


def test_ci_and_codeql_never_publish() -> None:
    for name in ("ci.yml", "codeql.yml"):
        text = _code(WF / name)
        assert "id-token: write" not in text, name
        assert "pypi-publish" not in text and "twine upload" not in text, name


def test_tree_hygiene_runs_wherever_check_pack_runs() -> None:
    """S-11: whole-tree hygiene drift fails CI, not only the local hook."""
    ci = _job((WF / "ci.yml").read_text(encoding="utf-8"), "check_pack")
    verify = _job((WF / "release.yml").read_text(encoding="utf-8"), "verify")
    for name, job in (("ci check_pack", ci), ("release verify", verify)):
        assert "python tools/check_pack.py dist" in job, name
        assert "python tools/precommit_hygiene.py tree" in job, name
