"""Pre-commit hygiene for the mill repo (card #230).

Usage:
  python tools/precommit_hygiene.py staged          # scan index blobs
  python tools/precommit_hygiene.py msg FILE        # scan a commit message
  python tools/precommit_hygiene.py tree            # comment scan, whole tip

Uses the tools/check_pack.py rules: non-documentation address, home path
with a login segment, email outside placeholder domains, byte-order mark,
typographic marks, and (in comments, docstrings, Markdown prose and the
commit message) the Title-case name-token rule with the desk-word
allow-list. Staged files are read from the index (git show :path), never
the working tree. Reports file:line and the kind; never the matched text.

Hooks: git config core.hooksPath .githooks (once per checkout).
Bypass: git commit --no-verify. CI check_pack still runs every rule.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pack as cp  # noqa: E402

_HASH_SUFFIXES = frozenset(
    {".sh", ".ps1", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".gitignore", ".gitattributes"}
)
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_SENT_START_RE = re.compile(r"(?:^|[.!?:;]\s+|^\s*[-*>#\d.)]+\s*)([A-Z][a-z]{2,20})\b")
# Word-ish things that are not prose: paths, dotted names, snake/camel case.
_NOT_PROSE_RE = re.compile(r"\S*[/\\_=@$<>{}\[\]]\S*|\w+\.\w+\S*")


_WORDS_FILE = Path(__file__).resolve().parent / "hygiene_words.txt"
_LOWER_RE = re.compile(r"\b[a-z]{3,21}\b")
_VOCAB: set[str] | None = None


def tree_vocab() -> set[str]:
    """Lower-case words used anywhere in the HEAD tree, plus hygiene_words.txt.

    A Title-case comment word that is an ordinary word elsewhere in the repo
    is prose, not a name. A name never appears lower-case, so it still fails.
    """
    global _VOCAB
    if _VOCAB is not None:
        return _VOCAB
    words: set[str] = set()
    try:
        raw = _git("grep", "-h", "-o", "-w", "-I", "-E", "[a-z]{3,21}", "HEAD", "--", ".")
        words.update(_LOWER_RE.findall(raw.decode("utf-8", "replace")))
    except (OSError, subprocess.CalledProcessError):
        pass
    try:
        for ln in _WORDS_FILE.read_text(encoding="utf-8").splitlines():
            ln = ln.split("#", 1)[0].strip()
            if ln:
                words.add(ln.casefold())
    except OSError:
        pass
    _VOCAB = words
    return words


def name_hit(text: str, vocab: set[str] | None = None) -> bool:
    """#229 rule for comment prose. Skips code spans and sentence-start words."""
    if vocab is None:
        vocab = tree_vocab()
    text = _CODE_SPAN_RE.sub(" ", text)
    text = _NOT_PROSE_RE.sub(" ", text)
    starts = {m.start(1) for m in _SENT_START_RE.finditer(text)}
    for m in cp._NAME_TOKEN_RE.finditer(text):
        if m.start() in starts:
            continue
        word = m.group(0).casefold()
        if word not in cp.DESK_WORD_ALLOWLIST and word not in vocab:
            return True
    return False


def comment_lines(rel: str, text: str) -> list[tuple[int, str]]:
    """(line, prose) for comments, docstrings and Markdown prose."""
    name = rel.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    suffix = Path(name).suffix
    out: list[tuple[int, str]] = []
    if suffix in (".py", ".pyi"):
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT:
                    out.append((tok.start[0], tok.string.lstrip("#")))
                elif tok.type == tokenize.STRING and re.match(r"^[rRuUbBfF]*('''|\"\"\")", tok.string):
                    for i, ln in enumerate(tok.string.splitlines()):
                        out.append((tok.start[0] + i, ln.strip("\"' rRuUbBfF") if i == 0 else ln))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            for i, ln in enumerate(text.splitlines(), 1):
                if "#" in ln:
                    out.append((i, ln.split("#", 1)[1]))
        return out
    lines = text.splitlines()
    if suffix == ".sql":
        for i, ln in enumerate(lines, 1):
            if "--" in ln:
                out.append((i, ln.split("--", 1)[1]))
    elif suffix in _HASH_SUFFIXES or name in (".gitlab-ci.yml", "makefile", "dockerfile") or (lines and lines[0].startswith("#!")):
        for i, ln in enumerate(lines, 1):
            s = ln.lstrip()
            if s.startswith("#") and not s.startswith("#!"):
                out.append((i, s.lstrip("#")))
    elif suffix in (".md", ".markdown", ".rst", ".txt"):
        fence = False
        for i, ln in enumerate(lines, 1):
            if ln.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            if fence or ln.startswith(("    ", "\t")):
                continue
            out.append((i, ln))
    return out


def scan_text(rel: str, blob: bytes) -> list[str]:
    fails: list[str] = []
    if Path(rel).suffix.lower() in cp.BINARY_SUFFIXES or b"\0" in blob[:8000]:
        return fails
    text = blob.decode("utf-8", "replace")
    if cp._is_text_file(rel) and blob.startswith(cp._BOM_PREFIXES):
        fails.append(f"{rel}:1: byte-order mark")
    for i, ln in enumerate(text.splitlines(), 1):
        if cp.text_has_forbidden_address(ln):
            fails.append(f"{rel}:{i}: non-documentation address")
        if cp.text_has_personal_home_path(ln):
            fails.append(f"{rel}:{i}: home path with a login name")
        if cp.text_has_personal_email(ln):
            fails.append(f"{rel}:{i}: email outside placeholder domains")
        if cp._is_text_file(rel):
            mark = cp.text_mark(ln)
            if mark is not None:
                fails.append(f"{rel}:{i}: typographic mark U+{mark:04X}")
    for i, prose in comment_lines(rel, text):
        if name_hit(prose):
            fails.append(f"{rel}:{i}: personal name token in a comment")
    return fails


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)


def scan_staged() -> list[str]:
    raw = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    fails: list[str] = []
    for rel in raw.decode("utf-8", "replace").split("\0"):
        if not rel:
            continue
        if cp.text_has_forbidden_address(rel) or cp.text_has_personal_home_path(rel):
            fails.append(f"{rel}: address or home path in the file path")
        fails.extend(scan_text(rel, _git("show", f":{rel}")))
    return fails


def scan_tree() -> list[str]:
    raw = _git("ls-files", "-z")
    fails: list[str] = []
    for rel in raw.decode("utf-8", "replace").split("\0"):
        if not rel:
            continue
        try:
            text = _git("show", f"HEAD:{rel}").decode("utf-8", "replace")
        except subprocess.CalledProcessError:
            continue
        for i, prose in comment_lines(rel, text):
            if name_hit(prose):
                fails.append(f"{rel}:{i}: personal name token in a comment")
    return fails


def scan_message(path: str) -> list[str]:
    body = Path(path).read_text(encoding="utf-8", errors="replace")
    # Git template lines are "# ..." (hash, space); card subjects are "#230 ...".
    kept: list[str] = []
    for ln in body.splitlines():
        if ln.startswith("# ------------------------ >8"):
            break
        kept.append("" if ln == "#" or ln.startswith("# ") else ln)
    body = "\n".join(kept)
    fails: list[str] = []
    for i, ln in enumerate(body.splitlines(), 1):
        if cp.text_has_forbidden_address(ln):
            fails.append(f"commit message:{i}: non-documentation address")
        if cp.text_has_personal_home_path(ln):
            fails.append(f"commit message:{i}: home path with a login name")
        if cp.text_has_personal_email(ln):
            fails.append(f"commit message:{i}: email outside placeholder domains")
        if cp.text_has_personal_name_token(ln):
            fails.append(f"commit message:{i}: personal name token (#229 rule)")
    return fails


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("staged", "msg", "tree") or (argv[0] == "msg" and len(argv) < 2):
        print(__doc__.strip())
        return 2
    if argv[0] == "staged":
        fails = scan_staged()
    elif argv[0] == "msg":
        fails = scan_message(argv[1])
    else:
        fails = scan_tree()
    if fails:
        print(f"hygiene FAIL: {len(fails)} hit(s)", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        print("Fix the lines above. Bypass only with git commit --no-verify; CI check_pack still fails it.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
