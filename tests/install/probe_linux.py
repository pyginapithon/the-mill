"""Linux mill-desk probe: Python version, then clean venv pip install + briefing.

Run on Linux (or WSL): python3 tests/probe_linux.py
Exit 4 if Python is below 3.10 (Ubuntu 20.04 system python3.8 is this miss).
Does not start mysqld or the wall.

WSL: 127.0.0.1 is Linux, not Windows MySQL. Use mirrored networking
(~/.wslconfig networkingMode=mirrored) or AGENT_COORD_HOST=<windows host>.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN = (3, 10)


def main() -> int:
    ver = sys.version.split()[0]
    print("linux probe", sys.platform, ver)
    if sys.version_info < MIN:
        print(
            "FAIL: mill desk needs Python "
            f"{MIN[0]}.{MIN[1]}+; this interpreter is {ver}. "
            "Ubuntu 22.04 / Amazon Linux 2023. Ubuntu 20.04 default is below the mill."
        )
        return 4
    sys.path.insert(0, str(ROOT / "tests"))
    import probe_install

    return probe_install.main()


if __name__ == "__main__":
    raise SystemExit(main())
