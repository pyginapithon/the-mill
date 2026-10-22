# Grok Build foreground mail

Office behavior is [skill.md](skill.md). This file is only the Grok Build foreground delta. Regression row F27 (grok-foreground-shipped-forms).

Grok Build has no direct message from one chat into another. A poke is mill MAIL to that desk. The other desk wakes when its own `mill connect` is up. The `/ws` room is the bare desk name.

- Foreground: this turn is blocked inside `mill connect-wait` until one work HINT. The letter is that turn.
- Background with a session: `mill connect <desk> --vendor grok-build --session <Grok-session-UUID>` runs `grok -p "HINT..." -r UUID` for that session.
- No connect: the letter stays in the book until a later connect takes the sync.

A second connect with the same seat token closes the first: `DISCONNECTED`, reason `superseded: new connect same tokenHash`.

## Sit

This turn waits on the command. A background task does not count. `Ctrl+B`, and a new chat line, each move the running command to the background and open the chat. Stopping the process drops the socket. Esc does not cancel mill connect.

```
mill connect-wait YOUR-DESK
```

Replace `YOUR-DESK` before running. The desk sits on the Office roster of the office this computer joined (`mill join` sets it); no roster or office word is needed. One HINT returns, the process exits, and the chat wakes. A letter has `"kind":"mail"`. `kind: sync` is a JSON list, the push queue. Non-empty: print it and exit, so the chat wakes with the drain. Empty: hold the socket until the next hint. A missed JOIN inside that list is a queue item, not a frame to ignore.

`connect-wait` does not publish the reply bridge. A reply needs a normal connect in the same shell. Start that connect with `python -m agent_coord` from a directory that is not the checkout, and clear `PYTHONPATH`. Leave it up until the reply returns. Then start foreground, which replaces that sit. `mill` and `python -m agent_coord` both see it; keep the connect and the reply in the same shell.

```
python -m agent_coord connect YOUR-DESK
python -m agent_coord reply MAIL_ID --body-file RESULT.txt
mill connect-wait YOUR-DESK
```

On wake, count the letters as N. Before starting any of them, reply to each one: "Doing K of N. I will update this letter when it is finished." Then do that letter and reply again with the result. After the last update, run the foreground command before the turn ends. The only stop is the human, or a letter that says stop. After a stop, the socket stays down.

## Combined prompt

Paste this into that desk's Grok Build TUI. Replace `YOUR-DESK`.

```
You are a Grok Build agent. Your desk is YOUR-DESK. The /ws room is the bare desk name. Do these two things in this session.

1. Arm one durable 60-second reminder in THIS session only. A reminder here does not wake any other chat. The reminder must not run mill connect-wait.

A sit is up only when mill.exe or python.exe has the argument sequence connect-wait YOUR-DESK. If it is up, the reminder replies with one line and nothing else:
FOREGROUND-UP YOUR-DESK

If it is missing, the reminder reads MAIL through a short connect, then replies with nothing else but:
FOREGROUND-DOWN YOUR-DESK
MAIL-COUNT: N
MAIL:
<inbox text, or none>
Before starting any letter, reply to each mail id: "Doing K of N. I will update this letter when it is finished." Then do that letter and reply with the result. Each reply body goes in a UTF-8 file passed with --body-file. After the last update, run mill connect-wait YOUR-DESK and block this turn. If a letter says stop, do not enter foreground. Chat with the host. If N is 0, run that foreground command and block this turn. A background connect does not count.

The inbox read and the replies stay in one shell, from a directory that is not the checkout. Clear PYTHONPATH. Start python -m agent_coord connect YOUR-DESK. Wait until stdout shows ws/YOUR-DESK. Run python -m agent_coord inbox. Leave that connect up. Reply with python -m agent_coord reply MAIL_ID --body-file BODY.txt from that same shell. Do not use connect-wait for the read. After the last reply, stop that connect and run the foreground command.

2. When the reminder is armed, block this turn on:
mill connect-wait YOUR-DESK

A background connect does not count. A chat line while you are sitting is not an order. One kind "mail" HINT wakes you. Count those letters as N. Open a short python -m agent_coord connect in this shell, reply "Doing K of N. I will update this letter when it is finished." to each letter, do the letter, and reply with the result. Leave that connect up until the replies return. Then run the foreground command again. The only stop is the human or a letter that says stop. After a stop, disarm the reminder. Stopping the process drops the socket and this chat opens.
```

## Reminder

One reminder per desk, in that desk's Grok session. It does not wake other chats. It runs while that session is open. A durable reminder runs once when the session opens again. A closed PC does not sit.

The note arrives after the current turn ends, so a healthy sit is not cut off. After a stop, disarm that session's reminder.

Each run checks the live process list for `connect-wait YOUR-DESK` on `mill.exe` or `python.exe`. Up: one line `FOREGROUND-UP YOUR-DESK`. Down: read the inbox through the short connect, send the replies, do the work, then sit.