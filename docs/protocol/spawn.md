# mill briefing spawn - HINT catch-all program

A catch-all program for every HINT is the route key `*` (JSON on stdin).
The chain lives under `~/.mill/session/<name>.route` (see [route.md](route.md)).

## Day-one

1. Leave `mill connect` running for the desk.
2. Optional catch-all: `mill route add * -- python path/to/handler.py` from that same parent shell.
3. Prefer per-HINT keys (`mill route add mail:MAIL -- ...`) over the catch-all.

## Vendor poke fallback

When no mill route entry handles the frame, the vendor poke looks for a program before the vendor connector. PING is never spawned. First hit:

1. `AGENT_COORD_SPAWN` (program argv).
2. This desk's spawn map, `~/.mill/session/<desk>.spawn` (or the office host file of that role). Lines are `key = program`. The key is `type:hint`, then `*`. A letter is `{kind: mail}` and has no `type` or `hint`, so a `mail:MAIL` line in this file does not match it. `mill route` is what matches `mail:MAIL`.
3. Config `spawn`, then `bot_wake_cmd` (`config.toml`; `AGENT_COORD_SPAWN` and `AGENT_COORD_BOT_WAKE_CMD` override the file).

A key that is present with an empty program does not fall through to `*`. This map is not `mill route`.

## Must not

- Invent Arm verbs that are not on PATH.

See also: [connect.md](connect.md), [hints.md](hints.md), [route.md](route.md).
