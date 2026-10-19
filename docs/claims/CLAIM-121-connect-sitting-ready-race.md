# Claim - #121 connect sitting-ready race (GO A)

Status: **patch for tui** against `d184e44` / 0.6.22. Not bumped. Not packed.

## Lock (GO A)

On the **exact** error `no sitting mill connect for this process; mill connect DESK first`
(`SESSION_WS_BRIDGE_REQUIRED`): **one** short wait, **one** auto-retry, then fail closed.
Other errors are not retried. Volunteer field unchanged. JOIN one-liner docs wait until
after this ships.

## Delay

`SITTING_BRIDGE_RETRY_WAIT_S = 0.5` in `agent_coord/client/ws.py`.

- Sync frames can print from `_sit_session` **before** `write_rpc_bridge` finishes (bridge
  thread binds, then file write). millq / verbs that key off `"kind": "sync"` can race that window.
- 0.5s is longer than the usual port-bind poll (0.02s steps, up to ~1s worst case is rare)
  and far shorter than reconnect backoff (3s). Fixed; no backoff essay.

## What landed

1. **`mill_ws_call`** - catch exact sitting-miss, `time.sleep(0.5)`, call once more.
2. **`mill_http_call`** - when `resolve_desk_owner` is empty, same wait then re-resolve before
   raising (CLI verbs hit this before `mill_ws_call`).
3. **Tests** - first miss then success; permanent miss after one retry; other errors not retried.

## Out of scope

- Version bump / Shipper / PyPI / aws install
- JOIN.md one-liner (after retry ships)
- #108 bearer lookup
