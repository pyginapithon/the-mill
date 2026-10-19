# Copilot code review instructions

Review for correctness and safety first; style last. Contributor rules are in
docs/dev/AGENTS.md; query and hot-path rules are in docs/dev/OPTIMIZATION.md.

Flag:

- Personal identifiers in code, docs, tests, fixtures or commit text: real
  names, home directory paths, IP addresses, email addresses (other than
  noreply addresses). Docs describe roles, not people.
- Credentials of any kind: tokens, passwords, keys, tokens in URLs or git
  config, or code that prints, logs or echoes a secret.
- Regressions in authorization, join gating or redaction: a verb that skips a
  permission check, widens who can read or join, or returns fields that were
  redacted before.
- SQL safety: string-built queries instead of bound parameters, unbounded
  reads, and migrations that are not forward-safe or lack a test.
- Performance on hot paths: N+1 queries, rows fetched and filtered in code,
  repeated reads of the same data in one request, new indexes on hot write
  tables without a measured win (see OPTIMIZATION.md).
- Tests that only exercise code without asserting behavior, or that were
  weakened to make a change pass.
- Drive-by reformatting or unrelated edits mixed into a focused change.
- Back-compat shims, deprecation aliases or fallback paths. The mill is
  alpha: change callers directly and remove the old path.

Do not flag:

- Formatting the linters already enforce.
- ASCII-only wording in docs; that is intended.

Keep comments short and specific, with the file and line and a suggested fix.
