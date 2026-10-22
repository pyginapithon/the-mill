"""todo lists short rows by default, paged; --full keeps today's reply (#295). Regression row F51 (todo-short-rows)."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_coord.__main__ import _build_parser, main
from agent_coord.client import http
from agent_coord.client.todo_rows import SHORT_KEYS, TODO_PAGE

GOLDEN = Path(__file__).with_name("todo_full_295.json")


def _card(i, roster="the-mill", tree=None, labels=None, volunteer=""):
    return {"project_id": roster, "need_id": f"need-{i}", "id": i, "status": "open",
            "doing": f"title {i}", "detail": "line\n" * 40, "volunteer": volunteer,
            "asker": "builder", "tree": tree, "labels": labels or []}


def board(n, roster="the-mill"):
    return [_card(i, roster=roster, tree=("a1b2c3d4e5" if i % 3 == 0 else None),
                  labels=(["ux"] if i % 2 else []), volunteer=("desk-a" if i % 5 == 0 else ""))
            for i in range(1, n + 1)]


def _wall(monkeypatch, rows, note="your rosters only (the-mill); mill todo --all lists every roster"):
    from agent_coord.server.mill_json import with_bytes

    def fake(args, body):
        reply, _ = with_bytes({"id": "r1", "ok": True, "result": list(rows), "sync": [], "mill": "t"})
        reply = dict(reply)
        reply["note"] = note
        return reply

    monkeypatch.setattr(http, "_todo_call", fake)
    monkeypatch.setattr("agent_coord.client.outbound.body_from_args", lambda args: {"verb": "todo"})


def _run(capsys, **kw):
    base = dict(cmd="todo", project="the-mill", need="", find="", group_by="", raw=False,
                said_command="", full=False, page=0)
    base.update(kw)
    rc = http.mill_http_from_args(SimpleNamespace(**base))
    out = capsys.readouterr().out.strip().splitlines()
    return rc, (out[-1] if out else ""), (json.loads(out[-1]) if out else None)


def _items(result):
    if isinstance(result, list):
        return result
    return [r for g in result["groups"] for r in g["items"]]


def test_default_rows_are_short(monkeypatch, capsys):
    _wall(monkeypatch, board(7))
    rc, line, row = _run(capsys)
    assert rc == 0
    rows = _items(row["result"])
    assert [r["id"] for r in rows] == [3, 6, 1, 2, 4, 5, 7]  # tree grouping kept
    for r in rows:
        assert set(r) <= set(SHORT_KEYS)
        assert "detail" not in r and "doing" not in r
        assert {"id", "need_id", "status", "volunteer"} <= set(r)
    assert next(r for r in rows if r["id"] == 5)["volunteer"] == "desk-a"
    assert row["bytes"] == len(line.encode("utf-8"))
    assert row["page"]["n"] == 1 and row["page"]["of"] == 1 and row["page"]["cards"] == 7
    assert "next" not in row["page"]
    assert "--full" in row["page"]["full"]


def test_one_roster_page_names_it_once(monkeypatch, capsys):
    _wall(monkeypatch, board(4))
    _, _, row = _run(capsys)
    assert all("project_id" not in r for r in _items(row["result"]))
    assert row["page"]["roster"] == "the-mill"


def test_mixed_rosters_keep_project_id(monkeypatch, capsys):
    _wall(monkeypatch, board(2) + board(2, roster="cold-test"))
    _, _, row = _run(capsys, project="")
    assert all("project_id" in r for r in _items(row["result"]))
    assert "roster" not in row["page"]


def test_empty_list(monkeypatch, capsys):
    _wall(monkeypatch, [])
    rc, _, row = _run(capsys)
    assert rc == 0 and row["result"] == []
    assert row["page"] == {"n": 1, "of": 1, "size": TODO_PAGE, "cards": 0, "full": row["page"]["full"]}


def test_empty_list_page_two_is_refused(monkeypatch, capsys):
    _wall(monkeypatch, [])
    with pytest.raises(Exception, match=r"todo --page 2: 0 card\(s\) make 1 page"):
        _run(capsys, page=2)


def test_exact_page_has_no_next(monkeypatch, capsys):
    _wall(monkeypatch, board(TODO_PAGE))
    _, _, row = _run(capsys)
    assert len(_items(row["result"])) == TODO_PAGE
    assert row["page"]["of"] == 1 and "next" not in row["page"]


def test_one_over_a_page_pages(monkeypatch, capsys):
    _wall(monkeypatch, board(TODO_PAGE + 1))
    _, _, row = _run(capsys)
    assert len(_items(row["result"])) == TODO_PAGE
    assert row["page"]["of"] == 2 and row["page"]["next"] == "--page 2"
    _, _, last = _run(capsys, page=2)
    assert [r["id"] for r in _items(last["result"])] == [TODO_PAGE + 1]
    assert last["page"]["n"] == 2 and "next" not in last["page"]


def test_pages_cover_every_card_once_in_wall_order(monkeypatch, capsys):
    n = TODO_PAGE * 2 + 15
    _wall(monkeypatch, board(n))
    seen = []
    for p in (1, 2, 3):
        _, _, row = _run(capsys, page=p, group_by="roster")
        seen += [r["id"] for r in _items(row["result"])]
    assert seen == list(range(1, n + 1))


def test_page_past_the_last_is_refused(monkeypatch, capsys):
    _wall(monkeypatch, board(TODO_PAGE + 1))
    with pytest.raises(Exception, match=r"todo --page 3: 51 card\(s\) make 2 page"):
        _run(capsys, page=3)


def test_full_is_todays_reply_byte_for_byte(monkeypatch, capsys):
    _wall(monkeypatch, board(TODO_PAGE + 20))
    rc, line, _ = _run(capsys, full=True)
    assert rc == 0
    assert line == GOLDEN.read_text(encoding="utf-8").strip()


def test_raw_is_unchanged(monkeypatch, capsys):
    rows = board(TODO_PAGE + 5)
    _wall(monkeypatch, rows)
    _, _, row = _run(capsys, raw=True)
    assert row == rows


def test_find_is_unchanged_by_the_short_default(monkeypatch, capsys):
    _wall(monkeypatch, board(TODO_PAGE + 5))
    _, _, row = _run(capsys, find="need-1")
    assert "page" not in row and all("snippet" in r for r in row["result"])


def test_peek_is_unchanged(monkeypatch, capsys):
    card = board(1)
    _wall(monkeypatch, card)
    _, _, row = _run(capsys, need="need-1")
    assert row["result"] == card and "page" not in row


@pytest.mark.parametrize("kw", [{"need": "need-1"}, {"find": "need"}, {"raw": True}])
def test_page_with_a_view_it_cannot_page_is_refused(monkeypatch, capsys, kw):
    _wall(monkeypatch, board(3))
    with pytest.raises(Exception, match="todo --page"):
        _run(capsys, page=2, **kw)


def test_parser_flags():
    p = _build_parser()
    a = p.parse_args(["todo", "the-mill", "--full"])
    assert a.full is True and a.page == 0
    assert p.parse_args(["todo", "--page", "3"]).page == 3


@pytest.mark.parametrize("argv", [["todo", "--page", "0"], ["todo", "--page", "-1"],
                                  ["todo", "--page", "x"], ["todo", "--full", "--page", "2"]])
def test_bad_page_flags_exit_2(argv, capsys):
    with pytest.raises(SystemExit) as e:
        _build_parser().parse_args(argv)
    assert e.value.code == 2


def test_help_names_the_default_and_full(capsys):
    with pytest.raises(SystemExit):
        main(["todo", "--help"])
    out = capsys.readouterr().out
    assert "--full" in out and "--page" in out and "short" in out
