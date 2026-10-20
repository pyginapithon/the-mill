# Cold start

Read this file and `examples/stub_handler.py`. Nothing else, unless a command below exits non-zero.

Desk `hint-cold`. No `--session`. No invite URL. Do not register. Do not open token files. `mill connect hint-cold` presents the token saved by join. `mill_url` is in `~/.mill/config.toml`. Do not run `mill join` if `mill_url` is set. Leave the HINT filter file (`want`) absent so every frame reaches the handler.

Repo: the checkout that contains this file. Program: `~/.mill/handlers/DESK_hint-cold/on_mail.py`. Copy `examples/stub_handler.py` there. Set `_ROOT` to the `docs/protocol/hint-handler` directory that contains this file (`Path(__file__).parents[1]` is that directory only in `examples/`). Ignore other doc links in the stub. Do not delete that program on tear-down.

Desk commands run only in the parent shell that started connect. The desk is that connect. A second call is refused with `no sitting mill connect`. The trap stops connect when the shell exits. Everything after the route key is the program. Pass the absolute path of `on_mail.py`. A `~` in the route file is not expanded at start.

This is the same parent shell `mill join` prints (`bash -c 'mill connect DESK >/dev/null 2>&1 & trap "kill $!" EXIT; mill VERB'`). Replace `PATH_OF_ON_MAIL_PY` with the absolute path of `on_mail.py` before you run it. If one command exits non-zero, stop and hand back stderr.

```bash
bash <<'EOF'
mill connect hint-cold --vendor grok-build >/dev/null 2>&1 &
trap "kill $!" EXIT
mill route add mail:MAIL -- python PATH_OF_ON_MAIL_PY
printf '%s\n' 'hint-cold mail' > body.txt
mill send desk hint-cold --body-file body.txt > send.json
id=$(python -c 'import json; print(json.load(open("send.json"))["result"]["id"])')
ev=~/.mill/handlers/DESK_hint-cold/hint-evidence.jsonl
i=0
while [ "$i" -lt 20 ]; do
  grep -F "\"id\": $id" "$ev" >/dev/null 2>&1 && break
  i=$((i + 1))
  sleep 1
done
grep -F "\"id\": $id" "$ev" || { echo "no evidence for $id" >&2; mill route list >&2; exit 1; }
mill label mail "$id" bug
mill unlabel mail "$id" bug
mill route rm mail:MAIL
EOF
```

The letter id is `result.id` in the send JSON. The top-level `id` is the call id, not the letter. Mail is not a watcher type. `mill add mail:ID` changes recipients, not watchers. The push handed to the program is `{kind: mail, id, idem, desk}` with no `type`, `hint`, or `detail`. The route key is `mail:MAIL`.

The `grep` line is the evidence line. Remember it. `detail_kind` is `default` because a letter has no detail. Do not expect watcher crumbs on that line.

`mill label` and `mill unlabel` on that mail do not plant a watcher and do not push another letter. Do not wait for a second evidence line.

The shell then exits and the trap stops this connect. Leave every other connect running. Do not change `mill_url`.

Reply with the remembered evidence line.

`join:JOIN` and `heartbeat:PING` are dropped on receive. Do not arm them.
