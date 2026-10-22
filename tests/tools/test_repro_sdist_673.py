"""#673: the release sdist is byte-reproducible (F78).

setuptools dates sdist members by checkout mtimes and build time and stamps
the gzip header, so two builds of one commit differed. tools/repro_sdist.py
rewrites the sdist with fixed times and owner; ci.yml build_pack runs it and
builds a second time to compare sha256.
"""
import gzip
import hashlib
import io
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "repro_sdist.py"
CI = ROOT / ".github" / "workflows" / "ci.yml"
EPOCH = 1792669285
FILES = {
    "the_mill-1.0/PKG-INFO": b"Metadata-Version: 2.4\n",
    "the_mill-1.0/agent_coord/__init__.py": b"x = 1\n",
    "the_mill-1.0/scripts/run.sh": b"#!/bin/sh\n",
}


def _sdist(path: pathlib.Path, mtime: float, owner: str, reverse: bool) -> None:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tf:
        names = ["the_mill-1.0", "the_mill-1.0/agent_coord", *FILES]
        for name in sorted(names, reverse=reverse):
            info = tarfile.TarInfo(name)
            info.mtime, info.uid, info.gid, info.uname, info.gname = mtime, 1000, 1000, owner, owner
            if name in FILES:
                info.size = len(FILES[name])
                info.mode = 0o775 if name.endswith(".sh") else 0o664
                tf.addfile(info, io.BytesIO(FILES[name]))
            else:
                info.type, info.mode = tarfile.DIRTYPE, 0o775
                tf.addfile(info)
    with gzip.GzipFile(filename=path.name, mode="wb", fileobj=open(path, "wb"), mtime=int(mtime)) as gz:
        gz.write(raw.getvalue())


def _run(dist: pathlib.Path, epoch: int | None = EPOCH) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "SOURCE_DATE_EPOCH"}
    if epoch is not None:
        env["SOURCE_DATE_EPOCH"] = str(epoch)
    return subprocess.run([sys.executable, str(TOOL), str(dist)], env=env, capture_output=True, text=True)


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_two_builds_differ_only_in_time_and_owner_then_match(tmp_path: pathlib.Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    _sdist(a / "the_mill-1.0.tar.gz", time.time() - 100.25, "box", reverse=False)
    _sdist(b / "the_mill-1.0.tar.gz", time.time(), "runner", reverse=True)
    assert _sha(a / "the_mill-1.0.tar.gz") != _sha(b / "the_mill-1.0.tar.gz")
    for d in (a, b):
        r = _run(d)
        assert r.returncode == 0, r.stderr
    assert _sha(a / "the_mill-1.0.tar.gz") == _sha(b / "the_mill-1.0.tar.gz")


def test_members_contents_and_header_are_fixed(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "the_mill-1.0.tar.gz"
    _sdist(p, time.time() + 0.5, "box", reverse=True)
    assert _run(tmp_path).returncode == 0
    raw = p.read_bytes()
    assert raw[3] & 0x08 == 0, "gzip header still carries a file name"
    assert int.from_bytes(raw[4:8], "little") == EPOCH
    with tarfile.open(p, "r:gz") as tf:
        ms = tf.getmembers()
        assert [m.name for m in ms] == sorted(m.name for m in ms)
        for m in ms:
            assert (m.mtime, m.uid, m.gid, m.uname, m.gname) == (EPOCH, 0, 0, "", ""), m.name
            assert "mtime" not in m.pax_headers, m.name
            want = 0o755 if m.isdir() or m.name.endswith(".sh") else 0o644
            assert m.mode == want, (m.name, oct(m.mode))
            if m.isfile():
                assert tf.extractfile(m).read() == FILES[m.name]
        assert {m.name for m in ms if m.isfile()} == set(FILES)


def test_idempotent(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "the_mill-1.0.tar.gz"
    _sdist(p, time.time(), "box", reverse=False)
    assert _run(tmp_path).returncode == 0
    once = _sha(p)
    assert _run(tmp_path).returncode == 0
    assert _sha(p) == once


def test_refuses_without_epoch_or_sdist(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "the_mill-1.0.tar.gz"
    _sdist(p, time.time(), "box", reverse=False)
    before = _sha(p)
    r = _run(tmp_path, epoch=None)
    assert r.returncode != 0 and "SOURCE_DATE_EPOCH" in r.stderr
    assert _sha(p) == before
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _run(empty)
    assert r.returncode != 0 and "no *.tar.gz" in r.stderr


def test_refuses_links(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "the_mill-1.0.tar.gz"
    with tarfile.open(p, "w:gz") as tf:
        info = tarfile.TarInfo("the_mill-1.0/link")
        info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
        tf.addfile(info)
    r = _run(tmp_path)
    assert r.returncode != 0 and "not a file or directory" in r.stderr


def _job(text: str, name: str) -> str:
    body = text.split(f"\n  {name}:\n", 1)[1]
    nxt = re.search(r"\n  [a-z_]+:\n", body)
    return body[: nxt.start()] if nxt else body


def test_build_pack_normalizes_then_builds_twice_and_compares() -> None:
    job = _job(CI.read_text(encoding="utf-8"), "build_pack")
    first = job.index("python -m build --no-isolation\n")
    norm = job.index("python tools/repro_sdist.py dist\n")
    upload = job.index("actions/upload-artifact@")
    assert first < norm < upload, job
    second = job[job.index("Build again and compare sha256"):upload]
    assert "git worktree add" in second and "--outdir" in second, second
    assert 'python tools/repro_sdist.py "$RUNNER_TEMP/dist2"' in second, second
    assert "sha256sum" in second and re.search(r"^ +diff ", second, re.M), second
    assert second.count("SOURCE_DATE_EPOCH=\"$(git log -1 --format=%ct)\"") == 1, second
