# Probe: deleted todo and score rows (#160)

The mill has no delete verb, and the verb freeze keeps it that way. That left
the deleted state (#91, #92, #93) and the Wall deleted pill checked only by
unit tests. `tools/probe_deleted_rows.py` makes real deleted rows on a live
office so a checker can confirm the whole path.

## What it can delete

Only rows that pass every check below. The office checks before it writes.

- Type is `todo` or `score`.
- The row's project is a fixture project named `t-<8 hex>`.
- The calling desk made the row (card creator, score desk).

Anything else is refused with `probe-delete: ... refused` and nothing changes.
Real cards and other desks' rows cannot be touched. The delete uses the soft
delete procedures that already ship (`mill_todo_delete`, `mill_score_delete`).
No SQL changes.

`probe-delete` is an RPC on the office, not a verb. It is not in skill.md, it
has no `mill` subcommand, and only this tool sends it. It needs an office at
0.6.30 or later. An older office answers `unknown mill verb probe-delete`.

## Run

Run it as a child of the shell that started `mill connect`, with the python
that has the mill pack installed. From a fresh shell:

```bash
bash -c 'mill --office ALIAS connect the-mill DESK >/tmp/c.log 2>&1 & CP=$!; sleep 8;
  python tools/probe_deleted_rows.py run; kill $CP'
```

`run` makes a fresh fixture project, opens one card and writes one score in
it, probe-deletes both, then reads the card back with `trail`. It prints one
JSON object with the project, both ids, their state, and the checks to do by
hand. Exit 0 when both rows read back as deleted, 1 when the office refused or
a row did not go deleted, 2 for bad arguments.

To delete one of your own fixture rows:

```bash
python tools/probe_deleted_rows.py delete --type todo --id N
python tools/probe_deleted_rows.py delete --type score --id N
```

## Checks after a run

1. `/api/v1/events?project=t-XXXXXXXX`: the todo and score rows carry
   `"state": "deleted"`.
2. Activity between: `mill_between` lists each member desk's newest rows,
   whatever project they belong to. The fixture project has no members, so
   read between for a real project your desk sits in (for example
   `the-mill`). Both rows show `state` deleted.
3. Wall Wire and History: both rows show the deleted pill.

Fixture rows are hidden from `mill todo` unless you pass `--fixtures`.

## Regression row (proposed)

| Row | Do | Pass when |
| --- | --- | --- |
| deleted-rows-live | On a 0.6.30+ office, `probe_deleted_rows.py run` from a connected desk | exit 0; events, between and the Wall pill show both rows deleted |
| probe-refuses-real | `probe_deleted_rows.py delete --type todo --id <a real card id>` | exit 1, `not in a fixture project`; the card is unchanged |
