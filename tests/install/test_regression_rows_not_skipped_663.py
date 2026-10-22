"""#663 (F112): a regression test the matrix cites is never skipped by collection.

A conftest hook sees every collected item in the session, not only the
items under its own directory. tests/validator/conftest.py marked every
item whose path contained "validator" as skipped unless MILL_LIVE=1, so the
F110 and F111 tests in tests/install were skipped in CI's no-SQL run and
the job stayed green. These tests run in pytest_no_sql and fail it when a
cited regression test is skipped at collection there again.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs" / "security" / "REGRESSION-MATRIX.md"
F110_F111 = (
    "tests/install/test_validator_pass_810.py",
    "tests/install/test_validator_status_identity_811.py",
)
LIVE_DIR = "tests/validator"

# Loaded into the child pytest with -p: records each collected item and the
# skip its marks evaluate to (skip or a true skipif), after -m deselection.
PROBE = '''
import json, os
from _pytest.skipping import evaluate_skip_marks

def pytest_collection_finish(session):
    out = []
    for item in session.items:
        skip = evaluate_skip_marks(item)
        out.append([item.nodeid, skip.reason if skip else None])
    with open(os.environ["MILL_ROW_PROBE_OUT"], "w", encoding="utf-8") as fh:
        json.dump(out, fh)
'''


def _env(tmp: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("MILL_LIVE", None)  # the CI no-SQL run is not live
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONPATH"] = os.pathsep.join([str(tmp), *filter(None, [env.get("PYTHONPATH")])])
    return env


def _pytest(tmp: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-m", "not sql", *args],
        cwd=ROOT, env=_env(tmp), capture_output=True, text=True, timeout=600,
    )


def _cited_files() -> set[str]:
    """Every tests/...py path in the regression-test column of a matrix row."""
    files: set[str] = set()
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| ID "):
            continue
        cells = line.strip().strip("|").split(" | ")
        files.update(re.findall(r"(tests/[\w/.-]+\.py)", cells[-1]))
    return files


def test_the_matrix_cites_test_files():
    files = _cited_files()
    assert set(F110_F111) <= files
    assert len(files) > 50, sorted(files)


def test_every_cited_regression_test_file_exists():
    missing = sorted(f for f in _cited_files() if not (ROOT / f).is_file())
    assert not missing, f"REGRESSION-MATRIX.md cites test files that do not exist: {missing}"


def test_no_cited_regression_test_is_skipped_at_collection(tmp_path: Path):
    """Collect the whole tree as pytest_no_sql does (MILL_LIVE unset, every
    conftest loaded) and fail on any cited test that collection skips."""
    (tmp_path / "_mill_row_probe.py").write_text(PROBE, encoding="utf-8")
    out = tmp_path / "items.json"
    env_out = {"MILL_ROW_PROBE_OUT": str(out)}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-p", "_mill_row_probe",
         "-m", "not sql", "--collect-only", "-q", "tests"],
        cwd=ROOT, env={**_env(tmp_path), **env_out}, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
    items = json.loads(out.read_text(encoding="utf-8"))
    cited = _cited_files()
    by_file: dict[str, int] = {}
    skipped = []
    for nodeid, reason in items:
        path = nodeid.split("::", 1)[0]
        by_file[path] = by_file.get(path, 0) + 1
        if path in cited and reason is not None:
            skipped.append(f"{nodeid}: {reason}")
    assert not skipped, "cited regression tests skipped in the no-SQL run:\n" + "\n".join(skipped)
    for path in F110_F111:
        assert by_file.get(path, 0) > 0, f"{path} collected nothing"
    # the live probes stay gated: collection still skips tests/validator
    live = [(n, r) for n, r in items if n.startswith(LIVE_DIR + "/")]
    assert live and all(r for _n, r in live), live


def test_f110_f111_tests_pass_beside_the_live_package(tmp_path: Path):
    """Run the F110/F111 files with tests/validator in the same session, as
    `pytest tests` does: every F110/F111 case passes, none is skipped, and
    every tests/validator case is still skipped without MILL_LIVE=1."""
    junit = tmp_path / "junit.xml"
    proc = _pytest(tmp_path, "-rs", f"--junitxml={junit}", *F110_F111, LIVE_DIR)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
    rows: dict[str, list[str]] = {"f110_f111": [], "live": []}
    for case in ET.parse(junit).iter("testcase"):
        cls = case.get("classname", "")
        outcome = "passed"
        for tag in ("skipped", "failure", "error"):
            if case.find(tag) is not None:
                outcome = tag
        if cls.startswith("tests.validator."):
            rows["live"].append(outcome)
        elif any(cls == f[:-3].replace("/", ".") for f in F110_F111):
            rows["f110_f111"].append(outcome)
    assert rows["f110_f111"], proc.stdout[-2000:]
    assert set(rows["f110_f111"]) == {"passed"}, (rows, proc.stdout[-3000:])
    assert rows["live"] and set(rows["live"]) == {"skipped"}, rows
