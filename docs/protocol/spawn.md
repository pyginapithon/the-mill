# mill briefing spawn - HINT catch-all program

A catch-all program for every HINT is the route key `*` (JSON on stdin).
The chain lives under `~/.mill/session/<name>.route` (see [route.md](route.md)).

## Day-one

1. Leave `mill connect` running for the desk.
2. Optional catch-all: `mill route add * -- python path/to/handler.py`.
3. Prefer per-HINT keys (`mill route add mail:MAIL -- ...`) over the catch-all.

## Must not

- Invent Arm verbs that are not on PATH.

See also: [connect.md](connect.md), [hints.md](hints.md), [route.md](route.md).
