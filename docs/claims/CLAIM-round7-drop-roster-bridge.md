# Claim - round7 cold A/B Loop-2 fixes (#126, #127, #101 message)

Status: Ready for Validator. Lands via patch to grok-tui; needs a pack. Python only, no SQL/SP.
Source: Gardener round7 cold A/B on 0.6.24 (lan). Triage: note @file -> dup #102 (noted, not fixed here).

## #126 drop-reply-says-released

| Item | Lock |
|------|------|
| `drop` own hold | `{ok: true, released: true, resource, id, owner: null, was_owner}` |
| `drop` someone else's hold | `{ok: false, released: false, resource, owner: <holder>, reason: "held by X, not you"}` |
| `drop` free / unknown | `{ok: false, released: false, resource, owner: null, reason: "not held by you"}` (was owner = caller) |
| SP refused | `released: false`, `reason: "release refused"` |
| Hint | HOLD fan-out only on a real release |
| `hold` reply | adds `held` (true/false); other keys unchanged |

Files: `agent_coord/server/records/hold.py` drop, `agent_coord/server/api/mill/rpc.py` _h_drop/_h_hold, `docs/protocol/verbs.md`.

## #127 send-echo-sender-roster

`mill_mail_insert` stamps the project on the letter when no `--roster`/`--reason`. The send/reply echo printed `sender.roster: null` while mail-thread and inbox showed the project. Echo is now `sender_aff or project`. Stored data unchanged.

Files: `agent_coord/server/api/mill/rpc.py` _h_send. Tests that pinned the null echo now expect the project (`test_send_mail_tos.py`, `records/test_room_reply.py`).

## #101 (message only)

`SESSION_WS_BRIDGE_REQUIRED` keeps its prefix (the #121 retry compares the constant) and adds: connect is bound to the process that started it; run verbs as children of that same shell; keep connect running. The by-desk bridge stays open on #101.

## Validator

1. `pytest tests/server/test_drop_reply_and_send_affil.py tests/server/test_send_mail_tos.py tests/client/test_parent_bridge.py` GO.
2. SQL suite: `tests/server/records/test_room_reply.py::test_inbox_public_shape_lean_mail` (needs MySQL; not run on the Builder box).
3. Live after pack: throwaway hold, drop it, drop again -> second reply `released: false, owner: null`; send with no `--reason` -> echo `sender.roster` = project, same as mail-thread.
4. Fresh shell verb with no connect -> error text names the binding.

## Roles only

Builder / Validator / Gardener / grok-tui. No names or home paths.
