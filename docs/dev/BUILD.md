# Build the mill pip pack

This is for people who **change mill** (the git tree). App users do not build - they `pip install the-mill`.

Do not pin mill versions in docs.

## Release order

Assume **regression tests already pass**. Then:

1. **Local hygiene** - bump version, `python -m build`, `python tools/check_pack.py dist`, `python tools/mill_cli_smoke.py` (install the **tarball** from a non-git cwd). Human pass on tracked `.md` / `.txt`. Do not push a dirty `dist/`.
2. **Commit** the version bump + hygiene fixes.
3. **Push** through a merge request: `main` is protected, see [CONTRIBUTING-MR.md](CONTRIBUTING-MR.md).
4. **Pipeline** - wait for GitLab `build_pack` -> `check_pack` -> `mill_cli_smoke` -> `pytest_no_sql` and `pytest_sql` (and pip-audit). `pytest_no_sql` installs Node.js, runs `npm ci --prefix tools/wall-validators` so stylelint, eslint, and html-validate check the wall files, then runs `pytest tests -m "not sql"`. `pytest_sql` starts MySQL 8.4 beside the job and runs `pytest tests -m sql`, with `AGENT_COORD_HOST=mysql`. SQL suites use per-process throwaway DB names (`tests/sql_isolate.py`) so concurrent local runners cannot wipe a shared mill_records_test. Branch and `main` pipelines do **not** publish.
5. **If pipeline GO** - after ship GO consensus at the exact sha (see [CI ship path](#ci-ship-path)), push an annotated tag `v<version>` on that sha (`git tag -a`). The tag pipeline reruns every job, then `release_pypi` uploads the same wheel + sdist it scanned. See [CI ship path](#ci-ship-path).
6. **`mill update`** - from a **non-git cwd**: stop mill-wall and wait until it is STOPPED, then `pip install -U the-mill` (or `mill update`), then start mill-wall. Do not pip while mill-wall is still running (`sc stop` on Windows returns at STOP_PENDING; wait for STOPPED). Refuse the install when another process is `mill connect` holding `Scripts\mill.exe`; stop that connect first. The installer does not kill it. After pip, import the package and the ASGI app before starting mill-wall. If pip or that import fails, leave mill-wall stopped. `mill -V` is the installed mill. A live office book does not pick up new stored procedures from that recycle. Apply them on the host as in [HOST.md](../install/HOST.md#update-a-running-host). Wall serve + MySQL pool/gzip/cache and what recycle vs SQL apply means: [HOST.md mill-wall and MySQL](../install/HOST.md#mill-wall-and-mysql-operator-config). The pipeline does not touch a customer book. **Gate:** the A/B in [HOST.md](../install/HOST.md#stored-procedures) gates a live SQL apply (lan or aws); CI `pytest_sql` covers writing the SQL.
7. **skill.md** - copy the pack's `docs/protocol/skill.md` (`mill join` prints its path after `skill`) over the desk's mill-desk `SKILL.md`, then **restart the TUI**. `python tools/check_skill_copy.py PATH` exits 0 when that copy matches the source; CI runs it with `--installed` on the pack (regression row F33, skill-copy). `mill briefing skill` is a terminal rendering, not a copy. mill on PATH is not the skill.

Git mill on this checkout uses `PYTHONPATH` / `pack_local.py --install`, not `mill update` from the repo root. Never `pip install .` from the git tree.

## What you produce

From the repo root:

```
python -m pip install build
python -m build
```

That writes two files under `dist/`:

- `the_mill-<version>-py3-none-any.whl` - what most `pip install` users get
- `the_mill-<version>.tar.gz` - the source tarball (`pip` can unpack this too)

Neither file starts mill-wall or MySQL. They only install the mill package (`mill` on PATH). The pack includes FastAPI/uvicorn so mill-wall can run after `pip install`.

Use the tarball, not only the wheel. If the tarball is dirty, a source install is dirty.

## Local pack (no PyPI)

Office dogfood **without** steps 3-5. After a commit:

```
python tools/pack_local.py
python tools/pack_local.py --install --notify
```

`--install` pip-installs the tarball from a non-git cwd. `--notify` mails the build-validator desk a local-pack note (`mill send desk build-validator --roster the-mill --body-file FILE`): re-measure, dry-run only. Regression row F32 (pack-local-notify): `tests/tools/test_pack_local_notify.py` parses that command with the mill parser. Does not `twine upload`. Recycle mill-wall after `--install`. Still recopy skill.md if the briefing changed.

## What must not be in either artifact

`tools/check_pack.py` is fail-closed on both the wheel and the sdist. Unpack both and fail if you find:

- backups (`.bak`, `.bak-*`)
- bytecode (`__pycache__`, `.pyc`)
- `wall_ui_save/` (local Wall dumps; gitignored, must not ship)
- surprise binaries under `agent_coord/`
- home-path prefixes (`C:\Users\`, `C:/Users/`, `/Users/`, `/home/`)
- emails outside the placeholder domains (`example.com/.org/.net`, `.example`, `.test`, `.invalid`, `.localhost`, GitLab and GitHub noreply); the project local-part `pyginapithon` and `git@` SSH remotes pass
- tokens
- office dest dumps or Wall diary scrapes
- a complete IP that is not a documentation address. Documentation ranges are RFC 5737 (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) and RFC 3849 (`2001:db8::/32`). Loopback (`127.0.0.0/8`, `::1`) and unspecified (`0.0.0.0`, `::`) may stay. LAN *prefix* `192.168.1.` / `192.168.1.%` / `192.168.1.*` is mill join product and is not a complete host. The same rule covers the wheel, the sdist, git-tracked files (including comments), and git commit messages
- a Windows editor mark in a text file in the wheel, the sdist, or git. Text means source and docs (`.py`, `.md`, `.sql`, `.js`, `.css`, `.html`, `.ps1`, `.sh`, `.toml`, `.yml`, `.json`, `.svg`, `.txt`, and the same kind of file). Images, fonts, and other binaries are not decoded for this scan. The mark is a leading byte-order mark (UTF-8 `EF BB BF`, or UTF-16 `FF FE` / `FE FF`) or one of these code points: U+FEFF, U+00A0, U+00B1, U+00B7, U+0394, U+200B, U+200C, U+200D, U+2013, U+2014, U+2018, U+2019, U+201C, U+201D, U+2026, U+2190 through U+2193, U+2264, U+2713. PowerShell `Set-Content -Encoding utf8` writes U+FEFF. The report is the code point and the path, not the glyph. The ASCII escape for U+FEFF may stay: that is how `mill send` strips a file-body mark. Old commit messages are not scanned for these marks
- `Sudoku` leftover under `agent_coord/`

The scanner reports *that* a home path, email, local home-user, or non-documentation address hit, not the matched substring.

**Local extra:** profile folder names from `C:\Users`, `/home` (Linux/WSL), `/Users` (macOS), and `wsl.exe ls /home` when check_pack runs on Windows with WSL. The same net includes the computer name and hyphenated office-alias filenames under the local mill home. A plain alias with no hyphen is not part of this net. Case-insensitive word-boundary scan of **wheel + sdist**, **`git ls-files`**, and commit messages. GitLab shows tracked `docs/dev/` even when not in the wheel. Documented prefixes (`C:\Users\`, `/home/`) in BUILD.md are allowed; a **login name**, computer name, or hyphenated office alias in a tracked file fails. Names are read from disk - not a word-list in `check_pack.py`. **GitLab CI skips** this net (`GITLAB_CI` / `CI=true`) so the runner login is not scanned. Skip Public / Default / Administrator / root / Guest / Shared. The address scan is not part of that skip. It runs on the wheel, the sdist, `git ls-files`, and commit messages in CI too.

`wall.local` in install/TLS copy is the product cert hostname. That stays.

`tests/` may appear in the tarball (repo/dev). They must not appear in the wheel. A `Sudoku` hit under `tests/` is a note, not a fail. A non-documentation address under `tests/` fails.

## Pack recipe (so junk cannot sneak back)

`pyproject.toml` must:

- include only product data: `static/*`, `schema.sql`, `scripts/*`, `wall_ui` `*.html` / `*.css` / `*.js` / `*.md`, and mill briefing markdown (`README.md`, `docs/JOIN.md`, `docs/HOST.md`, `docs/skills/**` (office adapters; not `docs/dev/`)
- exclude `__pycache__`, `*.pyc`, `*.bak`, `*.bak-*`, `*.orig`, `*~`
- prune `agent_coord/web/wall_ui_save` (`MANIFEST.in`)

Delete leftover backups and `__pycache__` from the tree **before** `python -m build`. The exclude list is backup; a dirty tree can still leak into the tarball.

## Pipeline hygiene

`.gitlab-ci.yml` publishes only from `release_pypi` on a `v*` tag. Its `workflow:` rules run one pipeline per push: the merge request pipeline for a branch with an open MR, the default branch after a merge or direct push, and tags. A branch with no open MR runs no pipeline. On every pipeline:

1. `build_pack` - `python -m build` -> `dist/`
2. `check_pack` - `python tools/check_pack.py dist`, then `pip-audit` on pack deps
3. `mill_cli_smoke` - install the sdist, run `python tools/mill_cli_smoke.py` (`mill -V`, `mill connect --help`, no retired verbs on `--help`, and the real-path rows in `RUN_ROWS`: `mill connect` runs its whole body against a closed local port and must reach the socket loop with no traceback)
4. `pytest_no_sql` and `pytest_sql` - the test suites (see step 4 of Release order)
5. `release_pypi` - on a `v*` tag only, after the jobs above pass

Same scanner locally (step 1 of Release order): `python tools/check_pack.py dist`.

## CI ship path

The release ships from GitLab CI, not from an office host.

1. The version bump is merged on `main` and the pipeline on that sha is green.
2. Ship GO consensus on that exact sha: each desk your office assigns to the builder, validator and shipper roles sends GO naming the sha. A silent desk is not a GO; there is no timeout and no quorum. A NOGO blocks. When desks are unavailable or a NOGO is stuck, the human office owner judges and may override.
3. Push an annotated tag `v<version>` (same as `pyproject.toml`) on that sha: `git tag -a v<version> -m "the mill <version>" <sha>`, then `git push origin v<version>`. An annotated tag records who tagged and when; a lightweight tag does not.
4. The tag pipeline runs `build_pack`, `check_pack`, `mill_cli_smoke`, `pytest_no_sql`, `pytest_sql`, then `release_pypi`.
5. `release_pypi` refuses if `PYPI_API_TOKEN` is unset, if `dist/` is not exactly `the_mill-<version>` wheel + sdist, if `tools/check_pack.py dist` fails, or if `twine check` fails. Then it runs `twine upload dist/*` with `TWINE_USERNAME=__token__`.
6. Hosts then update from PyPI as in step 6 of Release order.

Setup, once per project:

- CI/CD variable `PYPI_API_TOKEN`: a PyPI API token scoped to the `the-mill` project. Flags: Protected, Masked (and hidden). Environment scope `*`. Never put the token in a commit, doc, card or mail.
- Protected tag rule `v*` so only maintainers can push it and the protected variable is exposed to the tag pipeline.

A failed upload leaves PyPI unchanged for that file; fix and rerun the job. PyPI never accepts the same version twice, so a bad release needs a new version and tag.

## Allowlist vs gitignore

`.gitignore` is a denylist (skip these). The wheel allowlist is the opposite: only expected paths may ship. Changing the allowlist is a visible git diff. The pack pipeline is what enforces it.
