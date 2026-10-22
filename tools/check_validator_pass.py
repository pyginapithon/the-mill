#!/usr/bin/env python3
"""The Validator gate as a check (#810, F110). Standard library only.

  python3 tools/check_validator_pass.py      (in GitHub Actions)

Reads the event JSON at GITHUB_EVENT_PATH, the repo from GITHUB_REPOSITORY
and a read-only GITHUB_TOKEN (statuses and pull requests read).

merge_group: finds every PR in the queue entry (the pr-N in the queue
branch name and the "(#N)" squash subjects between the base and the queued
head) and requires the latest `validator` commit status on each PR's head
sha to be success. Anything else, or no PR found, fails.

pull_request: reports the `validator` state on the PR head and passes. The
queue is the gate: a PR may wait for its PASS without a red check.

The report names PR numbers, shas and states, never PR text.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from typing import Callable

CONTEXT = "validator"
QUEUE_REF_RE = re.compile(r"^(?:refs/heads/)?gh-readonly-queue/[^/]+(?:/[^/]+)*/pr-(\d+)-[0-9a-f]{40}$")
SUBJECT_PR_RE = re.compile(r"\(#(\d+)\)\s*$")
API = "https://api.github.com"

Fetch = Callable[[str], object]


def http_fetch(path: str) -> object:
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN", ""),
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed https host)
        return json.load(r)


def queue_prs(event: dict, repo: str, fetch: Fetch) -> list[int]:
    """PR numbers in a merge_group entry, ascending."""
    mg = event.get("merge_group") or {}
    nums: set[int] = set()
    m = QUEUE_REF_RE.match(str(mg.get("head_ref", "")))
    if m:
        nums.add(int(m.group(1)))
    base, head = str(mg.get("base_sha", "")), str(mg.get("head_sha", ""))
    if re.fullmatch(r"[0-9a-f]{40}", base) and re.fullmatch(r"[0-9a-f]{40}", head):
        cmp = fetch(f"/repos/{repo}/compare/{base}...{head}")
        for c in (cmp or {}).get("commits", []) if isinstance(cmp, dict) else []:
            subject = str((c.get("commit") or {}).get("message", "")).split("\n", 1)[0]
            s = SUBJECT_PR_RE.search(subject)
            if s:
                nums.add(int(s.group(1)))
    return sorted(nums)


def validator_state(repo: str, sha: str, fetch: Fetch) -> str:
    """Latest `validator` status on sha: success, failure, error, pending or missing."""
    combined = fetch(f"/repos/{repo}/commits/{sha}/status?per_page=100")
    for st in (combined or {}).get("statuses", []) if isinstance(combined, dict) else []:
        if st.get("context") == CONTEXT:
            return str(st.get("state", "missing"))
    return "missing"


def run(event_name: str, event: dict, repo: str, fetch: Fetch, out=print) -> int:
    if event_name == "merge_group":
        prs = queue_prs(event, repo, fetch)
        if not prs:
            out("FAIL: no PR found in this merge queue entry (failing closed)")
            return 1
        bad = 0
        for n in prs:
            pr = fetch(f"/repos/{repo}/pulls/{n}")
            sha = str(((pr or {}).get("head") or {}).get("sha", "")) if isinstance(pr, dict) else ""
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                out(f"FAIL: PR #{n}: head sha not readable")
                bad += 1
                continue
            state = validator_state(repo, sha, fetch)
            ok = state == "success"
            out(f"{'OK' if ok else 'FAIL'}: PR #{n} head {sha[:12]}: {CONTEXT} {state}")
            bad += 0 if ok else 1
        if bad:
            out(f"Validator has not passed {bad} PR head(s) in this entry; it leaves the queue.")
            return 1
        return 0
    if event_name == "pull_request":
        pr = event.get("pull_request") or {}
        sha = str((pr.get("head") or {}).get("sha", ""))
        state = validator_state(repo, sha, fetch) if re.fullmatch(r"[0-9a-f]{40}", sha) else "missing"
        out(f"PR #{pr.get('number')} head {sha[:12]}: {CONTEXT} {state}"
            " (report only here; the merge queue requires success on this sha)")
        return 0
    out(f"nothing to check on {event_name}")
    return 0


def main() -> int:
    path = os.environ.get("GITHUB_EVENT_PATH", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not path or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        print("FAIL: GITHUB_EVENT_PATH and GITHUB_REPOSITORY are required")
        return 2
    with open(path, encoding="utf-8") as f:
        event = json.load(f)
    return run(os.environ.get("GITHUB_EVENT_NAME", ""), event, repo, http_fetch)


if __name__ == "__main__":
    raise SystemExit(main())
