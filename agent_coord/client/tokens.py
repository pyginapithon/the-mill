"""Presence / session token digests + owner-only session token file.

Path: <mill_home>/session/<owner>.token
  Windows: %USERPROFILE%\\.mill\\session\\<owner>.token
  Linux / macOS / WSL ext4: ~/.mill/session/<owner>.token

WSL is Linux: chmod 0o600. icacls is Windows-only, except WSL DrvFS
(/mnt/c/...) where chmod does not enforce NTFS ACLs - then icacls.exe.
Windows mill.exe and WSL mill are different OS users/PID namespaces.
Never print the token. Never put the secret in process env - multi-desk shares env.
AGENT_COORD_MILL_HOME relocates mill_home (tests); default ~/.mill.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

_OWNER = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def token_hash(token: str) -> str:
    """SHA-256 hex digest of a mill session / collect / align token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_file_stem(desk_id: int | str) -> str:
    """Opaque session filename stem: sha256(str(name.id))[:16] (#398).

    desk_id is the salt; stem never contains the desk name.
    """
    return hashlib.sha256(str(int(desk_id)).encode("ascii")).hexdigest()[:16]


def mill_home(dest: Path | None = None) -> Path:
    """Office dest root. Default ~/.mill (not the session token itself)."""
    if dest is not None:
        return Path(dest)
    env = (os.environ.get("AGENT_COORD_MILL_HOME") or "").strip()
    if env:
        return Path(env)
    return Path.home() / ".mill"


def _safe_owner(owner: str) -> str:
    s = (owner or "").strip()
    if not _OWNER.match(s):
        raise ValueError("bad owner for session token file")
    return s


def _catalog_desk(value: str) -> str:
    """Stored desk name."""
    return (value or "").strip()


def session_token_path(
    owner: str,
    *,
    dest: Path | None = None,
    desk_id: int | str | None = None,
) -> Path:
    """Session token path. Prefer hashed stem when desk_id known (#398)."""
    root = mill_home(dest) / "session"
    if desk_id is not None and str(desk_id).strip() != "":
        return root / f"{session_file_stem(desk_id)}.token"
    return root / f"{_safe_owner(owner)}.token"


def is_wsl() -> bool:
    """True on WSL1/WSL2. False on native Linux, macOS, Windows."""
    if sys.platform != "linux":
        return False
    for p in ("/proc/sys/kernel/osrelease", "/proc/version"):
        try:
            if "microsoft" in Path(p).read_text(encoding="utf-8", errors="replace").lower():
                return True
        except OSError:
            continue
    return False


def drvfs_windows_path(posix: str) -> str | None:
    """WSL /mnt/<drive>/... -> C:\\... for icacls.exe. Else None."""
    s = (posix or "").replace("\\", "/").strip()
    parts = [p for p in s.split("/") if p]
    if len(parts) >= 3 and parts[0] == "mnt" and len(parts[1]) == 1 and parts[1].isalpha():
        return parts[1].upper() + ":\\" + "\\".join(parts[2:])
    return None


def _restrict_owner_only(path: Path, *, is_dir: bool = False) -> None:
    """POSIX 0600/0700; Windows icacls current user; WSL DrvFS icacls.exe."""
    mode = 0o700 if is_dir else 0o600
    try:
        os.chmod(path, mode)
    except OSError:
        pass
    win_path, icacls = _acl_target(path)
    if not win_path or is_dir:
        return
    who = _acl_identity(windows=True)
    if not who:
        return
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        subprocess.run(
            [icacls, win_path, "/inheritance:r", "/grant:r", f"{who}:F"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=flags,
        )
    except (OSError, subprocess.SubprocessError):
        return


def _acl_target(path: Path) -> tuple[str, str] | tuple[None, None]:
    if sys.platform == "win32":
        return str(path), "icacls"
    if is_wsl():
        converted = drvfs_windows_path(path.as_posix())
        if converted:
            return converted, "icacls.exe"
    return None, None


def _acl_identity(*, windows: bool) -> str:
    """whoami (DOMAIN\\user) on Windows; whoami.exe from WSL for DrvFS."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    cmd = ["whoami.exe"] if windows and sys.platform != "win32" else ["whoami"]
    try:
        run = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=flags,
        )
        who = (run.stdout or "").strip()
        if who:
            return who
    except (OSError, subprocess.SubprocessError):
        pass
    user = (os.environ.get("USERNAME") or "").strip()
    domain = (os.environ.get("USERDOMAIN") or "").strip()
    if windows and domain and user and domain.upper() != user.upper():
        return f"{domain}\\{user}"
    return user


def write_session_token(
    owner: str,
    token: str,
    *,
    dest: Path | None = None,
    desk_id: int | str | None = None,
) -> Path:
    """Write plaintext token to owner-only file(s). Never logs or prints the token.

    With desk_id (#398): write sha256(desk_id)[:16].token + matching .desk name map.
    Without desk_id: write <name>.token.
    Refuses if this token plaintext already belongs to a *different* desk (#391).
    """
    from agent_coord.helpers.ident import desk as desk_stem

    tok = (token or "").strip()
    if not tok:
        raise ValueError("session token empty")
    from agent_coord.client.offices import current_host_key, current_office, write_desk_token

    if current_office(dest=dest):
        return write_desk_token(owner, tok, host=current_host_key(dest=dest), dest=dest)
    bare = _catalog_desk(owner) or _safe_owner(owner)
    file_stem = desk_stem(bare)
    root = mill_home(dest) / "session"
    root.mkdir(parents=True, exist_ok=True)
    _restrict_owner_only(root, is_dir=True)

    def _bound_name(fp: Path) -> str:
        meta = fp.with_suffix(".desk")
        if meta.is_file():
            try:
                return _catalog_desk(meta.read_text(encoding="utf-8").strip())
            except OSError:
                pass
        return _catalog_desk(fp.stem)

    for fp in root.glob("*.token"):
        try:
            existing = fp.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if existing != tok:
            continue
        other = _bound_name(fp)
        if other and other != bare:
            raise ValueError(
                f"session token already bound to {other}; refuse alias onto {bare} "
                "(mill join that desk; Admin clear is mill reset seat <desk>; do not put the token in env)"
            )

    if desk_id is not None and str(desk_id).strip() != "":
        stem = session_file_stem(desk_id)
        path = root / f"{stem}.token"
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(tok + "\n", encoding="utf-8")
        _restrict_owner_only(tmp, is_dir=False)
        os.replace(tmp, path)
        _restrict_owner_only(path, is_dir=False)
        meta = root / f"{stem}.desk"
        meta.write_text(bare + "\n", encoding="utf-8")
        _restrict_owner_only(meta, is_dir=False)
        for who in (file_stem, bare):
            if not who:
                continue
            alias = session_token_path(who, dest=dest)
            try:
                if alias.is_file() and alias.resolve() != path.resolve():
                    alias.unlink()
            except OSError:
                pass
        return path

    primary = None
    for who in (file_stem, bare):
        if not who:
            continue
        path = session_token_path(who, dest=dest)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(tok + "\n", encoding="utf-8")
        _restrict_owner_only(tmp, is_dir=False)
        os.replace(tmp, path)
        _restrict_owner_only(path, is_dir=False)
        if primary is None:
            primary = path
    if primary is None:
        raise ValueError("bad owner for session token file")
    return primary


def read_session_token(
    owner: str,
    *,
    dest: Path | None = None,
    desk_id: int | str | None = None,
) -> str:
    """Read token from owner-only file, or empty if missing. Never prints."""
    from agent_coord.client.offices import current_host_key, current_office, read_desk_token, write_desk_token

    if current_office(dest=dest):
        host = current_host_key(dest=dest)
        got = read_desk_token(owner, host=host, dest=dest)
        if got:
            return got
        legacy = _legacy_session_token(owner, dest=dest, desk_id=desk_id)
        if legacy:
            write_desk_token(owner, legacy, host=host, dest=dest)
            return legacy
        return ""
    return _legacy_session_token(owner, dest=dest, desk_id=desk_id)


def _legacy_session_token(
    owner: str,
    *,
    dest: Path | None = None,
    desk_id: int | str | None = None,
) -> str:
    from agent_coord.helpers.ident import desk as desk_stem

    root = mill_home(dest) / "session"
    bare = _catalog_desk(owner) if owner else ""
    stem = desk_stem(bare) if bare else ""
    candidates: list[Path] = []
    if desk_id is not None and str(desk_id).strip() != "":
        candidates.append(root / f"{session_file_stem(desk_id)}.token")
    if root.is_dir() and bare:
        for meta in root.glob("*.desk"):
            try:
                mapped = _catalog_desk(meta.read_text(encoding="utf-8").strip())
            except OSError:
                continue
            if mapped == bare:
                candidates.append(meta.with_suffix(".token"))
    if stem:
        candidates.append(session_token_path(stem, dest=dest))
    if bare:
        candidates.append(session_token_path(bare, dest=dest))
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return ""


def clear_session_token(
    owner: str,
    *,
    dest: Path | None = None,
    desk_id: int | str | None = None,
) -> bool:
    """Unlink the session token file (unregister). True if a file was removed."""
    from agent_coord.helpers.ident import desk as desk_stem

    try:
        who = _safe_owner(owner) if owner else ""
    except ValueError:
        who = ""
    bare = _catalog_desk(owner) if owner else who
    stem = desk_stem(bare) if bare else ""
    root = mill_home(dest) / "session"
    removed = False
    paths: list[Path] = []
    if desk_id is not None and str(desk_id).strip() != "":
        hashed = session_file_stem(desk_id)
        paths.extend([root / f"{hashed}.token", root / f"{hashed}.desk"])
    if root.is_dir() and bare:
        for meta in root.glob("*.desk"):
            try:
                mapped = _catalog_desk(meta.read_text(encoding="utf-8").strip())
            except OSError:
                continue
            if mapped == bare:
                paths.append(meta)
                paths.append(meta.with_suffix(".token"))
    for cand in (stem, bare):
        if not cand:
            continue
        try:
            paths.append(session_token_path(cand, dest=dest))
        except ValueError:
            continue
    for path in paths:
        try:
            if path.is_file():
                path.unlink()
                removed = True
        except OSError:
            pass
        tmp = path.with_name(path.name + ".tmp")
        try:
            tmp.unlink()
        except OSError:
            pass
    return removed


def active_desk_path(*, dest: Path | None = None) -> Path:
    """~/.mill/session/active - one-line sticky desk name (not a token). (#492)"""
    return mill_home(dest) / "session" / "active"


def read_active_desk(*, dest: Path | None = None) -> str:
    """Sticky desk file. Verbs must not read this to choose a sender."""
    from agent_coord.client.offices import current_host_key, current_office, read_host_active

    if current_office(dest=dest):
        return _catalog_desk(read_host_active(current_host_key(dest=dest), dest=dest))
    path = active_desk_path(dest=dest)
    try:
        return _catalog_desk(path.read_text(encoding="utf-8").strip())
    except OSError:
        return ""


def write_active_desk(owner: str, *, dest: Path | None = None) -> Path:
    """Persist the stored desk name. Never stores the session token. (#492)"""
    who = _catalog_desk(owner)
    if not who:
        raise ValueError("bad owner for active desk file")
    who = _safe_owner(who)
    from agent_coord.client.offices import current_host_key, current_office, write_host_active

    if current_office(dest=dest):
        return write_host_active(current_host_key(dest=dest), who, dest=dest)
    root = mill_home(dest) / "session"
    root.mkdir(parents=True, exist_ok=True)
    _restrict_owner_only(root, is_dir=True)
    path = active_desk_path(dest=dest)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(who + "\n", encoding="utf-8")
    _restrict_owner_only(tmp, is_dir=False)
    os.replace(tmp, path)
    _restrict_owner_only(path, is_dir=False)
    return path


def resolve_desk_owner(cli_owner: str = "", *, dest: Path | None = None) -> str:
    """Desk this process may speak as.

    The sitting mill connect whose recorded parent pid equals this process's
    parent pid. cli_owner is ignored so argv cannot spoof the sender.
    Does not read the host active file and does not fall back to it.
    """
    _ = cli_owner  # retained for call-site compat; never selects the desk
    _ = dest  # bridge files follow the process mill home, not an override
    from agent_coord.client.ws import bridge_for_parent

    ep = bridge_for_parent()
    if not ep:
        return ""
    return str(ep.get("desk") or "").strip()


def apply_session_token_env(owner: str | None = None, *, dest: Path | None = None) -> bool:

    """Deprecated no-op. Tokens must not enter shared process env (multi-desk).

    Kept so old callers do not crash. Always returns False. (#397)
    """
    return False


def posix_mode(path: Path) -> int:
    """Permission bits (0o777 mask). Meaningful on POSIX/WSL ext4; not NTFS."""
    try:
        return stat.S_IMODE(Path(path).stat().st_mode)
    except OSError:
        return 0
