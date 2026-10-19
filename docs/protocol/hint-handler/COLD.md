# Cold start

Read this file and `examples/stub_handler.py`. Nothing else, unless a command below exits non-zero.

Desk `hint-cold`. `--owner hint-cold` on every verb. No `--session`. No invite URL. Do not register. Do not open token files. `mill connect --owner hint-cold` presents the token. `mill_url` is in `~/.mill/config.toml`. Do not run `mill join` if `mill_url` is set. Leave the HINT filter file (`want`) absent so every frame reaches the handler.

Repo: the checkout that contains this file. Program: `~/.mill/handlers/DESK_hint-cold/on_mail.py`. Copy `examples/stub_handler.py` there. Set `_ROOT` to the `docs/protocol/hint-handler` directory that contains this file (`Path(__file__).parents[1]` is that directory only in `examples/`). Ignore other doc links in the stub. Do not delete that program on tear-down.

Read `~/.mill/session/active` and keep that text. Connect rewrites the file and does not exit.

`--owner` before the key on `mill route`. A flag after the key becomes the program. Pass the absolute path of `on_mail.py`. Printed argv may show `~` instead of the home directory. The route file must contain that absolute path. A `~` in that file is not expanded at start.

Commands. If one exits non-zero, stop and hand back stderr.

1. `mill route add --owner hint-cold mail:MAIL -- python <absolute path of on_mail.py>`
2. `mill connect <project> hint-cold --vendor grok-build`
   Proceed when stdout JSON has `"desk"` `DESK_hint-cold` and `"mode"` `ws`.
3. write `hint-cold mail` to `body.txt`, then `mill send --body-file body.txt --to-desk hint-cold`
   The JSON `id` is the mail id. Mail is not a watcher type. `mill add mail:ID` changes recipients, not watchers. The push is `{kind: mail}`.
4. `mill label-add mail <id> bug --owner hint-cold`
   A mail label does not plant a watcher. Wait for a new `hint-evidence.jsonl` line for this mail id. Remember it. Ignore older lines. If the send line is missing, hand back the `mail:MAIL` line from the route file and stop.
   A `default` line's `detail` is `{what,id,when,state,watchers,tree}`. `state` is `sent` for a live letter, `deleted` once the activity is deleted, else null.
5. `mill label-remove mail <id> bug --owner hint-cold`
   Leave the route armed until another line for this mail id is appended.
6. `mill route rm --owner hint-cold mail:MAIL`
7. Stop the process whose command line contains `--owner hint-cold`. Leave every other connect running. Do not change `mill_url`. Write the saved active text back to `~/.mill/session/active`.

Reply with the remembered recipe line.

`join:JOIN` and `heartbeat:PING` are dropped on receive. Do not arm them.
