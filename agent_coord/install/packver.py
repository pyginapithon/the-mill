"""the-mill dist version. Git checkout pyproject wins over pip dist. Not a git SHA."""
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
