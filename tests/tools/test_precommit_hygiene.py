"""#230 pre-commit hygiene hooks: index blobs and the commit message."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import precommit_hygiene as ph  # noqa: E402

# Built at runtime so this file stays clean under check_pack.
HOME_PATH = "/ho" + "me/zorbin/notes.txt"
EMAIL = "zorbin" + "@" + "corp-mail.co"
NAME = "Zor" + "bin"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=check
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    r = tmp_path / "r"
    (r / "tools").mkdir(parents=True)
    for name in ("check_pack.py", "precommit_hygiene.py", "hygiene_words.txt"):
        shutil.copy(ROOT / "tools" / name, r / "tools" / name)
    shutil.copytree(ROOT / ".githooks", r / ".githooks")
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "desk@users.noreply.gitlab.com")
    _git(r, "config", "user.name", "desk")
    (r / "base.md").write_text("Plain words about the mill and a desk.\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "#230 Seed the repo")
    _git(r, "config", "core.hooksPath", ".githooks")
    ph._VOCAB = None
    return r


def _commit(repo: Path, msg: str = "#230 Add a file") -> subprocess.CompletedProcess:
    return _git(repo, "commit", "-q", "-m", msg, check=False)


def test_staged_home_path_fails_with_file_line(repo: Path) -> None:
    (repo / "a.txt").write_text("ok\nsee " + HOME_PATH + "\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    res = _commit(repo)
    assert res.returncode != 0
    assert "a.txt:2: home path with a login name" in res.stderr
    assert "zorbin" not in res.stderr


def test_staged_email_fails(repo: Path) -> None:
    (repo / "b.txt").write_text("mail " + EMAIL + "\n", encoding="utf-8")
    _git(repo, "add", "b.txt")
    res = _commit(repo)
    assert res.returncode != 0
    assert "b.txt:1: email outside placeholder domains" in res.stderr


def test_clean_staged_file_passes(repo: Path) -> None:
    (repo / "c.py").write_text(
        "# Keep the desk hold until the mill sync.\nx = 1  # see desk@example.com\n",
        encoding="utf-8",
    )
    _git(repo, "add", "c.py")
    res = _commit(repo)
    assert res.returncode == 0, res.stderr


def test_unstaged_dirty_file_not_scanned(repo: Path) -> None:
    (repo / "d.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "d.txt")
    (repo / "d.txt").write_text("dirty " + HOME_PATH + "\n", encoding="utf-8")
    (repo / "loose.txt").write_text(EMAIL + "\n", encoding="utf-8")
    res = _commit(repo)
    assert res.returncode == 0, res.stderr


def test_index_blob_scanned_even_if_worktree_clean(repo: Path) -> None:
    (repo / "e.txt").write_text("dirty " + HOME_PATH + "\n", encoding="utf-8")
    _git(repo, "add", "e.txt")
    (repo / "e.txt").write_text("clean\n", encoding="utf-8")
    assert _commit(repo).returncode != 0


def test_commit_message_prose_name_fails(repo: Path) -> None:
    (repo / "f.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "f.txt")
    res = _commit(repo, f"#230 Fix the hold as {NAME} asked")
    assert res.returncode != 0
    assert "commit message:1: personal name token" in res.stderr


def test_py_comment_name_fails(repo: Path) -> None:
    (repo / "g.py").write_text(f"x = 1\n# Per {NAME}'s request, keep it\n", encoding="utf-8")
    _git(repo, "add", "g.py")
    res = _commit(repo)
    assert res.returncode != 0
    assert "g.py:2: personal name token in a comment" in res.stderr


def test_py_docstring_name_fails(repo: Path) -> None:
    (repo / "h.py").write_text(f'def f():\n    """Return the row the way {NAME} wants."""\n', encoding="utf-8")
    _git(repo, "add", "h.py")
    assert "h.py:2:" in _commit(repo).stderr


def test_sql_comment_name_fails(repo: Path) -> None:
    (repo / "i.sql").write_text(f"SELECT 1; -- asked by {NAME}\n", encoding="utf-8")
    _git(repo, "add", "i.sql")
    res = _commit(repo)
    assert res.returncode != 0
    assert "i.sql:1: personal name token in a comment" in res.stderr


def test_desk_words_and_identifiers_pass(repo: Path) -> None:
    (repo / "j.py").write_text(
        "# Builder and Gardener hold the Mill desk; see MillClient.\n"
        "class MillClient:  # Windows and Linux\n    pass\n",
        encoding="utf-8",
    )
    (repo / "k.sql").write_text("-- Return the Wall rows for the desk\nSELECT 1;\n", encoding="utf-8")
    _git(repo, "add", "j.py", "k.sql")
    res = _commit(repo, "#230 Add the Builder desk notes")
    assert res.returncode == 0, res.stderr


def test_code_name_is_not_a_comment() -> None:
    assert ph.comment_lines("x.py", f"{NAME} = 1\n") == []


def test_name_hit_skips_sentence_start_and_code_spans() -> None:
    assert not ph.name_hit("Keep it. Ordinary words only", vocab={"ordinary"})
    assert not ph.name_hit(f"see `{NAME}` here", vocab=set())
    assert ph.name_hit(f"ask {NAME} first", vocab=set())


@pytest.fixture()
def empty_repo(tmp_path: Path) -> Path:
    """A repo before its first commit (an orphan or fresh root): no HEAD yet."""
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    r = tmp_path / "root"
    (r / "tools").mkdir(parents=True)
    for name in ("check_pack.py", "precommit_hygiene.py", "hygiene_words.txt"):
        shutil.copy(ROOT / "tools" / name, r / "tools" / name)
    shutil.copytree(ROOT / ".githooks", r / ".githooks")
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "desk@users.noreply.gitlab.com")
    _git(r, "config", "user.name", "desk")
    _git(r, "config", "core.hooksPath", ".githooks")
    ph._VOCAB = None
    return r


def test_root_commit_reads_words_from_the_staged_tree(empty_repo: Path) -> None:
    """With no HEAD, an ordinary word is still known from the staged files."""
    word = "zeppel" + "inade"
    (empty_repo / "a.md").write_text(
        f"the desk keeps a {word} log.\n\nthe desk reads {word.title()} notes.\n",
        encoding="utf-8",
    )
    _git(empty_repo, "add", "a.md")
    res = _commit(empty_repo, "initial public import")
    assert res.returncode == 0, res.stderr


def test_root_commit_still_fails_on_a_name(empty_repo: Path) -> None:
    (empty_repo / "a.md").write_text(f"the desk asks {NAME} for notes.\n", encoding="utf-8")
    _git(empty_repo, "add", "a.md")
    res = _commit(empty_repo, "initial public import")
    assert res.returncode != 0
    assert "a.md:1: personal name token" in res.stderr
