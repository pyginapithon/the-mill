# Validator live suite (`mill_live`)

Probes against a live mill-wall: HTTPS Wall stamps + `/ws` host perf.

## Run

```text
MILL_LIVE=1 py -3 -m pytest tests/validator -m mill_live -q
```

Windows (cmd):

```text
set MILL_LIVE=1
py -3 -m pytest tests/validator -m mill_live -q
```

Without `MILL_LIVE=1` the whole package skips (safe for default CI / local pytest).

## Required env

| Var | Default | Notes |
|-----|---------|-------|
| `MILL_LIVE` | unset | Must be `1` or package skips |
| `MILL_LIVE_URL` | `https://192.0.2.10` | Wall base URL (https) |
| `MILL_LIVE_CA` | unset | CA file path; else TLS verify off |
| `MILL_LIVE_DESK` | unset | Role desk for `/ws` (e.g. `validator`) |
| `MILL_LIVE_TOKEN` | unset | Bearer for that desk; WS tests skip if missing |

HTTPS Wall probes (`test_wall_https_live.py`) need only `MILL_LIVE=1` (and reachability).

`/ws` perf probes need desk + token. Join path (do not commit secrets):

1. Use a **role** desk (not a personal name): `mill join` / office invite for that desk.
2. Read the session token from the mill home session file for that desk (see `agent_coord.client.tokens.read_session_token`).
3. Export `MILL_LIVE_DESK` + `MILL_LIVE_TOKEN` for the pytest process only.

Also sets `AGENT_COORD_MILL_URL` from `MILL_LIVE_URL` so client helpers (`mill_ws_url`) resolve wss correctly.

## Markers

Uses pytest marker `mill_live` (already registered in `pyproject.toml`).
