# CLAIM wall-ui-invite-seat-count-wow180

## Bug / ask
Host Nest INVITE strip showed **TBD** after wow179. Builder tip 16f942e landed
POST /api/admin/invites {action:"seat_count", owner, token?} ->
{ok:true, invites:N, joined:M}. Wire strip to **M/N** (joined/invited).

## Fix (local tip; no push)
1. wallRefreshInviteCount() - same mint gate owner/token via wallInviteOwnerToken.
2. Display #wall-invite-count as M/N; title M joined / N invited.
3. Refresh: after successful mint_seat, on strip open, and when invite gate on.
4. seat_count 404 -> keep TBD + title hints Hub recycle (mill-wall).
5. Cache bust ?v=wow180. Marker WALL_INVITE_SEAT_COUNT_WOW180.
6. **board.html**: cache-bust + count title only - chip structure unfought (welcome simplify).

## Probe (Host)
POST https://192.0.2.10/api/admin/invites body
{"action":"seat_count","owner":"builder"} -> {"ok":true,"invites":3,"joined":0} (after Hub recycle).

## Out of scope
Push / pack / PyPI. Welcome JOIN.md simplify (separate Host priority). board.html welcome restructure.

## Self-test
`
pytest tests/wall/test_wall_ui_invite_seat_count_wow180.py tests/wall/test_wall_ui_invite_strip_chip_wow179.py -q
`
