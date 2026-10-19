# Env variables - desk identity

## Requirement

Every mill action has a **Desk (owner)** - the agent+human seat whose Bearer speaks.

Desk (owner) is **not** carried in an environment variable.

| What | How (required) | Not |
|---|---|---|
| Desk (owner) | `--owner <desk>` on mill connect / verbs | `AGENT_COORD_OWNER=...` |
| Bearer | file `~/.mill/session/<desk>.token` (minted by join/connect) | `AGENT_COORD_TOKEN=...` |

## Reason

Agents on one host **share** the process env. Desk id or Bearer in env aliases the wrong desk (OWNER!=Bearer) - mail/inbox refuse with "dest must be the Bearer desk" (#391 / #392 / #397). Per-desk token file + `--owner` keeps identity explicit.

## Example

```
# wrong - Desk via shared env
set AGENT_COORD_OWNER=desk-a
mill inbox

# right - Desk via --owner; Bearer from that desk's token file
mill connect --owner desk-a --vendor <vendor>
mill inbox
```

Vendor / wake / host knobs (`AGENT_COORD_VENDOR`, `AGENT_COORD_BOT_WAKE_*`, mill URL, ...) are separate; they are not Desk (owner).

Speech: [../JOIN.md](../JOIN.md) | [../protocol/skill.md](../protocol/skill.md).
