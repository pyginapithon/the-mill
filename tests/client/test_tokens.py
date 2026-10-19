"""Owner-only session token file + mill send -/@file (no MySQL)."""
from __future__ import annotations

import io
import os
import stat
import sys
from pathlib import Path

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.__main__ import _resolve_send_body
from agent_coord.client.tokens import (
    apply_session_token_env,
    clear_session_token,
    drvfs_windows_path,
    mill_home,
    posix_mode,
    read_session_token,
    session_token_path,
    token_hash,
    write_session_token,
)


def test_session_token_path_shape(tmp_path: Path) -> None:
    p = session_token_path("build-presence", dest=tmp_path)
    assert p == tmp_path / "session" / "build-presence.token"
    assert mill_home(tmp_path) == tmp_path


def test_session_token_path_default_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AGENT_COORD_MILL_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    p = session_token_path("desk-a")
    assert p == tmp_path / ".mill" / "session" / "desk-a.token"


def test_mill_home_env_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path / "reloc"))
    assert mill_home() == tmp_path / "reloc"
    p = session_token_path("desk-a")
    assert p == tmp_path / "reloc" / "session" / "desk-a.token"


@pytest.mark.parametrize("bad", ["", "  ", "../x", "a/b", "has space", "x" * 65])
def test_session_token_path_rejects_bad_owner(bad: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        session_token_path(bad, dest=tmp_path)


def test_write_read_roundtrip_no_print(tmp_path: Path, capsys) -> None:
    secret = "unit-test-token-not-for-chat"
    path = write_session_token("desk-a", secret, dest=tmp_path)
    assert path in (tmp_path / "session" / "desk-a.token", tmp_path / "session" / "DESK_desk-a.token")
    assert read_session_token("desk-a", dest=tmp_path) == secret
    out = capsys.readouterr()
    assert secret not in out.out
    assert secret not in out.err
    dumped = path.read_text(encoding="utf-8")
    assert secret not in dumped or dumped.strip() == secret


def test_write_restricts_owner_only(tmp_path: Path) -> None:
    path = write_session_token("desk-a", "perm-token", dest=tmp_path)
    mode = path.stat().st_mode
    if sys.platform == "win32":
        assert path.is_file()
        # icacls: current user Full, inheritance removed
        import subprocess

        r = subprocess.run(
            ["icacls", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        user = os.environ.get("USERNAME") or ""
        assert user
        assert user in r.stdout
        assert "(F)" in r.stdout or "(R,W)" in r.stdout or "F" in r.stdout
        assert "Everyone:" not in r.stdout
    else:
        assert posix_mode(path) == 0o600
        assert posix_mode(path.parent) == 0o700


def test_write_empty_token_refuses(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_session_token("desk-a", "  ", dest=tmp_path)


def test_read_missing_empty(tmp_path: Path) -> None:
    assert read_session_token("no-such-desk", dest=tmp_path) == ""


def test_clear_session_token(tmp_path: Path) -> None:
    write_session_token("desk-a", "to-clear", dest=tmp_path)
    assert clear_session_token("desk-a", dest=tmp_path) is True
    assert read_session_token("desk-a", dest=tmp_path) == ""
    assert clear_session_token("desk-a", dest=tmp_path) is False
    assert clear_session_token("../x", dest=tmp_path) is False


def test_apply_env_is_noop_never_sets_shared_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("AGENT_COORD_TOKEN", raising=False)
    monkeypatch.setenv("AGENT_COORD_OWNER", "desk-a")
    write_session_token("desk-a", "from-file", dest=tmp_path)
    assert apply_session_token_env(dest=tmp_path) is False
    assert not os.environ.get("AGENT_COORD_TOKEN")



def test_apply_env_ignores_existing_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TOKEN", "already")
    write_session_token("desk-a", "from-file", dest=tmp_path)
    assert apply_session_token_env("desk-a", dest=tmp_path) is False
    assert os.environ.get("AGENT_COORD_TOKEN") == "already"



def test_apply_env_missing_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("AGENT_COORD_TOKEN", raising=False)
    assert apply_session_token_env("desk-a", dest=tmp_path) is False
    assert not (os.environ.get("AGENT_COORD_TOKEN") or "").strip()


def test_session_token_public_omits_token(tmp_path: Path) -> None:
    secret = "must-not-appear-in-json"
    path = write_session_token("desk-a", secret, dest=tmp_path)
    extra = {"token_file": str(path)}
    assert "token" not in extra
    assert extra["token_file"].endswith("desk-a.token")
    assert secret not in extra["token_file"]
    assert read_session_token("desk-a", dest=tmp_path) == secret


def test_resolve_send_body_inline() -> None:
    assert _resolve_send_body("  hello mill  ") == "hello mill"


def test_resolve_send_body_stdin(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("  from stdin  \n"))
    assert _resolve_send_body("-") == "from stdin"


def test_resolve_send_body_at_file(tmp_path: Path) -> None:
    p = tmp_path / "body.txt"
    p.write_text("  file body  \n", encoding="utf-8")
    assert _resolve_send_body("@" + str(p)) == "file body"


def test_resolve_send_body_strips_utf8_bom(tmp_path: Path) -> None:
    p = tmp_path / "bom.txt"
    p.write_bytes(b"\xef\xbb\xbfhello bom\n")
    assert _resolve_send_body("@" + str(p)) == "hello bom"


def test_resolve_send_body_keeps_4096() -> None:
    assert len(_resolve_send_body("x" * 4096)) == 4096
    with pytest.raises(CoordError, match="1..4096"):
        _resolve_send_body("x" * 4097)
    with pytest.raises(CoordError, match="1..4096"):
        _resolve_send_body("")
    with pytest.raises(CoordError, match="1..4096"):
        _resolve_send_body("   ")


def test_resolve_send_body_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CoordError, match="body file not found"):
        _resolve_send_body("@" + str(tmp_path / "nope.txt"))


def test_token_hash_unchanged() -> None:
    assert token_hash("abc") == __import__("hashlib").sha256(b"abc").hexdigest()


def test_drvfs_windows_path_wsl_mnt(tmp_path: Path) -> None:
    assert drvfs_windows_path("/mnt/d/foo") == "D:\\foo"
    assert drvfs_windows_path("/mnt/c/office/session/desk-a.token") == (
        "C:\\office\\session\\desk-a.token"
    )
    # real local path, any OS - not a WSL /mnt/<drive> string
    assert drvfs_windows_path(tmp_path.as_posix()) is None
    assert drvfs_windows_path(str(tmp_path)) is None

def test_resolve_send_body_tty_refuses(monkeypatch) -> None:
    class Tty:
        def isatty(self) -> bool:
            return True

        def read(self) -> str:
            raise AssertionError("must not read TTY")

    monkeypatch.setattr(sys, "stdin", Tty())
    with pytest.raises(CoordError, match="not a TTY"):
        _resolve_send_body("-")


def test_resolve_send_body_at_file_posix_rel(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("letter.txt").write_text("posix rel\n", encoding="utf-8")
    assert _resolve_send_body("@letter.txt") == "posix rel"
