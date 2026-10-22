"""Build the pack twice from fresh clones and fail unless the bytes match.

  python tools/check_repro.py          two builds of HEAD must match
  python tools/check_repro.py dist     ...and match the wheel + sdist in dist/

Each build clones HEAD into its own temp dir under a different umask, a second
apart, dates it with SOURCE_DATE_EPOCH = the commit time, and runs
`python -m build --no-isolation` with this interpreter (the hash-locked build
env). Prints the sha256 of every artifact. Regression row F78.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UMASKS = (0o022, 0o002)


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _sums(dist: Path) -> dict[str, str]:
    out = {}
    for p in sorted(dist.iterdir()):
        if p.name.endswith((".whl", ".tar.gz")):
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _build(sha: str, epoch: str, umask: int, work: Path) -> dict[str, str]:
    src, out = work / "src", work / "out"
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    old = os.umask(umask)
    try:
        subprocess.run(["git", "-c", "init.defaultBranch=main", "clone", "-q", "--no-hardlinks", "--no-checkout", str(ROOT), str(src)], check=True)
        subprocess.run(["git", "checkout", "-q", "--detach", sha], cwd=src, check=True)
        done = subprocess.run(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(out)],
            cwd=src, env=env, capture_output=True, text=True,
        )
        if done.returncode:
            sys.stderr.write(done.stdout[-4000:] + done.stderr[-4000:])
            raise SystemExit(f"build failed (exit {done.returncode})")
    finally:
        os.umask(old)
    return _sums(out)


def main(argv: list[str]) -> int:
    sha = _git("rev-parse", "HEAD")
    epoch = _git("log", "-1", "--format=%ct", sha)
    runs: list[tuple[str, dict[str, str]]] = []
    if argv:
        runs.append((f"{argv[0]}/", _sums(Path(argv[0]))))
    for i, umask in enumerate(UMASKS, 1):
        if i > 1:
            time.sleep(1.1)
        with tempfile.TemporaryDirectory(prefix=f"repro{i}-") as tmp:
            runs.append((f"build {i} (umask {umask:03o})", _build(sha, epoch, umask, Path(tmp))))
    print(f"commit {sha[:12]} SOURCE_DATE_EPOCH={epoch}")
    for label, sums in runs:
        for name, digest in sums.items():
            print(f"  {digest}  {name}  [{label}]")
    first = runs[0][1]
    if len(first) != 2 or any(sums != first for _, sums in runs[1:]):
        print("FAIL: the pack is not reproducible (sha256 differs, or not one wheel + one sdist)")
        return 1
    print("OK: every build gave byte-identical wheel and sdist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
