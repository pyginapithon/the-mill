# Mill repo contributors (not office desks)

**Who:** people changing the-mill git (pack, mill-wall, prompts SoT). **Not** for customer office desks - those use [JOIN.md](../JOIN.md) + [skill.md](../protocol/skill.md).

Idle while dogfooding: **`mill connect`**, then HINT. Verbs: [verbs.md](../protocol/verbs.md). SoT: [tables.sql](../../agent_coord/server/sql/tables.sql) + skill.md.

- mill hold before write; mill drop after. Other desk hold -> refuse.
- `mill send desk NAME --body-file PATH` (or `--to-desk DESK`); `mill reply MAIL_ID --body-file PATH` answers in the thread. mill-wall 500 -> mail the Admin roster. SCORE is `mill score`.
- **Running the mill from a git checkout (contributors testing unreleased code):** `PYTHONPATH=<the-mill>` then `python -m agent_coord connect`. Desks and offices on the pip pack run `mill` with `PYTHONPATH` unset, so the installed pack is what runs. Check that `mill -V` matches the current pack.
- Pack / PyPI / mill update: [BUILD.md](BUILD.md).

## How to change code

Adapted from https://github.com/forrestchang/andrej-karpathy-skills (MIT), which is derived from observations on common LLM coding mistakes.

1. Think before coding. Reproduce the problem live first and write down what you saw. State assumptions; when a card can be read two ways, ask the filer before building.
2. Simplicity first. The smallest change that fixes the card. No speculative flags, aliases or layers (the mill is alpha: make hard breaks). Validate params up front and exit nonzero.
3. Surgical changes. One card, one branch, one MR. Make the smallest change at the right layer and touch only the lines it needs. When the right layer is outside the card's files (often the SQL), say so on the card, widen the scope to that layer and fix it there. Unrelated problems get a new card.
4. Goal-driven execution. Define the check before the change: an edge test that fails first and a regression matrix row per param. SQL is checked the same way: CI `pytest_sql` covers writing it, and the A/B in [HOST.md](../install/HOST.md#stored-procedures) gates only the live apply. Done means CI is green and the check passes. Steps the office repeats every time belong in code, a job or CI with a clear pass or fail; agents handle only what needs judgment.

Queries and read paths: [OPTIMIZATION.md](OPTIMIZATION.md) (filter in SQL, not in a loop; log each case you fix).

Always-on rules stay tiny. Office product skills live under [docs/skills/](../skills/).
