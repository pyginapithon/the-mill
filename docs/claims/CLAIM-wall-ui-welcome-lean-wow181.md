# CLAIM wall-ui-welcome-lean-wow181

## Bug / ask
Host: Nest welcome popup too much stuff. Gardener locked skinny wakeup.
Host lock: INVITE strip/chip ONLY for humans in **high** trust; limited must hide chip and mint must not work.

## Fix (local tip; no push)
1. Drop workstation/agent paste walls and long beats.
2. One copy block #wall-welcome-join via wallWelcomeWakeupText:
   - pip install -U the-mill
   - Read docs/JOIN.md - follow its wakeup paste (mill join then mill connect)
   - blank line + invite URL when ready
3. Keep Generate URL (gated), Copy, Enter Nest, noshow.
4. wallInviteGateOk => 
eturn t === "high" only (no limited/admin bypass). wallApplyInviteGate hides #wall-invite-box + disables mint.
5. Cache bust ?v=wow181. Markers WALL_WELCOME_LEAN_WOW181, WALL_INVITE_HIGH_TRUST_ONLY_WOW181.
6. wow180 seat_count markers/behavior kept when gate on.

## Glance (host)
Hard-refresh (oot.js?v=wow181). High trust: INVITE chip + welcome with 2 Gardener lines + URL. Limited: no INVITE chip; Generate disabled/hidden.

## Out of scope
Push / pack / PyPI. JOIN.md body. OIDC middleware stash.

## Self-test
`
pytest tests/wall/test_wall_ui_invite_high_trust_only_wow181.py tests/wall/test_wall_ui_welcome_persist_dismiss_wow174.py tests/wall/test_wall_ui_invite_seat_count_wow180.py -q
`
