# Claim - mill verbs JSON response shape audit

Status: **Audit Complete** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

Parent lock (CLAIM-34): every mill JSON return includes pack version under field **`mill`**.

## Scope

Census of every WALL mill verb + wire envelopes (WS RPC, HTTP join, JSON pushes).
No new CLI verbs. No wall_ui. No pack/push. Dirty WIP from other agents left untouched.

## Wire envelopes (locked)

| Channel | Ok shape | Error shape | `mill` |
|---------|----------|-------------|--------|
| `/ws` RPC reply | `{id, ok:true, result, mill}` | `{id, ok:false, error, mill}` | via `stamp_mill` in `asgi._ws_handle_client_text` |
| HTTP mill (`_json`) incl. join | top-level object + `mill` (bare list -> `{result, mill}`) | `{error, mill}` (HTTP 400/500; **no** `ok` key) | via `middleware._json` -> `dumps_mill_bytes` |
| WS pushes (HINT / PING / DISCONNECTED) | outermost object + `mill` | n/a | `push.Hub._broadcast` / `_kick_replaced` / `fanout` |

Lean rows inside `result` are **not** rewritten (CLAIM-34).

Version source: `agent_coord.install.packver.package_version()` -> field name **`mill`** (`mill_json.py`). Tip pack resolves **0.5.8**.

## Verb census

Registry: `agent_coord.client.outbound.WALL` (40 verbs) + `rpc.HANDLERS`.
Dispatch: `rpc.dispatch` (HTTP; non-join refused to WS-only) / `rpc.dispatch_ws` (sitting `/ws`).

| Verb | Handler | Ok `result` keys (lean) | Hard error | Soft `ok` in result | Envelope `mill` |
|------|---------|-------------------------|------------|---------------------|-----------------|
| join | `_h_here` / `_issue_here` | `group_id, owner, role, doing, token[, desk_id]` | CoordError | - | Y (HTTP `_json`) |

| session | `_h_session` | list of `{project_id, owner, doing, heartbeat, alive}` | - | - | Y |
| heartbeat | `_h_heartbeat` | activity rows (list) | - | - | Y |
| doing | `_h_doing` | `ok, doing, owner, id` | - | - | Y |
| inbox | `_h_inbox` | list of public MAIL rows | CoordError | - | Y |
| send | `_h_send` | public MAIL (+ optional `room`, `warnings`) | CoordError | - | Y |
| reply | `_h_reply` | send shape + `replied_to` | CoordError | - | Y |
| mail-thread | `_h_mail_thread` | chain object (+ `thread=1` when TREE) | CoordError | - | Y |
| todo | `_h_todo` | list `{project_id, need_id, id, status, doing, detail, progress, volunteer, asker[, nest]}` | - | - | Y |
| open | `_h_open` | `project_id, need_id, id, status, doing, detail` | - | - | Y |
| claim | `_h_claim` | `ok, need_id, id, status, volunteer` | CoordError | - | Y |
| assign | `_h_assign` | `ok, need_id, id, status, volunteer` | CoordError | - | Y |
| note | `_h_note` | `need_id, id, detail` | CoordError | - | Y |
| pass | `_h_pass` | `ok, need, status, id` (or soft fail) | CoordError (who-may) | **Y** missing need -> `{ok:false, need}` under envelope `ok:true` | Y |
| unclaim / yield | `_h_yield` | `ok, need, status` | CoordError (who-may) | **Y** missing need -> `ok:false` | Y |
| unpark | `_h_unpark` | `ok, need, status` | CoordError (no TREE parent) | **Y** missing need -> `ok:false` | Y |
| hold | `_h_hold` | `ok, resource, id, owner` | - | **Y** contended -> `ok:false` | Y |
| drop | `_h_drop` | `ok, resource, id\|owner` | - | **Y** | Y |
| score | `_h_score` | score rows (list) | - | - | Y |
| attach / move / prune / detach | tree handlers | tree rows (list) | - | - | Y |
| label-add / label-remove | `_h_label` | label row / list | CoordError | - | Y |
| label | `_h_label_name` | catalog rows | - | - | Y |
| member / member-add / member-remove | `_h_member` | member rows | CoordError | - | Y |
| rename / retire / group / role / reclaim | catalog/name | rows | CoordError (rename/retire own) | - | Y |
| reset | `_h_reset` | `{ok, reset}` or prune list | CoordError | - | Y |
| watcher | `_h_watcher` | `ok, type, id, desk, hint, rows` | CoordError | - | Y |
| invite | `_h_invite` | door board / mint / etc. | (admin) | - | Y |
| trust | `_h_trust` | `{trust}` or `{ok, trust}` | CoordError | - | Y |

Aliases (`thread`->`send`, `yield`->`unclaim`, `here`->`join`, ...) canonicalize before HANDLERS lookup. HANDLERS also keeps legacy `thread` / `yield` keys; after canonicalization they are unused for normal RPC.

## Inconsistencies found

### A. Envelope `mill` - **no gap**

Central helpers cover the locked surfaces:

- `mill_json.stamp_mill` / `dumps_mill*`
- `middleware._json` (HTTP join + wall JSON + mill HTTP errors)
- `asgi._ws_handle_client_text` (RPC ok + error)
- `push.Hub._broadcast`, `_kick_replaced`, `fanout` (pushes; webhook payload pre-stamped)

Tests: `tests/server/test_mill_json_version.py`, `test_ws_rpc.py`, `test_ws_kick_replaced.py`.

Out of scope / not mill-wall verb envelopes: MCP stdio JSON-RPC (`mcp_mill.py`), local prefs writes, perf log lines.

### B. Channel error shape (document, not a bug)

- WS: always `{ok:false, error, mill}` (+ `id`)
- HTTP: `{error, mill}` without `ok` (status code carries success)

Intentional; do not unify without a Host lock.

### C. Soft failure inside successful RPC envelope

`pass` (unknown need), `unclaim`/`unpark` (unknown need), `hold`/`drop` (contention) return lean `{ok:false, ...}` while the RPC envelope stays `{ok:true, result:...}`. Sibling verbs (`claim`, `note`, `assign`) raise `CoordError` for missing need -> envelope `ok:false`.

**Not fixed here** - behavior change for clients; needs Host/Gardener speech, not a silent Builder rewrite.

### D. Lean key drift: `need` vs `need_id`

| Uses `need_id` | Uses `need` |
|----------------|-------------|
| open, claim, assign, note, todo rows | pass, unclaim, unpark |

Same card spine; different key. Document for Gardener; **not fixed** (additive dual-key would widen surface; rename would break callers).

### E. Payload `ok` presence drift

Some mutators always include lean `ok` (claim, assign, doing, hold, drop, watcher, trust-set, reset). Others omit it (open, note, send, list verbs). Envelope `ok` remains the wire success bit. Informational only.

### F. Dead / redundant HANDLERS keys

- `thread` after alias -> `send`
- `yield` after alias -> `unclaim`
- `_h_label` branch `verb == "label"` never reached (`label` -> `_h_label_name`)

Cleanup optional; not required for mill-version lock.

## Fixes applied

**None.** No clear, small mill-version / envelope stamp bug. Avoided wholesale payload rewrite (soft-ok / need_id).

## Evidence

- Registry census: `WALL` 40 verbs; `HANDLERS` covers all WALL keys; aliases resolve.
- Stamp paths reviewed: `mill_json.py`, `middleware._json`, `asgi` RPC, `push` broadcast/kick/fanout.
- Self-test: python -m pytest tests/server/test_mill_json_version.py tests/server/test_ws_rpc.py tests/server/test_ws_kick_replaced.py - **17 passed** (repo basetemp).

## Ready for

- **Validator**: envelope `mill` lock holds; no code change.
- **Gardener** (speech only): soft-ok vs CoordError on card verbs; `need` vs `need_id` lexicon; optional dead HANDLERS cleanup. No docs rewrite in this claim.
