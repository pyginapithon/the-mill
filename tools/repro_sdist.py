"""Rewrite the sdist in DIR so the same commit always gives the same bytes.

setuptools dates sdist members by the checkout's file mtimes and the build
time (as PAX mtime records), stamps the gzip header with the build time, and
records the build user as owner. The wheel already honors SOURCE_DATE_EPOCH;
the sdist does not. This rewrites each DIR/*.tar.gz in place: the same
members in name order with the same contents, mtime = SOURCE_DATE_EPOCH,
owner 0/0 with no names, mode 0644 (0755 for directories and executables),
and a gzip header dated SOURCE_DATE_EPOCH with no file name. Only regular
files and directories are allowed. Running it twice changes nothing.

    SOURCE_DATE_EPOCH="$(git log -1 --format=%ct)" python tools/repro_sdist.py dist
"""
import gzip
import io
import os
import pathlib
import sys
import tarfile


def _epoch() -> int:
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if not raw.isdigit():
        sys.exit("repro_sdist: SOURCE_DATE_EPOCH must be set to a whole number of seconds")
    return int(raw)


def normalize(path: pathlib.Path, epoch: int) -> None:
    with tarfile.open(path, "r:gz") as src:
        members = []
        for m in src.getmembers():
            if not (m.isfile() or m.isdir()):
                sys.exit(f"repro_sdist: {path.name}: {m.name} is not a file or directory")
            data = src.extractfile(m).read() if m.isfile() else None
            members.append((m, data))
    members.sort(key=lambda md: md[0].name)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as dst:
        for m, data in members:
            info = tarfile.TarInfo(m.name)
            info.type = m.type
            info.mtime = epoch
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o755 if (m.isdir() or m.mode & 0o111) else 0o644
            info.size = len(data) if data is not None else 0
            dst.addfile(info, io.BytesIO(data) if data is not None else None)
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, compresslevel=9, mtime=epoch) as gz:
        gz.write(raw.getvalue())
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(out.getvalue())
    os.replace(tmp, path)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.exit("usage: repro_sdist.py DIR")
    epoch = _epoch()
    sdists = sorted(pathlib.Path(argv[0]).glob("*.tar.gz"))
    if not sdists:
        sys.exit(f"repro_sdist: no *.tar.gz in {argv[0]}")
    for p in sdists:
        normalize(p, epoch)
        print(f"repro_sdist: {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
