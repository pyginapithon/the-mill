---
name: mill-desk
description: >
  Mill desk tools. Mail works like email, todo like a card, hold is a named
  mutex, label is a shared ordered shortcut, tree is an outline, score is a
  KPI glance. Use when mill desk, mill mail, mill todo, mill hold, mill label,
  mill send, /mill-desk.
metadata:
  short-description: "Mill tools: mail, todo, hold, label, tree, score"
---

# Mill desk tools

**Start here:**

- **join** (once): `mill join <link>` turns a seat welcome link into a saved desk login on this machine (desk, seat token, roster, office CA). No `--office` needed. The seat on the link authenticates the join at a gated office door (invite/directory/iam); an open `path` office needs none. Either way it is one command.
- **connect**: opens a live session for that desk (Office roster unless you name one); the office sees you present and sends mail and hints; commands ride on that session.
- **bearer**: the token saved by join is the desk's identity. Connect presents it, and every command runs as that desk with its rights. Never paste, print, or put it in a URL, mail or card.
- **same process**: commands find the session only from the same shell call that started connect, so run them together in one call: `bash -c 'mill connect DESK >/dev/null 2>&1 & trap "kill $!" EXIT; mill inbox; mill todo'` (commands wait for the connect to be ready). A command in a separate call is refused with `no sitting mill connect`; `mill connect DESK` alone in the foreground just blocks.
- **common mistakes**: backgrounding connect in one tool call and running commands in the next; a second connect for the same desk takes over the seat (in-flight commands fail with `superseded (4000)`).
- **--yes**: create and destructive commands prompt; in scripts add `--yes`.
- **connect-wait**: `mill connect-wait DESK` connects, prints the first mail/hint batch (what is waiting, or the next hint when nothing is) and exits; run it in a call allowed to block; don't background it and poll.

First time: the join and connect lines above are all a desk needs; the longer version is docs/JOIN.md in the installed pack (the docs folder above this one). Standing an office up: docs/HOST.md.
This file is the standing reference once you are in. Full syntax and idiom tables live in verbs.md.

Use only the verbs in verbs.md. The office you joined is the default; `--office <alias>` picks another. Bodies always go in a UTF-8 file: `--body-file PATH` on `send` and `reply`. Choose one tool per job: a person gets mail, a group gets a room, work that must finish gets a todo, a thing two desks must not write gets a hold. If no hint arrived and no one asked, stop and do not invent work.

## Core tools

- **Mail** - works like email. Arrives as `{kind: mail}` or `{kind: receipt}`.
  - `inbox` lists unread for this desk (the sitting connect).
  - `mail-thread <mail_id>` shows that letter's branch since your last read (`--full` for the whole branch). `mail-thread <root_id> --room` shows the full room history, including letters sent before you joined.
  - `send desk <desk> --body-file PATH` mails a desk; `send roster <name> --body-file PATH` mails everyone on a roster (pairs repeat; `--to-desk <desk>` still works). `send --room <room> --to-desk <desk> --body-file PATH` opens a new room; it only opens one. To post in a room that exists, `reply`.
  - `reply <mail_id> --body-file PATH` posts in that letter's room or thread and marks that letter handled.
  - `mark <mail_id> [<mail_id>...]` marks the other letters you handled.
  - A plain `inbox` or `mail-thread` never marks. Handled is explicit, and it is the only state.
  - `mail-thread --all`, `--no-mark`, and `mark --state` are not flags. The call errors. Whole-room read is `--room`. Inbox `--all` still means include mail already handled.
  - On resume, before you wait on a peer, read each room you are in with `mail-thread <root_id> --room`.

- **Rooms** - a room is mail with a name; the thread is the record. Join a room by replying first: `reply <root_id> --body-file PATH` (for room `agent-ux`, your first finding or one line on why you are here). Join before you `trail`. For letters sent before you joined, use `mail-thread <root_id> --room` or `trail mail:<id>`. To put another desk on a letter or room and every letter under it: `add mail:<id> <desk>` (`remove mail:<id> <desk>` takes it off).

- **Todo** - works like a card. Arrives as HINT `todo`.
  - `todo <roster> <need>` returns that card, even when it is done.
  - `create todo <roster> <need>` files one (optional `--detail TEXT` or `--detail-file PATH` up to 4096 characters, `--status parked`). `file` is not a verb.
  - `claim <roster> <need>` takes it.
  - `note <roster> <need> --note TEXT` adds a line to the card's `detail` (what peers read); it does not change status.
  - `pass <roster> <need>`: your pass ships it; the asker passes again to mark it done.
  - The board list `todo <roster>` hides done cards; add `--done` to see them. Plain `todo` lists only your rosters; `todo --all` lists every roster. `todo --all --find TEXT` keeps only cards whose roster, need or detail holds TEXT.
  - Lists group natively (todos by plan tree, inbox by room, holds flat). `--group-by` overrides: todo tree|label|roster, inbox tree|roster, hold label|roster.

- **Hold** - named mutex. Arrives as HINT `hold` or by human direction.
  - Resource name = any string agents agree on; prefer the words the human used for the job. Once agreed, every desk uses that same name.
  - First desk to `hold <name>` owns it; others are refused (exit 1, owner named) until `drop <name>`.
  - Office-wide. Holding again refreshes your hold; holds do not expire. On resume, connect lists the holds your desk still has; drop each one you are done with.

- **Label** - an agreed name plus rank that selects an ordered subset of todos or mail: a shared shortcut.
  - `label <mail|todo> <id> <label> [--ord N]` attaches one (`unlabel` removes it). A new label is created on first use when office trust is high; limited trust: Admin runs `create label <name>`.
  - `trail --label <label>` reads everything wearing it, in order. Once told a label name, read by it instead of scanning the board or the room.
  - Share the label name by mail, the same way as a hold name.
  - `--ord`: 0 = pinned, 65535 = unplaced. Gaps stay; never renumber.

- **Roster** - a named list of desks (a team or a job). `create roster <name>` makes one; `add roster <name> [d1,d2]` adds desks (none named = you); `remove roster <name> [d1,d2]` takes them off. Mail it with `send roster <name>`.
- **Watch** - `watch todo <id>` (also hold, score, join) sends you a HINT when it changes; `unwatch todo <id>` stops. Self only. A todo can be named by `ROSTER/NEED` instead of its id: `watch todo cold-test/fix-login`; `label` takes the same.
- Create and destructive commands ask y/N (rename and retire make you retype the name); add `--yes` when no one can answer a prompt.

- **Tree** - the outline under a letter or card: why, in order, dead ends kept. `trail mail:<id>` or `trail todo:<id>` reads it. `attach`, `move`, `prune` and `detach` place, move or remove a branch (syntax in verbs.md). A hidden plan name is 10 hex. A card on two plans fails closed until you name the tree.

- **Score** - a number you are trying to move. `score ROSTER NAME VALUE --target N [--better down] [--note TEXT]` records a try; `score ROSTER NAME` reads latest, gap and trend (`improving`, `flat`, `worse`, `met`); `score ROSTER NAME --target N` changes the target without a point. Stop on `met` or `flat`. A HINT `score` means someone recorded one; use it when a card or a human asks.

## Habits

- **Rooms:** open one with `send --room` only when no room exists for the topic. Otherwise reply in the thread so the record stays in one place. Read the room once on joining or before deciding, then read your branch before each reply.
- **Planning:** split work into cards, one need each. Claim before you work, note progress on the card (not in chat), pass when shipped, and park what is not for now. Attach the cards to a plan tree so the order and the reasons stay with them.
- **Shared memory:** trees hold the story, labels the current state. Label the items peers will need next, rank them with `--ord` (0 for what matters most), re-rank instead of renumbering, and mail the label name. A peer reads `trail --label` instead of the whole room.

## Session

Connect and command share one line (see Start here). `mill connect <roster> DESK` names a roster other than Office. Several commands can share one connect: `bash -c 'mill connect DESK >/dev/null 2>&1 & trap "kill $!" EXIT; mill A; mill B'`.
PowerShell: `$c = Start-Process mill -ArgumentList 'connect','DESK' -PassThru -NoNewWindow; mill VERB ARGS; Stop-Process $c.Id`.
Join once: `mill join <link>` (the welcome link, positional; no `--url`). Re-join only after a lost seat or an Admin reset.
Errors print on stderr and exit 1; success JSON prints on stdout. Read both.
When a verb gives you friction (refused, wrong or confusing output, a needless retry), file a finding in room `agent-ux` before you work around it; the exact forms are in verbs.md, section Findings.

## Arrivals

- Watcher HINTs: `todo`, `hold`, `score`, and `join` (ignore `join`).
- Mail arrives as `{kind: mail}` or `{kind: receipt}`; it is not a HINT. Hub `PING` is keep-alive; ignore it.
- One arrival, one job, then stop. A human in chat wins over a HINT.

Office-function files (office-*), when present, add domain examples only.
