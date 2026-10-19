# Claim - cloud docs spine

Status: **local commit** on `claim/cloud-docs-spine` (from main `13ee22b`, pack 0.4.15). Not pushed. Not measured OOTB. #502 not moved.

## What / why

A cold agent needs one spine for "put our office on a cloud" before the workstation command and the on-VM apply exist. This claim records the 0.5.x decisions and leaves a playbook file per provider so later claims fill commands instead of inventing a second outline.

## Files changed

- `docs/install/CLOUD.md` - workstation journey, three `mill install cloud` modes, preflight, phase-state file, probe pass/fail/skip contract, done-report shape
- `docs/install/cloud/aws.md` - skeleton, `Status: unmeasured`
- `docs/install/cloud/azure.md` - skeleton, `Status: unmeasured`
- `docs/install/cloud/gcp.md` - skeleton, `Status: unmeasured`
- `docs/install/cloud/self.md` - skeleton, `Status: unmeasured`
- `docs/install/README.md` - links the four playbooks
- `docs/requirements/install.md` - S4b names the same flags and leaves #502 unmoved
- `agent_coord/install/catalog.py` - printed runbook points at `docs/install/cloud/<provider>.md`
- `agent_coord/install/host.py` - cloud notes name that playbook path (git and `share/the-mill`)
- `pyproject.toml` - data-files so the four playbooks ship in the pack
- `tests/install/test_cloud_docs_spine.py` - runbook path, status line, phase headings, pack list
- `docs/claims/CLAIM-cloud-docs-spine.md` - this file

## Evidence

- `tests/install/test_cloud_docs_spine.py`
- `pytest tests/install/test_cloud_docs_spine.py tests/install/test_install_preflight.py tests/install/test_install_check_liar.py` - pass (59)

`docs/protocol/skill.md` is not in this claim. A pointer from that file belongs to Mill Prompt Gardener.

## Still open

- On-VM server apply: systemd mill-wall enabled and started, survives reboot, MariaDB on `127.0.0.1`, HTTPS on 443, re-run safe, invite door with one enabled invite
- Done-report filled from probes (any fail blocks green). The printer still uses placeholders
- Workstation preflight, phased plan, `--ssh`, phase-state writer (`~/.mill/session/cloud-install.json`)
- Full playbook commands (aws, azure, gcp, self), still `unmeasured`
- End-to-end measure and cold-agent test. #502 stays put until those pass for a provider
- Pack ship: data-files are listed; Mill Pack Shipper confirms on the next pack. Version was not bumped

Six `tests/install` failures reproduce on main without this diff (empty-bootstrap plan text, `docs/HOST.md` pointer, wall next-steps mkdir, packaged scripts path, mill join config write, update refuses `pip install .`). They are not part of this claim.
