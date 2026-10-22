"""F78 (sdist-repro): the in-tree backend makes both archives byte-identical.

Two archives with the same member bytes but different mtimes, owners, modes,
member order and gzip header time come out identical after the rewrite.
"""
from __future__ import annotations

import gzip
import importlib.util
import io
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mill_build", ROOT / "build_backend" / "mill_build.py")
mb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb)

EPOCH = 1792670000
FILES = {"pkg-1.0/b.txt": b"bee\n", "pkg-1.0/a.sh": b"#!/bin/sh\n", "pkg-1.0/sub/c.py": b"x = 1\n"}


def _sdist(path: Path, *, mtime: float, uid: int, uname: str, umask: int, order, gz_time: int) -> None:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name in order:
            info = tarfile.TarInfo(name)
            info.mtime, info.uid, info.gid, info.uname, info.gname = mtime, uid, uid, uname, uname
            if name.endswith("/"):
                info.type, info.mode, info.name = tarfile.DIRTYPE, 0o777 & ~umask, name.rstrip("/")
                tf.addfile(info)
                continue
            data = FILES[name]
            info.size = len(data)
            info.mode = (0o777 if name.endswith(".sh") else 0o666) & ~umask
            tf.addfile(info, io.BytesIO(data))
    with open(path, "wb") as out, gzip.GzipFile("pkg-1.0.tar", "wb", 9, out, mtime=gz_time) as gz:
        gz.write(raw.getvalue())


def _wheel(path: Path, *, date, umask: int) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("pkg/a.sh", "pkg/b.txt", "pkg-1.0.dist-info/RECORD"):
            info = zipfile.ZipInfo(name, date)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = (0o777 if name.endswith(".sh") else 0o666) & ~umask
            info.external_attr = (0o100000 | mode) << 16
            zf.writestr(info, b"data " + name.encode())


def test_sdist_rewrite_is_byte_identical_and_normalized(tmp_path):
    (tmp_path / "1").mkdir()
    (tmp_path / "2").mkdir()
    a, b = tmp_path / "1" / "pkg-1.0.tar.gz", tmp_path / "2" / "pkg-1.0.tar.gz"
    names = ["pkg-1.0/", "pkg-1.0/sub/", *FILES]
    _sdist(a, mtime=1792669964.56, uid=1000, uname="box", umask=0o022, order=names, gz_time=1792669964)
    _sdist(b, mtime=1792669999.12, uid=1001, uname="runner", umask=0o002, order=names[::-1], gz_time=1792670099)
    assert a.read_bytes() != b.read_bytes()
    mb._normalize_sdist(str(a), EPOCH)
    mb._normalize_sdist(str(b), EPOCH)
    assert a.read_bytes() == b.read_bytes()
    assert int.from_bytes(a.read_bytes()[4:8], "little") == EPOCH
    with tarfile.open(a) as tf:
        members = tf.getmembers()
        assert [m.name for m in members] == sorted(m.name for m in members)
        for m in members:
            assert (m.mtime, m.uid, m.gid, m.uname, m.gname) == (EPOCH, 0, 0, "", "")
            assert m.mode == (0o755 if m.isdir() or m.name.endswith(".sh") else 0o644), m.name
            if m.isfile():
                assert tf.extractfile(m).read() == FILES[m.name]


def test_wheel_rewrite_is_byte_identical_and_keeps_order(tmp_path):
    a, b = tmp_path / "a.whl", tmp_path / "b.whl"
    _wheel(a, date=(2026, 10, 22, 11, 41, 24), umask=0o022)
    _wheel(b, date=(2026, 10, 22, 11, 42, 0), umask=0o002)
    assert a.read_bytes() != b.read_bytes()
    mb._normalize_wheel(str(a), EPOCH)
    mb._normalize_wheel(str(b), EPOCH)
    assert a.read_bytes() == b.read_bytes()
    with zipfile.ZipFile(a) as zf:
        infos = zf.infolist()
        assert [i.filename for i in infos][-1] == "pkg-1.0.dist-info/RECORD"
        for i in infos:
            assert i.date_time == (2026, 10, 22, 11, 53, 20)
            assert i.external_attr >> 16 == (0o100755 if i.filename.endswith(".sh") else 0o100644)
            assert zf.read(i) == b"data " + i.filename.encode()


def test_without_epoch_member_times_are_kept(tmp_path):
    a = tmp_path / "a.tar.gz"
    _sdist(a, mtime=1792669964.56, uid=1000, uname="box", umask=0o022, order=list(FILES), gz_time=1)
    mb._normalize_sdist(str(a), None)
    with tarfile.open(a) as tf:
        assert {m.mtime for m in tf.getmembers()} == {1792669964}


def test_rewrite_is_idempotent(tmp_path):
    a = tmp_path / "pkg-1.0.tar.gz"
    w = tmp_path / "pkg-1.0-py3-none-any.whl"
    _sdist(a, mtime=1792669964.56, uid=1000, uname="box", umask=0o022, order=list(FILES), gz_time=1)
    _wheel(w, date=(2026, 10, 22, 11, 41, 24), umask=0o002)
    mb._normalize_sdist(str(a), EPOCH)
    mb._normalize_wheel(str(w), EPOCH)
    once = (a.read_bytes(), w.read_bytes())
    mb._normalize_sdist(str(a), EPOCH)
    mb._normalize_wheel(str(w), EPOCH)
    assert (a.read_bytes(), w.read_bytes()) == once


def test_link_member_fails_the_build(tmp_path):
    a = tmp_path / "pkg-1.0.tar.gz"
    with tarfile.open(a, "w:gz") as tf:
        info = tarfile.TarInfo("pkg-1.0/link")
        info.type, info.linkname = tarfile.SYMTYPE, "../../etc/passwd"
        tf.addfile(info)
    with pytest.raises(ValueError, match="not a regular file"):
        mb._normalize_sdist(str(a), EPOCH)
