# tools/

Human CLIs that are **not** mill-office. Mill stays office verbs (MAIL/TODO/connect).

## bin/

| Command | What |
| --- | --- |
| `git-changes` | Pretty file list / patch between two git revs (default: last version -> HEAD) |

### Run

From any checkout of this repo (or put `tools/bin` on PATH):

```bash
# Unix / macOS / WSL / Git Bash
./tools/bin/git-changes
./tools/bin/git-changes --from v0.4.12 --to HEAD
./tools/bin/git-changes --patch > since.patch
```

```bat
REM Windows (cmd / PowerShell)
tools\bin\git-changes.cmd
tools\bin\git-changes.cmd --pretty --no-color
python -m tools.git_changes --names
```

TTY -> pretty table. Pipe/redirect -> `--names` (no color). Override with `--pretty` / `--patch` / `--stat`.

## check_sql.py

Compare the pack's routines to the live book. Run it on the wall host. It reads mill config, skips `wipe.sql` and `tables.sql`, and prints names only. The match is case-sensitive.

```bash
python tools/check_sql.py
python tools/check_sql.py --sql path/to/agent_coord/server/sql
```

Exit 1 when a pack routine is missing. Extra live routines are listed and do not fail the check. It does not apply SQL.

## orphan_scan.py

Which `agent_coord` modules nothing imports. Use this before deleting a file that "looks unused."

```bash
python tools/orphan_scan.py
python tools/orphan_scan.py --root path/to/the-mill
```

One orphan per line: `module<TAB>repo-relative-path`. A count goes to stderr. Exit 0.

It starts from `pyproject.toml` console scripts (`mill`, `mill-mcp`), every `tests/` import, and `python -m agent_coord...` strings. Importing a package counts that package's `__init__.py` imports. `from . import name` counts the submodule. A file loaded by path (`spec_from_file_location`) counts too.

`web/wall_ui_save/` is a snapshot and is not scanned.

A module can be an orphan and still be a stub you meant to keep (`install/todo_diary.py` is the todo snapshot across a schema wipe; it is just not wired to a command). The scan does not decide keep or delete.

## probe_deleted_rows.py

Test-only. Makes a deleted todo row and a deleted score row live, on the calling desk's own `t-<8 hex>` fixture rows only, so the deleted state can be checked on events, activity between, and the Wall pill (#160). Run it as a child of the shell that started `mill connect`. Needs an office at 0.6.30 or later.

```bash
python tools/probe_deleted_rows.py run
python tools/probe_deleted_rows.py delete --type todo --id N
```

See [docs/dev/PROBE-DELETED-ROWS.md](../docs/dev/PROBE-DELETED-ROWS.md).
