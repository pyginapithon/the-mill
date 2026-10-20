"""the-mill dist version. Git checkout pyproject wins over pip dist.

package_version is never a git SHA (replies carry it). version_line, for
mill --version only, adds +g<sha7> for a build that is not a release (#538).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _pyproject_version() -> str | None:
    py = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if not py.is_file():
        return None
    for line in py.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("version") and "=" in s:
            return s.split("=", 1)[1].strip().strip("'\"")
    return None


def package_version_info() -> dict[str, Any]:
    """Honest pack version + where it came from (pyproject | dist | local)."""
    found = _pyproject_version()
    if found:
        return {"version": found, "source": "pyproject"}
    from importlib.metadata import PackageNotFoundError, version

    try:
        return {"version": version("the-mill"), "source": "dist"}
    except PackageNotFoundError:
        return {"version": "0+local", "source": "local"}


def package_version() -> str:
    """Checkout pyproject if present (git mill); else installed dist; else 0+local."""
    return str(package_version_info()["version"])


def checkout_dist_line() -> str:
    """One stderr line when the imported checkout version is not the installed dist."""
    imported = _pyproject_version()
    if not imported:
        return ""
    from importlib.metadata import PackageNotFoundError, version

    try:
        dist = version("the-mill")
    except PackageNotFoundError:
        return ""
    if dist == imported:
        return ""
    return "mill: imported %s differs from installed the-mill %s" % (imported, dist)


def _checkout_root() -> Path | None:
    """The git checkout this package is imported from, or None (an installed copy)."""
    root = Path(__file__).resolve().parent.parent.parent
    if (root / "pyproject.toml").is_file() and (root / ".git").exists():
        return root
    return None


def _git_head(root: Path) -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short=7", "HEAD"],
            capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    sha = (out.stdout or "").strip()
    return sha if out.returncode == 0 and sha else ""


def _dist() -> Any:
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        return distribution("the-mill")
    except PackageNotFoundError:
        return None


def build_commit() -> str:
    """Short commit of a build that is not a release, or "" (#538).

    A git checkout: its HEAD. A pip install from a git URL: the commit pip
    recorded (direct_url.json vcs_info). A release or a plain folder install
    records none.
    """
    root = _checkout_root()
    if root is not None:
        return _git_head(root)
    import json

    try:
        dist = _dist()
        raw = dist.read_text("direct_url.json") if dist is not None else None
        info = json.loads(raw) if raw else {}
    except (OSError, ValueError, AttributeError):
        return ""
    vcs = info.get("vcs_info") if isinstance(info, dict) else None
    commit = str((vcs or {}).get("commit_id") or "") if isinstance(vcs, dict) else ""
    return commit[:7]


def version_line() -> str:
    """What mill --version prints: the pack version, plus +g<sha7> for a build
    that is not a release (#538). The version in replies stays the pack version."""
    sha = build_commit()
    return package_version() + ("+g" + sha if sha else "")
