# Contributing to the mill repo: pull requests

This is for agents and people who change the mill git tree. Mill users
(JOIN, skill, desk speech) are not affected and do not need this.

The repo lives on GitHub: `https://github.com/pyginapithon/the-mill`.
The old GitLab project is a read-only archive; do not open merge requests
there.

`main` is protected by a ruleset: no direct pushes, no force pushes, no
deletion, linear history, and every change lands through a pull request
(PR) whose required checks are green. Version bumps too.

## Steps

0. Once per checkout, turn on the repo hooks:

       git config core.hooksPath .githooks

   `pre-commit` runs `tools/precommit_hygiene.py staged` on the staged
   blobs (the index, not the working tree): addresses, home paths with a
   login name, emails outside placeholder domains, typographic marks, and
   Title-case name tokens in comments, docstrings and Markdown prose.
   `commit-msg` runs the same rules on the message. Each hit names
   `file:line` and the kind. Words that are ordinary elsewhere in the tree,
   or listed in `tools/hygiene_words.txt`, are not names. In a commit
   message that holds for the first word of a line (sentence case, also
   after a bullet, a list number or a card number); a capital mid-line
   still has to be on the desk-word allow-list. `check_pack` applies the
   same rule to commit history. Regression row F49 (hook-linestart).
   The hooks find the repo from their own path, so running one by hand
   from any directory gives the same verdict, and a scan that cannot run
   exits 1 with `hygiene ERROR` (it fails closed). The hooks need
   `python3`, `python` or `py` on PATH (Git Bash on Windows is fine).
   `git commit --no-verify` skips them; CI `check_pack` still fails the PR.
   `python tools/precommit_hygiene.py tree` runs the comment scan over the
   whole tip.

1. Start from a fresh `main`:

       git fetch origin
       git switch -c fix/223-short-slug origin/main

   One branch per change. Name it after the card: `fix/<card>-<slug>`
   (or `feat/`, `docs/`, `speech/` when that fits better).

2. Commit. Every commit message cites the card, e.g.
   `#223 Skip login name box in local-name scan`. Commit with a role
   identity and a noreply address, never a personal email.
   Run the local hygiene first: `python tools/check_pack.py dist` after
   `python -m build`, plus the tests you touched.

3. Push the branch and open the PR:

       git push -u origin fix/223-short-slug

   Then open the PR against `main` in the GitHub web UI (git prints the
   link), or with the GitHub CLI if your seat has it:

       gh pr create --base main --fill

   Authenticate the CLI or git with the desk's own token from its
   credential file (a credential helper or `gh auth login --with-token`).
   Never paste a token into chat, mail, a URL, a file in the repo or a
   commit.

4. CI must pass. The required checks are the `ci` jobs `build_pack`,
   `check_pack` (hygiene and pip-audit), `mill_cli_smoke`,
   `pytest_no_sql`, `pytest_sql`, and the CodeQL jobs `analyze (python)`
   and `analyze (actions)`. A red PR is not reviewed. A PR from a fork
   runs CI only after a maintainer approves the run.

5. Tell Builder the PR number in the card's thread. Builder reviews and
   merges with squash or rebase (merge commits are off, so history stays
   linear). The head branch is deleted on merge. Do not merge your own PR.
   Copilot code review runs on each PR and push; its comments are advisory.
   The author addresses or answers each one, and Builder still merges.

   Merges must keep noreply identities. A web merge (squash or rebase)
   stamps the merging account's commit email on the result, so every
   account that merges keeps GitHub email privacy on ("Keep my email
   addresses private" and "Block command line pushes that expose my
   email"). `check_pack` fails on main if a personal address lands anyway;
   fixing that is a history rewrite the human office owner approves.

6. If Builder asks for a rebase:

       git fetch origin
       git rebase origin/main
       git push --force-with-lease

   Force-push only your own branch. Never force-push `main` or another
   desk's branch.

## Moving an old branch that carries commits main already has

If your branch was cut from an old `main` (or carries commits that are
already merged), do not open the PR from it. Make a fresh branch and take
only your own commits:

    git fetch origin
    git cherry -v origin/main old-branch
    git switch -c fix/<card>-<slug> origin/main
    git cherry-pick <sha> [<sha>...]

`git cherry -v` marks with `+` the commits main does not have yet (yours
to keep) and with `-` the ones already on main (skip them). Cherry-pick
only the `+` commits. Or squash the whole diff into one commit:

    git switch -c fix/<card>-<slug> origin/main
    git checkout old-branch -- <paths you changed>
    git commit -m "#<card> ..."

Check that `git cherry -v origin/main fix/<card>-<slug>` lists only your
commits, then push the new branch and open the PR as in step 3.

## Dependabot

Dependabot opens version-update PRs from `.github/dependabot.yml` and
security-update PRs. They run the same checks. Its commits carry a fixed
sign-off trailer that `check_pack` accepts exactly (regression row S-8).
Ask it to rebase with a PR comment `@dependabot rebase`.

## Kept by Builder

- Version bumps (also through a PR, merged by Builder).
- Collecting ship GO consensus (BUILD.md, CI ship path) and the GO to the shipper.
- Merging to `main`.

## A refused push to main

A direct push to `main` fails with a ruleset error like this:

    remote: error: GH013: Repository rule violations found for refs/heads/main.
    ! [remote rejected] main -> main (push declined due to repository rule violations)

Nothing is lost. Move the commits to a branch and open a PR:

    git switch -c fix/<card>-<slug>
    git push -u origin fix/<card>-<slug>
    git switch main && git reset --hard origin/main
