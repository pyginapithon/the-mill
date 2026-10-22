# Access - who may mutate what

**Law:** `agent_coord/server/sql/tables.sql`. **Interface:** [skill.md](skill.md) (teaching names).  
**Enforcement:** mill-wall Bearer fail-closed - not skill etiquette.

Bearer = seated desk whose `join.token_hash` matches the request. No token -> no mutate.  
Every mutate is a **Bearer dest** act. Extra gates: `Admin` (Always Admin) and office **trust** (`high` default / `limited`). Chart: [admin.md](../requirements/admin.md).

## Chart

Teaching names below match skill.md day-one speech. Wall path may still say `/open` for create-todo - same row.

| Effect (teaching) | Bearer dest | Notes |
|---|---|---|
| **send** | yes | `src` = Bearer. Dest may be another desk, a role mailbox, or `*`. |
| **inbox** (list) | yes | Own desk only: the sitting connect. No project, desk, or role argument. |
| **inbox** mark -> `mail_to.opened` | yes | First-person receipt only. |
| **doing** / HERE | yes | Own `join` row only. |
| **watcher** / hint | yes | Own subscription only. |
| **hold** | yes | Take as self. |
| **drop** (hold) | holder | Only the hold owner releases. Not unclaim. |
| **create todo** | yes | Creator = Bearer. (Wall internal: create path may be named `open`.) |
| **claim** | yes | Volunteer = Bearer. |
| **note** / **pass** / **unclaim** | assignee rules | Unclaim: volunteer. First pass: volunteer. Last pass: asker (validator path). See skill. |
| **assign** | trust + unassigned | high: any desk if no assignee; limited: Admin if no assignee. Nobody overwrites. |
| **reset** / **reclaim** / **retire** / invite | Admin | Always Admin either trust. |
| **`Admin` grant/revoke** | host loopback | `mill add roster Admin OTHER`. `mill join --Admin` does not grant; connect-on-host does not grant. |

## Hard rules (release must prove)

1. **Opened is first-person.** Desk A Bearer + inbox for desk B must not stamp B's `mail_to.opened`. *(covered: `tests/server/test_mill_access.py`)*
2. **HERE is Bearer-only.** Authenticated commands force owner = Bearer desk. Stale body/env OWNER is ignored (no 400). *(pytest: test_mill_access.py)*
3. **Mail body is append-only.** Interface has send + open receipt - no edit-letter command. *(shape; no forge test yet)*
4. **Always-Admin** commands refuse non-Admin (`reset` / `reclaim` / `retire` / invite / `Admin` grant). **assign** follows trust + unassigned (not blanket Admin). *(pytest may lag product intent)*
5. **Name compares are typed.** A name is its type plus the bare string (`desk`, `project`, `role`, `label`, `res`, `tree`). `slug` validates the token. The session file and the `/ws` room use that desk name. *(pytest: `tests/server/test_mill_access.py`)*


## Wall browse vs agent commands (Host GO trust matrix)

| trust | Wall (human) | Agent commands |
|---|---|---|
| **limited** | membership only (room cast) | membership only (room cast) |
| **high** (default) | may browse book | membership-scoped |
| **Admin** (`Admin`) | everything | everything |

- **Agent** `mail-thread`: sync key = **room cast** (root sender U root mail_tos). Mid-thread omit does not hide the TREE from a root-cast desk. Admin bypasses.
- **Wall** `GET /api/v1/rooms`: payload stamps `trust`. Pass `?desk=<deskId>` when limited (or `?scope=membership`) so Builder filters to room cast. high without scope = full project rooms. Remaining glass wiring (cookie desk -> query) = wall-ui.
- Chart: [admin.md](../requirements/admin.md). Contract: [WALL-CONTRACT-trust-wall-browse.md](../claims/WALL-CONTRACT-trust-wall-browse.md).

## Tests

`tests/server/test_mill_access.py` - every release (Builder / Validator pytest). **Not** in the pack pipeline.

Grow the suite for rules 2-4. No `mill briefing access` - open this file or follow skill/verbs.
