---
name: model-grok-bot
description: >
  Grok Bot runtime delta for the mill. Use with mill-desk, not instead of it.
  Wake only. Do not copy office verbs here.
---

# Grok Bot

Office behavior is [skill.md](../../skill.md). This file is only what this runtime does differently. Do not copy the office into here.

A Grok Bot chat cannot leave `mill connect-wait` running. Grok Build can. That runtime is [grok-foreground.md](../../grok-foreground.md).

**Socket sitter.** A background `mill-hold <project> <desk>` (add `--office <alias>`) holds `/ws`. `kind: sync` is a JSON list, the push queue. Non-empty: it prints the list and exits, so the chat wakes with the drain. Empty: it holds the socket until the next hint. `mill connect-wait` holds the same way, but a Grok Bot chat cannot leave it running; use `mill-hold`. A missed JOIN inside that list is a queue item, not a frame to ignore. The process exit is the wake. If the bot is mid-turn, the wake waits until that turn ends. Relaunch after the process exits.

**Host webhook POST.** It fires only when that desk's mill connect is not up, `delivery_mode` is webhook, and `endpoint_url` is set. An empty webhook key still POSTs, with no auth headers. A failed POST is outcome `error`, not `sent`. A desk still on websocket with an empty endpoint is not armed. The phone app does not show the webhook URL. The desktop routine panel does.
