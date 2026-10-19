"""Import-time Python version gate (stdlib only).

Must stay parseable on CPython 3.8: no PEP604 unions, no package imports.
MIN=(3,10). Used by package bootstrap before coord/presence load.
"""
import sys

MIN = (3, 10)


def python_too_old(version=None):
    """True when interpreter (or injected version) is below MIN.

    version: None -> sys.version_info[:2]; else tuple like (3, 8).
    """
    if version is None:
        ver = tuple(sys.version_info[:2])
    else:
        ver = tuple(version)
    if len(ver) < 2:
        ver = (ver[0], 0) if ver else (0, 0)
    return ver < MIN


def gate_message(version=None):
    """Human message pointing at uv + CPython 3.12 (no traceback)."""
    if version is None:
        major, minor = sys.version_info[:2]
    else:
        ver = tuple(version)
        if len(ver) < 2:
            ver = (ver[0], 0) if ver else (0, 0)
        major, minor = int(ver[0]), int(ver[1])
    return (
        "Python %d.%d is too old; mill needs Python %d.%d+.\n"
        "Hint: use uv + CPython 3.12 (e.g. uv python install 3.12; "
        "uv venv --python 3.12).\n"
        % (major, minor, MIN[0], MIN[1])
    )


def exit_if_too_old(version=None):
    """Print gate_message to stderr and exit 2 when too old; else return None."""
    if not python_too_old(version=version):
        return None
    sys.stderr.write(gate_message(version=version))
    raise SystemExit(2)
