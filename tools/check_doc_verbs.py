"""Fail when the docs name a mill verb or flag the CLI does not have.

The CLI parser (`agent_coord.__main__._build_parser`) is the authority: the
same object `mill VERB --help` prints from. Every `mill ...` command written
in a code span or a code block of the checked docs is read token by token:

  unknown-verb      `mill VERB` where VERB is not a verb (e.g. `mill mail`)
  unknown-sub       `mill route VERB` / `mill create TYPE` not in its choices
  unknown-flag      a `--flag` (or `-x`) the verb does not take
  missing-arg       a command in a code block with fewer positionals than the
                    verb requires (e.g. `mill connected` without a roster)
  retired-word      a retired name (RETIRED below) anywhere in the text
  bad-choice        a literal positional outside its choices (`mill install foo`)
  stale-placeholder `<project>` where the verb's positional is now a roster
  undocumented-verb a verb `mill -h` lists that no checked doc names
  undocumented-flag a flag `mill VERB -h` lists that no checked doc names
  help-*            the same command checks run on the parser's own help text

Placeholders (VERB, <verb>, ...) and bracketed forms (`[--full | --page N]`)
are read as the docs write them. A line can opt out with the marker
`doc-verbs: skip` in an HTML comment on the line itself or the line above.

Usage:
  python tools/check_doc_verbs.py          # exit 0 clean, 1 on any mismatch
  python tools/check_doc_verbs.py --list   # print every verb and its flags
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The docs a desk or a mill developer reads for verbs. Design docs that
# propose verbs or flags not built yet (NOT_CHECKED) are not checked.
DOC_GLOBS = (
    "README.md",
    "docs/*.md",
    "docs/protocol/*.md",
    "docs/protocol/models/*.md",
    "docs/protocol/models/*/*.md",
    "docs/protocol/hint-handler/*.md",
    "docs/dev/*.md",
    "docs/install/*.md",
    "docs/install/cloud/*.md",
    "docs/requirements/*.md",
    "docs/skills/*/SKILL.md",
)
NOT_CHECKED = {"docs/dev/VERB-LEXICON-PROPOSAL.md", "docs/dev/DETERMINISTIC-OFFICE.md"}

# Flags read before the parser runs (main / _run_parsed), valid on any verb.
ANY_VERB_FLAGS = {"--office", "--yes", "-h", "--help"}
# Top-level flags, valid only before the verb.
TOP_FLAGS = {"--raw", "-v", "--verbose", "-V", "--version", "--agent", "--office", "-h", "--help"}

# Names the CLI dropped. A doc that still uses one teaches a verb that is gone.
RETIRED = {
    "mill_wait": "the MCP wait tool is gone: a desk waits with mill connect + HINT or a webhook",
    "mill leftover": "removed verb: idle is mill connect + HINT",
}

# Verbs the CLI dropped; named in prose they still count as a verb.
GONE_VERBS = {"mail", "mcp", "mcp-config", "leftover", "leftover-done", "heartbeat", "sync", "done", "spend", "issues", "here", "presence", "acquire", "yield", "open"}

SKIP_MARK = "doc-verbs: skip"
PLACEHOLDER = re.compile(r"^(<[^>]*>|[A-Z][A-Z0-9_]*|\.\.\.|\u2026|VERB|verb|\$\w+|\{[^}]*\}|[A-Z_]+\.\.\.)$")
VERB_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")
FLAG_TOKEN = re.compile(r"^(--[a-z][a-z0-9-]*|-[a-zA-Z])(=.*)?$")
# A `mill` word that starts a command: not part of mill-wall, the-mill, etc.
MILL_AT = re.compile(r"(?<![\w./-])mill (?=\S)")
# Shell words that end one command.
END = {";", "&&", "||", ">", ">>", "2>", "2>&1", "&", "<", "|"}


@dataclass(frozen=True)
class Verb:
    name: str
    flags: frozenset
    takes_value: frozenset
    required: int
    positionals: tuple
    choices: tuple
    subs: dict
    parser: argparse.ArgumentParser


def _verb_of(name: str, p: argparse.ArgumentParser) -> Verb:
    flags, takes = set(), set()
    required = 0
    names = []
    choices = []
    subs: dict = {}
    for act in p._actions:
        if isinstance(act, argparse._SubParsersAction):
            subs = {n: _verb_of(n, c) for n, c in act.choices.items()}
            if act.required:
                required += 1
            continue
        if act.option_strings:
            flags.update(act.option_strings)
            if act.nargs != 0:
                takes.update(act.option_strings)
        else:
            names.append(str(act.metavar or act.dest).lower())
            choices.append(tuple(c for c in act.choices if c) if act.choices else ())
            if act.nargs in (None, "+") or isinstance(act.nargs, int):
                required += act.nargs if isinstance(act.nargs, int) else 1
    return Verb(name, frozenset(flags), frozenset(takes), required, tuple(names), tuple(choices), subs, p)


def load_verbs() -> dict:
    from agent_coord.__main__ import _build_parser

    top = _build_parser()
    for act in top._actions:
        if isinstance(act, argparse._SubParsersAction):
            return {n: _verb_of(n, c) for n, c in act.choices.items()}
    raise SystemExit("check_doc_verbs: the mill parser has no verbs")


def shown_verbs() -> set:
    """Verbs `mill -h` lists (a verb with help=SUPPRESS is hidden on purpose)."""
    from agent_coord.__main__ import _build_parser

    for act in _build_parser()._actions:
        if isinstance(act, argparse._SubParsersAction):
            return {ca.dest for ca in act._choices_actions if ca.help != argparse.SUPPRESS}
    return set()


def shown_flags(verb: Verb) -> set:
    return {
        o
        for act in verb.parser._actions
        if act.option_strings and act.help != argparse.SUPPRESS
        for o in act.option_strings
    } - {"-h", "--help", "--yes", "--office"}


def help_texts(verbs: dict):
    """(where, text) for every help and description string the parser prints."""
    from agent_coord.__main__ import _build_parser

    def walk(p, path):
        if p.description:
            yield path, p.description
        for act in p._actions:
            if isinstance(act, argparse._SubParsersAction):
                for ca in act._choices_actions:
                    if ca.help:
                        yield f"{path} {ca.dest}".strip(), ca.help
                for n, c in act.choices.items():
                    yield from walk(c, f"{path} {n}".strip())
            elif act.help and act.help != argparse.SUPPRESS:
                yield f"{path} {'/'.join(act.option_strings) or act.dest}".strip(), act.help

    yield from walk(_build_parser(), "mill")


@dataclass(frozen=True)
class Finding:
    kind: str
    where: str
    text: str
    why: str

    def line(self) -> str:
        return f"{self.where}: {self.kind}: {self.text} ({self.why})"


def doc_files(root: Path = ROOT) -> list:
    seen = []
    for pat in DOC_GLOBS:
        for path in sorted(root.glob(pat)):
            rel = path.relative_to(root).as_posix()
            if path.is_file() and rel not in NOT_CHECKED and rel not in seen:
                seen.append(rel)
    return seen


def code_pieces(text: str):
    """(line_no, piece, mode) for every code span, code block line and diagram line.

    mode is "span" (inline code), "block" (a fenced shell or text block: only a
    `mill` at a command position is a command) or "prose" (a mermaid diagram).
    """
    fence = None
    lang = ""
    skip_next = False
    for n, line in enumerate(text.split("\n"), 1):
        skip_here = SKIP_MARK in line or skip_next
        skip_next = SKIP_MARK in line and "mill " not in line.replace(SKIP_MARK, "")
        m = re.match(r"^\s*(```+|~~~+)\s*(\S*)", line)
        if m:
            if fence and line.strip().startswith(fence):
                fence = None
            elif not fence:
                fence, lang = m.group(1), m.group(2).lower()
            continue
        if skip_here:
            continue
        if fence:
            yield n, line, "prose" if lang == "mermaid" else "block", "", ""
            continue
        for span in re.finditer(r"(`+)(.+?)\1", line):
            yield n, span.group(2), "span", line[: span.start()], line[span.end() :]


def tokens_after(piece: str, start: int, prose: bool) -> list:
    """(token, depth) words of one command; depth > 0 is inside [ ] or ( )."""
    out, depth = [], 0
    for tok in re.findall(r"""'[^']*'|"[^"]*"|\S+""", piece[start:]):
        if depth == 0 and (tok in END or tok in ("/", "-->", "->", "=")):
            break
        if tok.startswith(("'", '"')):
            out.append(("POS", depth))
            continue
        last = False
        if depth == 0 and tok.endswith(("'", '"', "`", ";")):
            tok, last = tok.rstrip("'\"`;"), True
        if prose and depth == 0 and tok.endswith((",", ".", ":", ")", "]")) and not tok.startswith(("[", "<", "(")):
            tok, last = tok.rstrip(",.:)]"), True
        opened = tok.count("[") + tok.count("(")
        closed = tok.count("]") + tok.count(")")
        bare = tok.strip("[]()|,")
        if bare:
            out.append((bare, depth + (1 if opened and tok[0] in "[(" else 0)))
        depth = max(0, depth + opened - closed)
        if last:
            break
    return out


def _negated(piece: str, start: int, end: int) -> bool:
    """`no mill sync verb`, `do not run mill install`, `mill leftover: retired`,
    `mill install cloud --ssh` (planned): the line says the form is not a shipped one."""
    before = piece[max(0, start - 24) : start].lower()
    after = piece[end : end + 48].lower()
    return bool(
        re.search(r"\b(no|not|never|without)\b[^.;]*$", before)
        or re.search(r"^[^.;]{0,24}\b(retired|removed|is gone|was dropped|planned|not in this pack)\b", after)
    )


def check_command(piece: str, start: int, verbs: dict, mode: str, where: str):
    prose = mode == "prose"
    toks = tokens_after(piece, start, prose)
    i = 0
    while i < len(toks) and FLAG_TOKEN.match(toks[i][0]) and toks[i][0].split("=")[0] in TOP_FLAGS:
        i += 2 if toks[i][0] == "--office" else 1
    if i >= len(toks):
        return
    name = toks[i][0]
    if not VERB_TOKEN.match(name) or PLACEHOLDER.match(name):
        return
    rest = toks[i + 1 :]
    verb = verbs.get(name)
    if verb is None:
        # In prose `mill` is also a noun ("the mill office"): there a word is
        # read as a verb only when it is a known dropped verb or flags follow.
        if prose and name not in GONE_VERBS and not any(FLAG_TOKEN.match(t) for t, _ in rest[:2]):
            return
        yield Finding("unknown-verb", where, f"mill {name}", f"no verb {name!r}")
        return
    if verb.subs and rest:
        sub = rest[0][0]
        if VERB_TOKEN.match(sub) and not PLACEHOLDER.match(sub):
            if sub not in verb.subs:
                if not prose:
                    yield Finding(
                        "unknown-sub", where, f"mill {name} {sub}", f"{name} takes {', '.join(sorted(verb.subs))}"
                    )
                return
            verb, rest = verb.subs[sub], rest[1:]
            name = f"{name} {sub}"
    positional = 0
    j = 0
    while j < len(rest):
        tok, depth = rest[j]
        fm = FLAG_TOKEN.match(tok)
        if fm:
            flag = fm.group(1)
            if flag not in verb.flags and flag not in ANY_VERB_FLAGS:
                yield Finding("unknown-flag", where, f"mill {name} {flag}", f"{name} has no {flag}")
            elif flag in verb.takes_value and not fm.group(2):
                nxt = rest[j + 1][0] if j + 1 < len(rest) else ""
                if not FLAG_TOKEN.match(nxt):
                    j += 1
        else:
            word = tok.strip("<>").lower()
            if word == "project" and "project" not in verb.positionals:
                yield Finding(
                    "stale-placeholder", where, f"mill {name} {tok}", f"{name} takes {' '.join(verb.positionals) or 'no positional'}"
                )
            if depth == 0 and tok not in ("|", "or", "POS") or tok == "POS":
                k = positional
                if (
                    k < len(verb.choices)
                    and verb.choices[k]
                    and VERB_TOKEN.match(tok)
                    and not PLACEHOLDER.match(tok)
                    and "|" not in tok
                    and tok not in verb.choices[k]
                    and not prose
                ):
                    yield Finding("bad-choice", where, f"mill {name} {tok}", f"{name} takes {', '.join(verb.choices[k])}")
                positional += 1
        j += 1
    if mode == "block" and positional < verb.required and not verb.subs:
        yield Finding(
            "missing-arg", where, f"mill {name}", f"{name} needs {verb.required} positional, got {positional}"
        )


# A `mill` at a command position in a code block: line start, after a shell
# separator or keyword, or after `bash -c '`.
BLOCK_AT = re.compile(r"(?:^\s*(?:\$\s+|>\s+)?|(?:;|&&?|\|\|?|\(|\$\(|'|\bthen|\bdo)\s*)mill (?=\S)")


def check_text(text: str, verbs: dict, where: str, prose: bool = False):
    pieces = ((0, text, "prose", "", ""),) if prose else code_pieces(text)
    for n, piece, mode, before, after in pieces:
        loc = f"{where}:{n}" if n else where
        finder = BLOCK_AT if mode == "block" else MILL_AT
        for m in finder.finditer(piece):
            stop = piece.find("`", m.end())
            stop = len(piece) if stop < 0 else stop
            if mode == "prose":
                stop = m.end() + 24
            if _negated(before + piece + after, len(before) + m.start(), len(before) + stop):
                continue
            yield from check_command(piece, m.end(), verbs, mode, loc)


def retired(text: str, where: str):
    for n, line in enumerate(text.split("\n"), 1):
        if SKIP_MARK in line:
            continue
        for word, why in RETIRED.items():
            for m in re.finditer(rf"(?<![\w-]){re.escape(word)}(?![\w-])", line):
                if not _negated(line, m.start(), m.end()):
                    yield Finding("retired-word", f"{where}:{n}" if n else where, word, why)


def retired_in(text: str, where: str):
    for f in retired(text, ""):
        yield Finding(f.kind, where, f.text, f.why)


def run(root: Path = ROOT) -> list:
    verbs = load_verbs()
    found: list = []
    named: set = set()
    alltext: list = []
    for rel in doc_files(root):
        text = (root / rel).read_text(encoding="utf-8")
        found += list(check_text(text, verbs, rel))
        found += list(retired(text, rel))
        named.update(re.findall(r"(?<![\w./-])mill ([a-z][a-z0-9-]*)", text))
        named.update(re.findall(r"^\| `([a-z][a-z0-9-]*)` \|", text, re.M))
        alltext.append(text)
    for where, text in help_texts(verbs):
        for f in check_text(text, verbs, f"help[{where}]", prose=True):
            found.append(Finding("help-" + f.kind, f.where, f.text, f.why))
        for f in retired_in(text, f"help[{where}]"):
            found.append(Finding("help-" + f.kind, f.where, f.text, f.why))
    shown = shown_verbs()
    for name in sorted(shown):
        if name not in named:
            found.append(Finding("undocumented-verb", "docs", f"mill {name}", "in mill --help, named in no checked doc"))
    blob = "\n".join(alltext)
    for name in sorted(shown):
        for sub in [verbs[name], *verbs[name].subs.values()]:
            for flag in sorted(shown_flags(sub)):
                if not re.search(re.escape(flag) + r"(?![\w-])", blob):
                    where = f"mill {name}" + (f" {sub.name}" if sub.name != name else "")
                    found.append(Finding("undocumented-flag", "docs", f"{where} {flag}", "in --help, named in no checked doc"))
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--list", action="store_true", help="print every verb and its flags, then exit 0")
    args = ap.parse_args(argv)
    if args.list:
        def show(vs, pre=""):
            for n, v in sorted(vs.items()):
                print(f"{pre}{n} [{v.required} positional] {' '.join(sorted(v.flags - {'-h', '--help'}))}")
                show(v.subs, f"{pre}{n} ")
        show(load_verbs())
        return 0
    found = run()
    for f in found:
        print(f.line())
    kinds: dict = {}
    for f in found:
        kinds[f.kind] = kinds.get(f.kind, 0) + 1
    if found:
        print("check_doc_verbs: FAIL " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())), file=sys.stderr)
        return 1
    print(f"check_doc_verbs: ok ({len(doc_files())} docs, every mill verb and flag matches the CLI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
