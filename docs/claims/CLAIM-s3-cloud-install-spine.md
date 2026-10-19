# Claim - S3 cloud install product spine

Status: **done on box worktree** (GO honored). Checked: see evidence below (PT).

## What / why

`mill install cloud` was a stub notes file (old lexicon: VPN-as-door, gym.pt, peek/needs, introduce collect, ~24 provider peers). CLOUD.md is the intent bar for S3. This cut turns cloud install into an **agent spine**: pip -> `mill install server --apply --public` -> `mill init --yes`, invite door default, local probes only (no cloud APIs / no key storage), printed providers collapsed to aws|azure|gcp|self, JOIN verbs, done-report `next[]`, and explicit **not measured OOTB / #502**.

## Files changed

- `docs/install/CLOUD.md` - probe contract, done-report example, TLS stance pointers, Day-2 HOST pointer, on-VM mysqld default, status #502
- `docs/requirements/install.md` - align S4b with probes + escape hatch + invite default
- `docs/JOIN.md` - thin S3/public invite-door note
- `agent_coord/install/catalog.py` - `PRINTED_CLOUD_IDS`, `printed_cloud_id`, rewritten `cloud_runbook`
- `agent_coord/install/host.py` - `probe_cloud_local`, rewritten `cloud_notes` / `_write_cloud`, check_office cloud contract, score note; `_posix_book_services` tolerates missing `systemctl`
- `docs/claims/CLAIM-s3-cloud-install-spine.md` - this file

## Evidence (roles-only paths)

On shared bot computer worktree `/workspace/the-mill-s3-cloud` (office checkout Shell `machineId` was **not** available to this executor subagent schema - see blockers).

| Check | Path / result |
|---|---|
| `mill install cloud --dry-run` | `/workspace/claims/s3-cloud-install/dry-run.json` - ok, mutated false, would_write cloud notes |
| `mill install cloud` | `/workspace/claims/s3-cloud-install/cloud-self.json` + `cloud-office-self.txt` - probes + next[] done-report shape + #502 |
| `mill install cloud --provider aws` | `/workspace/claims/s3-cloud-install/cloud-aws.json` + `cloud-office-aws.txt` - aws hyperscale stub |
| azure/gcp/self/hetzner | self-test matrix: azure/gcp deep stubs; self + hetzner -> printed `self` |
| Lexicon guard | absent: gym.pt, briefing join, introduce collect, peek/needs, long provider peer list; present: mill join/connect, No VPN-as-door, spine commands |
| Install unit tests | `pytest tests/install/test_install_preflight.py tests/install/test_install_check_liar.py` - pass |

## Deferred

- Live cloud VM measure (#502) - aws/azure/gcp end-to-end
- Linux systemd mill-wall OOTB measure
- Pack/PyPI/ship
- Managed DB path / migrate verb
- Docker-as-second-installer
- Twelve cloud API installers

## Blockers

1. **Registered-host office checkout** (`machineId` 58ba8b0d-...) - this executor's Shell tool schema did not expose `machineId`, so edits/commit could not land on the office checkout path. Work landed in box git worktree `claim/s3-cloud-install-spine` from `origin/main@57451c1`. Parent/host should cherry-pick or merge onto office checkout and re-run `mill install cloud` there for host evidence.
2. No push performed (prefer local commit).
