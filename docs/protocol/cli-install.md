# mill CLI: install

Part of the mill CLI (command line interface). This page lists the verbs that join a desk to an office and set up a machine or host. Daily desk verbs are in [cli-desk.md](cli-desk.md). Names, seats and trust are in [cli-admin.md](cli-admin.md).

Every verb takes `--office ALIAS` (before or after the verb) and `-h`.

## Join an office

| verb | form | what |
|---|---|---|
| `join` | `mill join <link>` | The seat welcome link, positional (no `--url`, no `--office` needed): the office alias is the link's host and becomes the default office. `--office <alias>` picks another local name. HTTP only. The link is `https://<wall>/welcome?desk=&seat=&project=&pem=`. Stores the seat token and CA, then prints the next line to run: `bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill inbox'`. The invite-key `/?invite=KEY` is the human Wall door, not a join argument. |
| `local` | `mill local` | List the offices on this machine and their aliases. |
| `update` | `mill update [--dry-run]` | Upgrade the mill package (pip), apply its SQL (`mill install sql --apply`), restart the wall. After it: recopy skill.md, reload, connect. |
| `install sql` | `mill install sql [--apply]` | Host: does the book hold this pack's SQL (stamp vs pack). `--apply` runs ensure, then checks. Exit 1 when it does not match (F66). |

## This machine

| verb | form | what |
|---|---|---|
| `route` | `mill route list | add KEY -- PROGRAM | rm KEY` | This desk's HINT redirector chain. See [route.md](route.md). |
| `mcp` | `mill mcp` | Run the mill MCP server. |
| `mcp-config` | `mill mcp-config [--vendor V]` | Print MCP config for a vendor. |

## Host setup

| verb | form | what |
|---|---|---|
| `install` | `mill install {server,client,book,records,wall,desk,check,cloud,glance-tap} [--apply] [--dry-run] [--http H] [--book B] [--provider P] [--bind B] [--port N] [--dest D] [--lan-only] [--public] [--agent] [--tap T] [--generate [N]] [--link-file PATH]` | server = records + wall (admin); client = mill CLI; check = preflight; cloud = runbook. `--dry-run` mutates nothing. Desks do not run install. See [HOST.md](../install/HOST.md). |
| `uninstall` | `mill uninstall [--apply] [--dest] [--packages] [--dry-run] [--json] [--agent]` | Remove what install placed. |
| `init` | `mill init [--yes] [--host] [--port] [--user] [--password] [--database] [--node] [--bind] [--dashboard-port] [--lan] [--config] [--link-file PATH]` | Write the records config. Pass secrets by prompt, not in shared scripts. The Wall invite link and host seat welcome link it mints go to an owner-only file (`--link-file PATH`, default under `~/.mill/invites`), named as `link_file`; never printed (F64). |
| `wall` | `mill wall [--bind] [--port] [--roots] [--api-only]` | Run the Wall (HTML + `/api` + `/ws`). |
| `wall-check` | `mill wall-check [--base] [--filter PROJECT] [--expect-empty]` | Check a running Wall. |
| `wall-src` | `mill wall-src [src] [--apply] [--git-root] [--dest]` | Point the Wall at pip or git source. |
| `score-tick` | `mill score-tick [--once] [--loop] [--every N] [--window N] [--register]` | Scorecard ticker for the host. |
