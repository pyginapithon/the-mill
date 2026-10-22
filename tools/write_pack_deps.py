"""Write pack-deps.txt and pack-floors.txt from pyproject.toml project.dependencies.

pack-floors.txt pins each runtime dep at its >= floor (extras dropped): the
oldest version a user's install may keep. CI audits it with
`pip-audit --disable-pip --no-deps`, so a floor with a known advisory fails.
"""
import pathlib
import re
import sys
import tomllib

FLOOR_RE = re.compile(r"^([A-Za-z0-9._-]+)(?:\[[\w,-]+\])?>=([0-9][\w.]*)$")

deps = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
floors = []
for d in deps:
    m = FLOOR_RE.match(d)
    if not m:
        sys.exit(f"write_pack_deps: dependency without a plain >= floor: {d}")
    floors.append(f"{m.group(1)}=={m.group(2)}")
pathlib.Path("pack-deps.txt").write_text("\n".join(deps) + "\n", encoding="utf-8")
pathlib.Path("pack-floors.txt").write_text("\n".join(floors) + "\n", encoding="utf-8")
