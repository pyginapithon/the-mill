# -*- coding: utf-8 -*-
"""join.doing on the wall matches the book stack: newest first, escaped separator."""
from __future__ import annotations

import json
import shutil
import subprocess

from agent_coord.server.records.doing_stack import push, split
from agent_coord.web.wall_logic.packs import wall_ui_root

BOOT = wall_ui_root() / "default" / "boot.js"


def _js_split(samples: list[str]) -> list[list[str]]:
    node = shutil.which("node")
    if not node:
        raise AssertionError("Node.js is not on PATH, so the doing stack cannot run.")
    src = BOOT.read_text(encoding="utf-8")
    start = src.index("function wallDoingUnescape(")
    end = src.index("function wallDoingBlock(")
    body = src[start:end]
    script = (
        "const fs = require('fs');\n"
        "const body = fs.readFileSync(process.argv[2], 'utf8');\n"
        "const samples = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));\n"
        "const api = new Function(body + '\\nreturn wallDoingSplit;')();\n"
        "process.stdout.write(JSON.stringify(samples.map(api)));\n"
    )
    # body is passed as a file so the shell never sees the escapes.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        js = tmp / "split.js"
        body_file = tmp / "body.js"
        data = tmp / "samples.json"
        js.write_text(script, encoding="utf-8", newline="\n")
        body_file.write_text(body, encoding="utf-8", newline="\n")
        data.write_text(json.dumps(samples), encoding="utf-8", newline="\n")
        proc = subprocess.run(
            [node, str(js), str(body_file), str(data)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    if proc.returncode != 0:
        raise AssertionError((proc.stderr or proc.stdout or "node failed")[-2000:])
    return json.loads(proc.stdout)


def test_wall_split_matches_the_book():
    samples = [
        "",
        "only",
        push("present", "wake"),
        push("present", r"a | b\c"),
        push(push("old", "mid"), "new"),
    ]
    got = _js_split(samples)
    assert got == [split(s) for s in samples]


def test_here_paints_the_newest_note():
    src = BOOT.read_text(encoding="utf-8")
    assert "function wallDoingFace(" in src
    assert "doingOlder: face.older" in src
    assert "wallDoingBlock(doingNow, doingOlder)" in src
    assert "wallDoingRow(doingNow, doingOlder)" in src
