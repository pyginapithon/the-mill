"""Local pack: build + hygiene. Optional install (not PyPI) + mill MAIL.

For people who change mill. App users still `pip install the-mill`.

  python tools/pack_local.py
  python tools/pack_local.py --install
  python tools/pack_local.py --install --notify

Never uploads to PyPI. Never `pip install .`.
`--install` runs pip from a non-git cwd so the checkout is not on sys.path.
`--notify` mails build-validator with mill send desk ... --body-file (office dogfood;
skipped if mill is missing).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    if not (here / "pyproject.toml").is_file():
        raise SystemExit("pack_local: run from a the-mill checkout (missing pyproject.toml)")
    return here


def redacted(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + path.resolve().relative_to(home).as_posix()
    except ValueError:
        return path.name


def git_sha(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return (out.stdout or "").strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def drop_pycache(root: Path) -> None:
    skip = {".git", "dist", "build", "tmp", ".pytest_cache"}
    for p in root.rglob("__pycache__"):
        if any(part in skip for part in p.parts):
            continue
        shutil.rmtree(p, ignore_errors=True)


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def newest(dist: Path, pattern: str) -> Path:
    hits = sorted(dist.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"pack_local: no {pattern} in dist/")
    return hits[-1]


def notify_body(*, sha: str, version: str, wheel: Path) -> str:
    return (
        f"LOCAL PACK ready (not PyPI). sha {sha} the-mill {version} "
        f"wheel {wheel.name}. Re-measure dry-run only; no --apply wipe. "
        f"This is build-validator (not Bot Validator). Prefer mill."
    )


def notify_cmd(mill: str, body_file: Path) -> list[str]:
    """The current send form: one desk by name, body from a UTF-8 file."""
    return [mill, "send", "desk", "build-validator", "--roster", "the-mill", "--body-file", str(body_file)]


def notify_build_validator(*, sha: str, version: str, wheel: Path) -> None:
    mill = shutil.which("mill")
    if not mill:
        print("notify: mill not on PATH; skipped")
        return
    env = os.environ.copy()
    env.setdefault("AGENT_COORD_OWNER", "builder")
    with tempfile.TemporaryDirectory() as tmp:
        body_file = Path(tmp) / "local-pack.txt"
        body_file.write_text(notify_body(sha=sha, version=version, wheel=wheel), encoding="utf-8")
        print("+ mill send desk build-validator --roster the-mill --body-file <local-pack note>")
        subprocess.run(notify_cmd(mill, body_file), cwd=str(Path.home()), check=False, env=env)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--install", action="store_true", help="pip install the wheel from a non-git cwd")
    p.add_argument("--notify", action="store_true", help="mill MAIL build-validator after a clean pack")
    args = p.parse_args(argv)

    if args.notify and not args.install:
        print("pack_local: --notify is meant with --install (still mailing after pack-only if you insist)")

    root = repo_root()
    os.chdir(root)
    drop_pycache(root)
    run([sys.executable, "-m", "pip", "install", "-q", "build"], cwd=root)
    run([sys.executable, "-m", "build"], cwd=root)
    run([sys.executable, "tools/check_pack.py", "dist"], cwd=root)

    dist = root / "dist"
    whl = newest(dist, "*.whl")
    sdist = newest(dist, "*.tar.gz")
    sha = git_sha(root)
    version = "unknown"
    for line in (root / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            version = line.split("=", 1)[1].strip().strip('"')
            break
    print(f"sha {sha} version {version}")
    print(f"wheel {whl.name}")
    print(f"sdist {sdist.name}")

    if args.install:
        home = Path.home()
        if home.resolve() == root.resolve():
            raise SystemExit("pack_local: refuse pip install from repo as cwd")
        run(
            [sys.executable, "-m", "pip", "install", "--force-reinstall", str(whl.resolve())],
            cwd=home,
        )
        print("installed wheel into this Python (not PyPI). revert: python -m pip install the-mill==<pypi>")

    if args.notify:
        notify_build_validator(sha=sha, version=version, wheel=whl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
