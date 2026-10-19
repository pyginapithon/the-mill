"""A mill token is the stored string.

Session files and /ws rooms use the desk name. slug() checks the token.
"""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path

_IDENT = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_RESOURCE = re.compile(r"^[A-Za-z0-9._/-]{1,255}$")

STABLE_HUMANS = frozenset({"setter-upper", "human"})


def desk(name: str) -> str:
    """Desk name used for the session file and the /ws room."""
    return (name or "").strip()


def desk_name(path: str) -> str:
    """Desk name from a session path or a /ws path segment."""
    return (path or "").strip()


def slug(value: str, *, kind: str = "id", maxlen: int = 64) -> str:
    from agent_coord.helpers.errors import CoordError

    try:
        return ident(value, kind=kind, maxlen=maxlen)
    except ValueError as e:
        raise CoordError(str(e)) from e


def ident(value: str, *, kind: str = "id", maxlen: int = 64) -> str:
    """Mill token: a stored name, or a hold resource path when kind is resource."""
    s = (value or "").strip().replace("\\", "/")
    pat = _RESOURCE if kind == "resource" else _IDENT
    cap = 255 if kind == "resource" else maxlen
    if not pat.match(s) or len(s) > cap:
        raise ValueError(f"bad {kind}: {value!r}")
    return s


def file_key(path: str | Path, project_root: str | Path | None = None) -> str:
    """Path -> mill hold resource key, relative to the project root when it fits."""
    raw = Path(str(path).replace("\\", "/"))
    roots: list[Path] = []
    if project_root:
        roots.append(Path(project_root))
    roots.append(Path.cwd())
    roots.append(Path(__file__).resolve().parents[2])
    if raw.is_absolute() or (len(str(raw)) > 1 and str(raw)[1] == ":"):
        try:
            resolved = raw.resolve()
        except OSError:
            resolved = raw
        for root in roots:
            try:
                rel = resolved.relative_to(root.resolve())
                return ident(rel.as_posix().lstrip("./"), kind="resource")
            except (ValueError, OSError):
                continue
        key = resolved.as_posix()
        if len(key) > 1 and key[1] == ":":
            key = key[2:]
        key = key.lstrip("/")
        return ident(key[:255], kind="resource")
    return ident(raw.as_posix().lstrip("./"), kind="resource")


def this_host() -> str:
    raw = (os.environ.get("AGENT_COORD_NODE") or "").strip()
    if not raw:
        from agent_coord.config import load_file

        raw = str(load_file().get("node") or "").strip()
    if not raw:
        raw = socket.gethostname().split(".")[0]
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-.")[:64]
    return cleaned or "node"


def iso6(v) -> str:
    """Wire timestamps at DATETIME(6) precision."""
    if v is None:
        return ""
    if hasattr(v, "strftime"):
        micro = getattr(v, "microsecond", 0) or 0
        return v.strftime("%Y-%m-%d %H:%M:%S") + f".{micro:06d}"
    return str(v)



def is_stable_human(owner: str | None) -> bool:
    raw = (owner or "").strip()
    if not raw:
        return False
    try:
        s = ident(raw)
    except Exception:
        s = raw.lower()
    return s in STABLE_HUMANS
