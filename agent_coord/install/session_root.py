"""Session disk root. Mill primitive; git worktree is an adapter later.

A clocked-in session has a disk root it may write. Other sessions do not share
that root by default. File leases are (project_id, root_key, resource).
gym.pt stays a leased station file (agent_lock), not a MySQL blob.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def normalize(path: str | Path | None) -> str:
    """Absolute resolved path, posix slashes, no trailing slash (except drive root)."""
    if path is None or str(path).strip() == "":
        raw = Path.cwd()
    else:
        raw = Path(str(path).strip()).expanduser()
    try:
        p = raw.resolve()
    except OSError:
        p = raw.absolute()
    s = p.as_posix()
    if len(s) > 3 and s.endswith("/") and not s.endswith(":/"):
        s = s.rstrip("/")
    return s[:512]


def _posixish(path: str) -> str:
    s = (path or "").replace("\\", "/").strip().lower()
    if len(s) >= 2 and s[1] == ":":
        s = "/" + s[0] + s[2:]
    if len(s) > 1:
        s = s.rstrip("/")
    return s or "/"


def refuse_reason(path: str | Path | None) -> str | None:
    """Why this path must not be a mill session root. None = allowed."""
    if path is None or str(path).strip() == "":
        return "session root empty"
    raw = str(path).replace("\\", "/").strip()
    raw_l = raw.lower().rstrip("/")
    # C:/ resolves under the cwd on Linux, so catch the drive root from the raw text.
    if len(raw_l) == 2 and raw_l[1] == ":":
        return "refuse bare drive as session root"
    raw_parts = [p for p in raw_l.split("/") if p]
    if raw_l == "/mnt/c" or (len(raw_parts) == 2 and raw_parts[0] == "mnt" and len(raw_parts[1]) == 1):
        return "refuse WSL drive root as session root"
    if "/mnt/" in raw_l + "/" and "/windows" in raw_l:
        return "refuse Windows/System32 as session root"
    n = normalize(path)
    s = _posixish(n)
    if s == "/":
        return "refuse Unix / as session root"
    parts = [p for p in s.split("/") if p]
    if len(parts) == 1 and len(parts[0]) == 1:
        return "refuse bare drive as session root"
    if len(parts) == 2 and parts[0] == "mnt" and len(parts[1]) == 1:
        return "refuse WSL drive root as session root"
    joined = "/" + "/".join(parts)
    if "/windows" in joined or joined.endswith("/system32") or "/system32/" in joined:
        return "refuse Windows/System32 as session root"
    try:
        home = normalize(Path.home())
        office = normalize(_office_dest())
        if n == home and n != office:
            return "refuse ~ as a second dest; office dest is session root"
    except OSError:
        pass
    return None


def _office_dest() -> Path:
    env = (os.environ.get("AGENT_COORD_MILL_HOME") or "").strip()
    if env:
        return Path(env)
    return Path.home() / ".mill"


def default_root(project_root: str | Path | None = None) -> str:
    """Clock-in default: office dest (~/.mill), not cwd. Explicit project_root if allowed."""
    if project_root:
        n = normalize(project_root)
        err = refuse_reason(n)
        if err:
            raise ValueError(err)
        return n
    n = normalize(_office_dest())
    err = refuse_reason(n)
    if err:
        raise ValueError(err)
    return n


def choose_root(root: str | Path | None = None) -> str:
    """Session root: --root if set, else office dest. Never cwd. Fail closed on refuse."""
    if root is None or str(root).strip() == "":
        return default_root()
    n = normalize(root)
    err = refuse_reason(n)
    if err:
        raise ValueError(err)
    return n


def is_file_resource(resource: str) -> bool:
    """File-like keys take a session root. Abstract names (dump, mysql-solve) do not."""
    s = (resource or "").replace("\\", "/").strip()
    if not s:
        return False
    return "/" in s or bool(Path(s).suffix)


def root_key(root: str | None) -> str:
    """Short hash for the lock PK. Empty iff no disk root (abstract resource)."""
    n = (root or "").strip()
    if not n:
        return ""
    return hashlib.sha256(n.encode("utf-8")).hexdigest()[:16]


def for_lock(root: str | None, resource: str) -> tuple[str, str]:
    """Return (disk_root, root_key) stored on agent_lock."""
    if not is_file_resource(resource):
        return "", ""
    n = normalize(root) if root else ""
    if not n:
        return "", ""
    return n, root_key(n)


def base_moved(
    disk_root: str | None,
    session_root: str | None,
    root_key: str | None,
    resource: str = "",
) -> bool:
    """True when a live file lease root is gone or not the session root.

    Abstract names (dump, mysql-solve) keep root_key '' and never fire.
    gym.pt stays a station FILE. Not a STALE card state.
    """
    if not (root_key or "").strip():
        return False
    if resource and not is_file_resource(resource):
        return False
    disk = (disk_root or "").strip()
    if disk:
        try:
            if not Path(disk).exists():
                return True
        except OSError:
            return True
    sess = (session_root or "").strip()
    if sess and disk:
        return normalize(sess) != normalize(disk)
    return False
