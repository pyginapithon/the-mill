"""F35 (ci-one-pipeline): CI runs one pipeline per push (workflow rules) and still ships from v* tags."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")


def test_workflow_runs_mr_default_branch_and_tags_only() -> None:
    head = CI.split("\nstages:", 1)[0]
    assert "\nworkflow:\n  rules:\n" in head
    mr = head.index('- if: $CI_PIPELINE_SOURCE == "merge_request_event"')
    skip = head.index("- if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS\n      when: never")
    tag = head.index("- if: $CI_COMMIT_TAG\n")
    main = head.index("- if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH")
    # The open-MR skip sits before the default-branch rule, after the MR rule.
    assert mr < skip < main and tag > 0
    assert head.count("when: never") == 1


def test_no_always_true_job_rules_and_release_on_v_tags() -> None:
    assert "- if: $CI_PIPELINE_SOURCE\n" not in CI
    for job in ("build_pack:", "check_pack:", "mill_cli_smoke:", "pytest_no_sql:", "pytest_sql:", "release_pypi:"):
        assert "\n" + job + "\n" in CI, job
    release = CI.split("\nrelease_pypi:\n", 1)[1]
    assert release.split("\n  variables:", 1)[0].strip().endswith("rules:\n    - if: $CI_COMMIT_TAG =~ /^v/")
