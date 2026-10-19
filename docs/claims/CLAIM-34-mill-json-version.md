# Claim - every mill JSON return includes mill version

Status: **local WIP** folded on `claim/34-mill-name-get-put-gate` (dirty). Not committed. Not pushed.

## Lock

Every JSON return the mill-wall emits includes the mill version string under the field name **`mill`**.

## Version source

- Single source: `agent_coord.install.packver.package_version()` (checkout `pyproject.toml` wins, else installed dist metadata, else `0+local`).
- `agent_coord.__version__` mirrors that same call so import and wire agree.
- Today that resolves to **0.5.5**.

## Envelope (not lean payload)

| Wire | Shape |
|------|--------|
| `/ws` RPC reply | `{id, ok, result|error, mill}` |
| HTTP JSON (`_json`, join, errors) | top-level object gets `mill` |
| WS pushes (HINT / PING / DISCONNECTED) | outermost object gets `mill` |

Lean verb rows inside `result` (MAIL inbox rows, member lists, ...) are **not** rewritten. Version lives only on the envelope.

## Bare JSON array choice

Desk-acting verbs (inbox, member, ...) already return over `/ws` RPC; `mill_ws_call` unwraps `result` for the CLI, so stdout stays the lean payload.

If an HTTP path still emits a bare JSON **array** as the whole body, `_json` / `stamp_mill` wrap it as:

```json
{"result": [ ... ], "mill": "0.5.5"}
```

Join and error bodies are already objects, so they only gain `mill`. Wall `/api/*` objects likewise gain `mill` via the central `_json` helper. New verbs that go through `_json`, RPC reply helpers, or Hub push inherit the stamp automatically.

## Sample JSON

RPC ok:

```json
{"id": "r1", "ok": true, "result": [{"id": 7}], "mill": "0.5.5"}
```

PING push:

```json
{"type": "heartbeat", "id": 0, "hint": "PING", "mill": "0.5.5"}
```

HTTP error:

```json
{"error": "bad json", "mill": "0.5.5"}
```

## Files

- `agent_coord/server/mill_json.py` - `mill_version`, `stamp_mill`, `dumps_mill*`
- `agent_coord/__init__.py` - `__version__`
- `agent_coord/server/middleware.py` - `_json` stamps; bad-json uses `_json`
- `agent_coord/server/asgi.py` - RPC replies + ASGI 500 JSON stamp
- `agent_coord/server/push.py` - broadcast / kick / fanout stamp
- `tests/server/test_mill_json_version.py` - throwaway unit coverage
- `tests/server/test_ws_rpc.py`, `tests/server/test_ws_kick_replaced.py` - expect `mill`

## Evidence

- `pytest tests/server/test_mill_json_version.py tests/server/test_ws_rpc.py tests/server/test_ws_kick_replaced.py` (no live SQL) - 17 passed

## Out of scope

- Live SQL, docs/Gardener rewrite, commit/push, pack bump
