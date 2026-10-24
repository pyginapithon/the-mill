# Grok Build idle wait

Office behavior is [skill.md](skill.md); its section "Grok Build idle" is the rule. This file is only the detail behind it. Regression row F27 (grok-foreground-shipped-forms).

Grok Build has no direct message from one chat into another. A poke is mill MAIL to that desk. The desk wakes when its own wait is up. With no wait up, the letter stays in the book until a later connect takes the sync.

## The wait

Run one wait as a background task this Grok session owns (start it in the session, then `Ctrl+B`). The chat stays free.

```
mill connect-wait YOUR-DESK
```

Replace `YOUR-DESK`. The desk sits on the Office roster of the office this computer joined. Never print the socket URL.

- Owned: a wait started by a shell that then exits dies with it (Windows prints `parent exited`). Start it from the session, not from a throwaway shell.
- One: never two waits, and never a poll loop of connects. A second connect for the seat is refused as busy; `--take` takes the seat from the first.
- One wake path: no `mill route`, webhook or `--vendor grok-build` beside this wait, or the same letter is handled twice.
- A human line wins and is not a mill order.

## On wake

The wait exits on one non-PING hint (a letter is `"kind":"mail"`; a non-empty `kind: sync` list is the queue). Read it before you say the wait is up. `body_trunc` means `mill mail-thread ID` before acting.

- A letter that asks this desk for work: count those letters as N. `connect-wait` does not publish the reply bridge, so open a short connect in the same shell, from a directory that is not the checkout, with `PYTHONPATH` clear. Reply "Doing K of N" to each, do the letter, reply the result, stop the short connect, start the wait again.
- A status note that does not ask this desk: `mark` it, do not reply. Replies to status notes ping-pong the room.
- A letter that says stop: leave the wait down.
- The wait dropped with no letter: start it again.

```
python -m agent_coord connect YOUR-DESK
python -m agent_coord reply MAIL_ID --body-file RESULT.txt
mill connect-wait YOUR-DESK
```

The short connect stays until one connection can hold the seat and run commands (card 703).

## Reminder (optional)

A durable 60-second reminder in this session may check the process list for `connect-wait YOUR-DESK` and print `UP` or `DOWN`. It never opens a connect: a second connect is refused as busy, or with `--take` takes the seat. A reminder wakes only its own session; a closed PC does not sit.

## Not this job

`mill connect YOUR-DESK --vendor grok-build --session UUID` starts a new headless `grok -p` turn per HINT. Injecting a HINT into an open TUI turn is not built ([connect.md](connect.md)).

A skill edit reaches a new chat only after skill.md is recopied and the session reloads; an open chat keeps the old text.
