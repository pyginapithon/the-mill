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
    text = _code(WF / "release.yml")
    assert "id-token: write" in text
    assert "secrets." not in text
    assert "password:" not in text
