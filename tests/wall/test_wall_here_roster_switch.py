# -*- coding: utf-8 -*-
"""#718: on a roster switch CONNECTED shows the hourglass until the new roster's desks paint.

Runs the real resetFloorBook(), wallHereHourglass(), wallHereAgentsRead() and
wallHereNeedsPaint() from boot.js in Node against a stub #here, so the test checks
behavior, not source text.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from agent_coord.web.wall_logic.packs import wall_ui_root

BOOT = wall_ui_root() / "default" / "boot.js"

HARNESS = r"""
const fs = require('fs');
const body = fs.readFileSync(process.argv[2], 'utf8');
const here = { innerHTML: '<table><tr><td>installer</td><td>working</td></tr></table>' };
const stubs = {
  document: { getElementById: (id) => (id === 'here' ? here : null) },
  window: {},
  wallResetStripReady: () => {},
  wallIsLoadingEl: (el) => /data-wall-loading/.test(el.innerHTML),
  wallLoadingHtml: (lbl) => '<div class="wall-loading" data-wall-loading="1">' + lbl + '</div>',
  _railPickApplied: '', _floorHash: '',
};
const names = Object.keys(stubs);
const api = new Function(...names, body + `
return {
  reset: resetFloorBook, needs: wallHereNeedsPaint, read: wallHereAgentsRead,
  setPick: (p) => { _hereDomPick = p; }, pick: () => _hereDomPick,
  setBook: (b) => { _floorBook = b; },
};`)(...names.map((n) => stubs[n]));
const out = {};
// Office painted #here.
api.setPick('project:Office');
out.officeRepaint = api.needs('project:Office', { agents: [{ owner: 'installer', alive: true }] });
// Switch to the-mill.
api.reset();
out.afterReset = { html: here.innerHTML, pick: api.pick() };
// A TODO poll for the new roster: the cut view has agents [] but the book never read them.
api.setBook({ needs: [], trees: [] });
out.todoPoll = { read: api.read({ agents: [] }), needs: api.needs('project:the-mill', { agents: [] }) };
// The agents part lands and the roster is empty: paint the honest empty.
api.setBook({ agents: [] });
out.emptyRoster = api.needs('project:the-mill', { agents: [] });
// Once painted for this roster, a same-roster poll does not force a repaint.
api.setPick('project:the-mill');
out.samePick = api.needs('project:the-mill', { agents: [] });
// No book yet: a slice speaks for itself through parts.
api.setBook(null);
out.sliceTodos = api.read({ parts: ['todos'], agents: [] });
out.sliceAgents = api.read({ parts: ['agents'], agents: [] });
process.stdout.write(JSON.stringify(out));
"""


def _run() -> dict:
    node = shutil.which("node")
    if not node:
        raise AssertionError("Node.js is not on PATH, so the CONNECTED pane cannot run.")
    src = BOOT.read_text(encoding="utf-8")
    block = src[src.index("let _hereDomPick"):src.index("function bookIsProject(")]
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        js, body = tmp / "here.js", tmp / "body.js"
        js.write_text(HARNESS, encoding="utf-8", newline="\n")
        body.write_text(block, encoding="utf-8", newline="\n")
        proc = subprocess.run([node, str(js), str(body)], capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise AssertionError((proc.stderr or proc.stdout or "node failed")[-2000:])
    return json.loads(proc.stdout)


def test_switch_drops_last_roster_desks_for_the_hourglass():
    out = _run()
    assert out["officeRepaint"] is False
    assert "installer" not in out["afterReset"]["html"]
    assert "data-wall-loading" in out["afterReset"]["html"]
    assert out["afterReset"]["pick"] == ""


def test_hourglass_stays_until_desks_are_read():
    out = _run()
    assert out["todoPoll"] == {"read": False, "needs": False}


def test_empty_new_roster_paints_the_honest_empty():
    out = _run()
    assert out["emptyRoster"] is True
    assert out["samePick"] is False


def test_slice_without_book_reads_parts():
    out = _run()
    assert out["sliceTodos"] is False
    assert out["sliceAgents"] is True
