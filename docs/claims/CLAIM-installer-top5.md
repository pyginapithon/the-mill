# CLAIM - Installer top-5 (public bind, systemd honesty, CA pin, invite session, update)

**Branch:** `claim/installer-top5`
**Base tip:** `3f1fff7` (PyPI 0.6.16 on `main`)
**Roles:** Builder (implement) / Host Installer (acceptance) / Shipper (later)

Remint seat is **out of scope** (human/Admin ops only). No dedicated service account - unit `User=` is the invoking user.

## Claims

### A1 - `--public` / `--lan-only` reach `write_role`; public forces invite door
- CLI rejects both flags together (non-zero). Evidence: `agent_coord/__main__.py` install handler (mutual exclusive before `write_role`).
- `lan_only` / `public` passed into `write_role` -> `_write_wall`. Evidence: `agent_coord/install/host.py` `write_role` (`public`/`lan_only` params + `door_plan`) and wall return fields.
- With `--public`, `--apply` calls `set_door("invite")` (or refuses if door still not invite); dry-run / no-apply reports `door_plan` action. Evidence: `host.py` `door_plan` block in `write_role`.
- Tests: `tests/install/test_installer_top5.py` (`test_a1_*`).

### A4+B5 - Honest Linux systemd + `_apply_wall` return codes
- Unit emits `User=<invoking user>`, `Environment=AGENT_COORD_MILL_HOME=<dest>`, and `Environment=PYTHONPATH=<user site>` when the pack is under a `--user` install (or when `pythonpath=` is passed). Evidence: `host.py` `systemd_unit` (~2208+).
- `_apply_wall` uses `sudo -n`; any non-zero rc -> `ok:false` with `failed_step` naming the step; caller no longer text-matches for ok. Evidence: `host.py` `_apply_wall` (~3026+) and `_write_wall` apply caller.
- Tests: `test_a4_systemd_unit_user_and_env`, `test_b5_apply_wall_failed_systemctl`, updated `test_systemd_unit_contract`.

### A2 - Join CA fetch validates / pins before trust
- Body validated as CA PEM via `parse_mill_ca_pem` (shared with `materialize_mill_ca`); nothing written on bad body. Evidence: `agent_coord/client/http.py` `parse_mill_ca_pem` / `fetch_mill_ca`.
- Invite URL may carry `ca=<sha256-der-hex>`; mismatch -> no write. Mint paths build `/?invite=...&ca=...` when a local CA exists (`door._invite_path_with_ca`). Evidence: `http.py` `ca_fingerprint` / `ca_fp_on_url`; `agent_coord/server/admin/door.py` `_invite_path_with_ca`.
- Join dest is `home/ssl/ca.crt`. Evidence: `host.py` `mill_join` `ca_dest`.
- Tests: `test_a2_*` in `test_installer_top5.py`.

### E16 - Invite join writes a session token (closes #510 intent)
- Local door/db invite status check removed from `mill_join`; trust is remote Wall + CA pin/PEM.
- After CA trust, invite+`--desk` POSTs Wall `join` and stores the returned session token (or exits non-zero with exact next command when `--desk` missing / Wall returns no token). Evidence: `host.py` `mill_join` invite branch.
- Tests: `test_e16_invite_join_writes_session_token`, `test_e16_invite_join_without_desk_gives_next_cmd`.

### D14 - `mill update`: admin gate, stop->pip->start, separate result fields
- Admin check up front when `update_requires_admin()` (Windows); clear refuse `not-admin` with `pip_applied=false` / `restart_ok=false`.
- Order: `wall_stop_cmds` -> pip -> `wall_start_cmds`; Linux uses `sudo -n`.
- Result exposes `pip_applied` and `restart_ok` separately; start failure leaves `ok:false` and notes wall down.
- Evidence: `host.py` `wall_stop_cmds` / `wall_start_cmds` / `run_update`.
- Tests: `test_run_update_restart_failure_reports_separately`, `test_run_update_refuses_when_not_admin`, updated apply order asserts.

## Deferred
- Dedicated non-root service account (explicitly rejected by Host Installer acceptance - use invoking user).
- Remint seat / human Admin seat ops.
- Broader installer-hardening children (A3 DB root secret, B6-B9, C10-C13, D15 nginx apply, E17 directory door, F18-F20) - not in this top-5.

## Tests run
```
PYTHONPATH=. python -m pytest \
  tests/install/test_installer_top5.py \
  tests/install/test_mill_update.py \
  tests/install/test_mint_ca_join.py \
  tests/install/test_mill_join.py \
  tests/install/test_mill_join_fail_closed.py \
  tests/install/test_install_cross_platform.py::test_systemd_unit_contract \
  tests/install/test_install_real_services.py::test_apply_wall_mints_ca_and_leaf \
  tests/install/test_install_real_services.py::test_apply_wall_reports_missing_openssl \
  -q
```
**Result:** 39 passed, 0 failed.

## Blast radius (Shipper / Host Installer)
- Linux unit files gain `User=` + env; existing units need re-`install wall --apply` / copy to pick up.
- `_apply_wall` return shape is now `{"ok","steps","failed_step"}` (callers that expected a bare list should use `["steps"]` - pack-internal caller updated).
- `mill update` on Windows refuses without Admin; Linux stop/start uses `sudo -n` (will fail closed without passwordless sudo instead of hanging).
- Invite URLs may grow `&ca=` fingerprint; old URLs without pin still work (pin optional).
- Invite `mill join` without `--desk` now fails closed with a next command (previously ok:true with no session token).

## Recommended Commit

Tip of branch `claim/installer-top5` (this commit). Verify with:

```
git rev-parse claim/installer-top5
```
