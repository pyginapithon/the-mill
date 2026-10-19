# Claim - wire sync CLI envelope (cloud-mill #61)

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

need_id: `wire-sync-cli-envelope` (todo id 61). Claimed by DESK_builder.

## Lock (ACCEPT)

1. `mill connect` prints one JSON line: `{"kind":"sync","sync":[...],"mill":"<pack version>"}` - not bare `{'sync':[...]}` missing kind+mill.
2. Desk verb CLI prints ONE reply object with at least `result` + `sync` (oldest-first; empty sync ok). Default is the full host envelope (`ok` / `mill` / `id` / `result` / `sync`). Bare arrays blocked warm teach. Optional `mill --raw <verb>` restores the old lean unwrap.
3. Pack share includes `docs/protocol/sync.md` (skill already links it; 0.5.11 share was missing it).

Out of scope: multi-desk host active/Bearer (#9 sibling). Do not invent a mill sync verb.

## Files

- `agent_coord/client/ws.py` - connect on_frame prints kind+sync+mill via `json.dumps`; `mill_ws_call` returns full success envelope; failures raise `CoordError(..., envelope=msg)`
- `agent_coord/helpers/errors.py` - `CoordError.envelope`
- `agent_coord/__main__.py` - `_format_error` prefers full failure envelope and always includes `sync`; global `--raw`
- `agent_coord/client/http.py` - `_unwrap_cli_raw` + `mill_http_from_args` respects `--raw`
- `docs/protocol/sync.md` - "What the command prints" matches default full envelope + `--raw`
- `pyproject.toml` - `docs/protocol/sync.md` in `share/the-mill/docs/protocol`
- `agent_coord/server/mill_json.py` - docstring notes CLI default envelope
- `tests/client/test_wire_sync_cli_envelope.py` - focused unit coverage
- `docs/claims/CLAIM-wire-sync-cli-envelope.md` - this claim

## Evidence (path:lines)

- Connect stamp print: `agent_coord/client/ws.py:179-191` (`kind` / `sync` / `mill` JSON line)
- Verb success envelope: `agent_coord/client/ws.py:617-629` (return `dict(msg)` with list `sync`)
- Verb failure envelope: `agent_coord/client/ws.py:630-632` + `agent_coord/helpers/errors.py` + `agent_coord/__main__.py` `_format_error`
- CLI `--raw` unwrap: `agent_coord/client/http.py` `_unwrap_cli_raw` / `mill_http_from_args`
- Pack include: `pyproject.toml` `share/the-mill/docs/protocol` lists `docs/protocol/sync.md`
- Protocol: `docs/protocol/sync.md` mill connect + verb + print sections

## Live measure (checkout `python -m agent_coord`, office cloud-mill, DESK_builder sitting)

Connect first line after seat:

```json
{"kind": "sync", "sync": [...], "mill": "0.5.11"}
```

`mill member` (default):

```json
{"id": "...", "ok": true, "result": [...], "sync": [], "mill": "0.5.11"}
```

`mill --raw member`: bare result array (documented opt-out).

## Tests

```text
pytest tests/client/test_wire_sync_cli_envelope.py tests/server/test_mill_json_version.py -q
# 16 passed
```

## Out of scope / follow

- Push, pack bump / PyPI, multi-desk host active (#9)
