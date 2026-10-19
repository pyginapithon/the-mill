"""Clean-venv install probe: pip install . then briefing + init (no session token).

Run: python tests/probe_install.py
Uses agent_coord_test. Writes config under a temp dir, not ~/.mill.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DB = "agent_coord_test"


def _run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def main() -> int:
    td = Path(tempfile.mkdtemp(prefix="mill-probe-"))
    vdir = td / "venv"
    cfg = td / "config.toml"
    print("venv", vdir)
    venv.create(vdir, with_pip=True)
    if sys.platform == "win32":
        exe = vdir / "Scripts" / "python.exe"
    else:
        exe = vdir / "bin" / "python"
    pip = _run([str(exe), "-m", "pip", "install", "--upgrade", "pip"])
    if pip.returncode != 0:
        print(pip.stdout)
        print(pip.stderr)
        return pip.returncode
    inst = _run([str(exe), "-m", "pip", "install", str(ROOT)])
    if inst.returncode != 0:
        print(inst.stdout)
        print(inst.stderr)
        return inst.returncode
    env = os.environ.copy()
    env["AGENT_COORD_CONFIG"] = str(cfg)
    env["AGENT_COORD_DATABASE"] = TEST_DB
    brief = _run([str(exe), "-m", "agent_coord", "briefing", "bootstrap"], env=env)
    if brief.returncode != 0 or "mill init" not in brief.stdout:
        print("briefing failed", brief.returncode, brief.stdout, brief.stderr)
        return 1
    init = _run(
        [
            str(exe),
            "-m",
            "agent_coord",
            "init",
            "--yes",
            "--database",
            TEST_DB,
            "--config",
            str(cfg),
        ],
        env=env,
    )
    if init.returncode != 0:
        print("init failed", init.stdout, init.stderr)
        err = (init.stderr or "") + (init.stdout or "")
        if "Can't connect to MySQL" in err or "2003" in err:
            print(
                "hint: 127.0.0.1 is *this* OS. WSL is not Windows. "
                "Same PC: WSL mirrored networking (~/.wslconfig networkingMode=mirrored) "
                "so localhost reaches Windows MySQL. Other machine: AGENT_COORD_HOST=<book host>. "
                "Do not bind MySQL to 0.0.0.0 on the public internet."
            )
        return init.returncode
    data = json.loads(init.stdout)
    if data.get("token"):
        print("FAIL: init minted a token", data)
        return 2
    if "token" in data:
        print("FAIL: init result has token key", data)
        return 2
    if not cfg.is_file() or "NOT a session token" not in cfg.read_text(encoding="utf-8"):
        print("FAIL: config missing disclaimer", cfg)
        return 3
    if sys.platform == "win32":
        cli = vdir / "Scripts" / "mill.exe"
    else:
        cli = vdir / "bin" / "mill"
    if not cli.is_file():
        print("FAIL: mill console script missing after pip install", cli)
        return 4
    mig = _run(
        [
            str(exe),
            "-c",
            "from pathlib import Path; import agent_coord; "
            "p=Path(agent_coord.__file__).resolve().parent/'server'/'sql'/'tables.sql'; "
            "print('yes' if p.is_file() else 'no')",
        ],
        env=env,
    )
    if mig.returncode != 0 or "yes" not in (mig.stdout or ""):
        print("FAIL: sql/tables.sql not packaged", mig.stdout, mig.stderr)
        return 5
    help_session = _run([str(exe), "-m", "agent_coord", "session", "--help"], env=env)
    if help_session.returncode != 0:
        print("FAIL: session --help", help_session.stdout, help_session.stderr)
        return 6
    via_script = _run([str(cli), "session", "--help"], env=env)
    if via_script.returncode != 0:
        print("FAIL: mill session not on PATH", via_script.stdout, via_script.stderr)
        return 6
    dest = td / "office"
    dest.mkdir()
    wall = _run(
        [str(exe), "-m", "agent_coord", "install", "wall", "--dest", str(dest)],
        env=env,
    )
    if wall.returncode != 0:
        print("install wall failed", wall.stdout, wall.stderr)
        return wall.returncode
    cloud = _run(
        [str(exe), "-m", "agent_coord", "install", "cloud", "--dest", str(dest)],
        env=env,
    )
    if cloud.returncode != 0:
        print("install cloud failed", cloud.stdout, cloud.stderr)
        return cloud.returncode
    print("probe ok", {"config": str(cfg), "schema_version": data.get("schema_version"), "dest": str(dest)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
