"""PEP 517 backend: setuptools, then byte-reproducible archives.

setuptools dates wheel members by SOURCE_DATE_EPOCH but keeps each file's
checkout mode (umask), and its sdist keeps checkout mtimes, the builder's
uid/gid and names, and a gzip header stamped with the build time. This
rewrites both archives in place: members sorted by name, regular files 0644
(0755 if any execute bit was set), directories 0755, owner 0/0 with no names,
every mtime and the gzip header (no file name) set to SOURCE_DATE_EPOCH (the
commit time in CI). Member bytes are unchanged, so RECORD stays valid; the
wheel keeps its member order. A link or other special sdist member fails the
build. A second rewrite changes nothing. Regression row F78.
"""

from __future__ import annotations

import gzip
import io
import os
import tarfile
import time
import zipfile

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # noqa: F401,F403  (the rest of the PEP 517 hooks)

_ZIP_EPOCH = 315532800  # 1980-01-01, the earliest time a zip member can hold


def _epoch() -> int | None:
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    return int(raw) if raw else None


def _mode(mode: int, is_dir: bool) -> int:
    if is_dir or mode & 0o111:
        return 0o755
    return 0o644


def _normalize_sdist(path: str, epoch: int | None) -> None:
    with tarfile.open(path, "r:gz") as src:
        members = sorted(src.getmembers(), key=lambda m: m.name)
        for m in members:
            if not (m.isfile() or m.isdir()):
                raise ValueError(f"sdist member {m.name} is not a regular file or directory")
        blobs = {m.name: src.extractfile(m).read() for m in members if m.isfile()}
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as dst:
        for m in members:
            m.mtime = epoch if epoch is not None else int(m.mtime)
            m.mode = _mode(m.mode, m.isdir())
            m.uid = m.gid = 0
            m.uname = m.gname = ""
            m.pax_headers = {}
            data = blobs.get(m.name)
            dst.addfile(m, io.BytesIO(data) if data is not None else None)
    stamp = epoch if epoch is not None else int(time.time())
    with open(path, "wb") as out:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=out,
            compresslevel=9,
            mtime=stamp,
        ) as gz:
            gz.write(raw.getvalue())


def _normalize_wheel(path: str, epoch: int | None) -> None:
    with zipfile.ZipFile(path) as src:
        infos = src.infolist()
        blobs = [(i, src.read(i)) for i in infos]
    stamp = None
    if epoch is not None:
        stamp = time.gmtime(max(epoch, _ZIP_EPOCH))[:6]
    with zipfile.ZipFile(path, "w") as dst:
        for old, data in blobs:
            is_dir = old.filename.endswith("/")
            info = zipfile.ZipInfo(old.filename, stamp or old.date_time)
            info.compress_type = old.compress_type
            info.create_system = 3
            info.external_attr = (_mode(old.external_attr >> 16, is_dir) | (0o040000 if is_dir else 0o100000)) << 16
            dst.writestr(info, data)


def build_sdist(sdist_directory, config_settings=None):
    name = _orig.build_sdist(sdist_directory, config_settings)
    _normalize_sdist(os.path.join(sdist_directory, name), _epoch())
    return name


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    name = _orig.build_wheel(wheel_directory, config_settings, metadata_directory)
    _normalize_wheel(os.path.join(wheel_directory, name), _epoch())
    return name
