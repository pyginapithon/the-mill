"""Pack hygiene: home paths, emails, addresses, and commit-message name tokens.

Every fixture is invented placeholder data. Forbidden shapes are assembled at
run time so this file itself stays clean under the git-tip scan.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _mod():
    spec = importlib.util.spec_from_file_location("check_pack", ROOT / "tools" / "check_pack.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _j(*parts: str) -> str:
    return "".join(parts)


BS = "\\"
LOGIN = _j("fixture", "login")


def test_home_path_with_login_fails() -> None:
    mod = _mod()
    for text in (
        _j("C:", BS, "Users", BS, LOGIN, BS, "mill"),
        _j("c:", BS, BS, "users", BS, BS, LOGIN),
        _j("C:/Users/", LOGIN, "/AppData"),
        _j("/", "home", "/", LOGIN, "/.mill"),
        _j("/", "Users", "/", LOGIN, "/Library"),
        _j('path = "/', 'home/', LOGIN, '"'),
    ):
        assert mod.text_has_personal_home_path(text), text


def test_home_path_placeholders_pass() -> None:
    mod = _mod()
    for text in (
        "C:\\Users\\<user>\\.mill",
        "C:\\Users\\example\\.mill",
        "C:/Users/<you>/AppData",
        "C:\\Users\\%USERNAME%\\.mill",
        "C:\\Users\\$env:USERNAME",
        "C:\\Users\\",
        "C:\\Users\\...",
        "/home/<user>/.mill",
        "/home/example/.mill",
        "/home/$USER/.mill",
        "/home/${USER}/.mill",
        "/home/*",
        "/Users/<user>/Library",
        "under /home/ on Linux",
        "https://docs.example.com/home/intro",
        "~/.mill/home/desk",
        "",
    ):
        assert not mod.text_has_personal_home_path(text), text


def test_email_outside_placeholder_domains_fails() -> None:
    mod = _mod()
    assert mod.text_has_personal_email(_j("someone", "@", "corp", ".", "com"))
    assert mod.text_has_personal_email(_j("To: ", "first.last", "@", "mail", ".", "co"))


def test_email_placeholders_pass() -> None:
    mod = _mod()
    for text in (
        "a@office.example",
        "desk@example.com",
        "desk@sub.example.org",
        "x@example.net",
        "build@host.test",
        "nobody@nowhere.invalid",
        "me@box.localhost",
        "bot@users.noreply.gitlab.com",
        "12345+bot@users.noreply.github.com",
        "git@gitlab.com:group/repo.git",
        "icon@2x.png",
        "GRANT mill@192.168.1.%",
        "user@<host>",
        "<user>@<host>",
        "pip install pkg@1.2",
        "",
    ):
        assert not mod.text_has_personal_email(text), text


def test_addresses_loopback_and_doc_ranges_only() -> None:
    mod = _mod()
    for octets in ((10, 0, 0, 5), (172, 16, 4, 2), (192, 168, 0, 9), (8, 8, 4, 4)):
        assert mod.text_has_forbidden_address("host " + ".".join(map(str, octets)))
    for text in ("127.0.0.1", "0.0.0.0", "203.0.113.5", "198.51.100.7", "192.0.2.1", "v1.2.3", "1.2.3"):
        assert not mod.text_has_forbidden_address(text), text


def test_box_seat_skips_css_and_home_path_still_fails() -> None:
    mod = _mod()
    assert mod._keep_home_name("box") is False
    css = "box-shadow: 0 1px rgba(0, 0, 0, 0.4);"
    kept = tuple(n for n in ("box",) if mod._keep_home_name(n))
    assert mod._has_local_home_user(css, mod._home_user_regexes(kept)) is False
    home = _j("C:", BS, "Users", BS, "box", BS, "mill")
    assert mod.text_has_personal_home_path(home)
    assert mod._has_local_home_user(home, mod._home_user_regexes(("box",)))
    suffixed = _j(LOGIN, "-pc")
    assert mod._has_local_home_user(suffixed, mod._home_user_regexes((LOGIN,)))
    real = _j("C:", BS, "Users", BS, LOGIN, BS, "mill")
    assert mod._has_local_home_user(real, mod._home_user_regexes((LOGIN,)))


def test_false_positive_words_pass() -> None:
    mod = _mod()
    text = "challenge the homepage; /homework and Users guide; workstation HOME=~"
    assert not mod.text_has_personal_home_path(text)
    assert not mod.text_has_personal_email(text)
    assert not mod.text_has_forbidden_address(text)


def test_git_scans_cover_new_rules() -> None:
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    assert "home path with a login name in git tip" in src
    assert "email outside placeholder domains in git commit" in src
    mod = _mod()
    assert not mod.text_has_personal_home_path(src)
    assert not mod.text_has_personal_email(src)
    assert mod.scan_git_tracked(()) == []
    assert mod.scan_git_messages() == []


def test_commit_message_personal_name_token_fails() -> None:
    """Title-cased token off the desk-word allow-list fails (assembled at runtime)."""
    mod = _mod()
    # Invented token; joined so no contiguous personal name literal sits in this file.
    who = _j("W", "ibble")
    body = _j(who, " chose the paragraph over table rows")
    assert mod.text_has_personal_name_token(body), body
    assert who.casefold() not in mod.DESK_WORD_ALLOWLIST


def test_commit_message_allowlisted_tokens_pass() -> None:
    mod = _mod()
    for text in (
        "Docs: keep Loops and graphs under the comparison table",
        "Merge branch fix into main",
        "Bump the mill pack",
        "Builder notes the Wall Loop",
        "Add name-token scan to commit-message hygiene",
        "Speech for labels; Refuse an unknown project",
        "",
    ):
        assert not mod.text_has_personal_name_token(text), text


def test_git_message_scan_clean_on_tip() -> None:
    """Scan stays clean: name-token rule is gated to post-scrub HEAD ancestry."""
    mod = _mod()
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    assert "personal name token in git commit" in src
    assert mod.NAME_TOKEN_SCAN_SINCE == "f3aeff8"
    assert "--ancestry-path" in src and "NAME_TOKEN_SCAN_SINCE" in src
    assert mod.scan_git_messages() == []


def test_shallow_clone_fails_closed_on_the_name_token_cut(monkeypatch) -> None:
    """A clone without the scrub cut used to skip the name-token rule silently."""
    mod = _mod()
    monkeypatch.setattr(mod, "name_token_cut_present", lambda root: False)
    monkeypatch.setattr(mod, "clone_is_shallow", lambda root: True)
    fails = mod.scan_git_messages()
    assert any(mod.NAME_TOKEN_SCAN_SINCE in f and "shallow" in f for f in fails), fails


def test_reviewed_commits_are_full_shas_and_ci_clones_full_history() -> None:
    mod = _mod()
    assert mod.NAME_TOKEN_REVIEWED
    assert all(len(s) == 40 and int(s, 16) >= 0 for s in mod.NAME_TOKEN_REVIEWED)
    ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    assert 'GIT_DEPTH: "0"' in ci


# Fresh-root clones (S-8): a public import is one root commit with no scrub cut.

_GIT_ID = (
    "-c", "user.name=fixture desk",
    "-c", "user.email=desk@example.com",
    "-c", "commit.gpgsign=false",
    "-c", "core.hooksPath=/dev/null",
)


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *_GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return out.stdout.strip()


def _fresh_root(path: Path, *messages: str) -> Path:
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    for i, msg in enumerate(messages):
        (path / "f.txt").write_text(str(i), encoding="ascii")
        _git(path, "add", "f.txt")
        _git(path, "commit", "-q", "-m", msg)
    return path


def _scan_in(monkeypatch, repo: Path):
    mod = _mod()
    monkeypatch.setattr(mod, "mill_root", lambda: repo)
    return mod, mod.scan_git_messages()


def test_fresh_root_full_clone_without_cut_passes_clean(tmp_path, monkeypatch) -> None:
    repo = _fresh_root(tmp_path / "r", "the-mill 0.7.6: initial public import")
    mod, fails = _scan_in(monkeypatch, repo)
    assert not mod.name_token_cut_present(repo)
    assert not mod.clone_is_shallow(repo)
    assert fails == [], fails


def test_fresh_root_scans_the_root_commit_for_name_tokens(tmp_path, monkeypatch) -> None:
    who = _j("W", "ibble")
    repo = _fresh_root(tmp_path / "r", _j("import tree for ", who))
    _mod_, fails = _scan_in(monkeypatch, repo)
    root = _git(repo, "rev-list", "--max-parents=0", "HEAD")
    assert fails == [f"personal name token in git commit {root[:12]}"], fails


def test_fresh_root_scans_later_commits_too(tmp_path, monkeypatch) -> None:
    who = _j("W", "ibble")
    repo = _fresh_root(tmp_path / "r", "initial public import", _j("fix for ", who))
    _mod_, fails = _scan_in(monkeypatch, repo)
    tip = _git(repo, "rev-parse", "HEAD")
    assert fails == [f"personal name token in git commit {tip[:12]}"], fails


def test_fresh_root_shallow_clone_still_fails_closed(tmp_path, monkeypatch) -> None:
    src = _fresh_root(tmp_path / "src", "initial public import", "second commit")
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", src.as_uri(), str(shallow))
    mod, fails = _scan_in(monkeypatch, shallow)
    assert mod.clone_is_shallow(shallow)
    assert any(mod.NAME_TOKEN_SCAN_SINCE in f and "shallow" in f for f in fails), fails


def test_unreadable_shallow_state_counts_as_shallow(tmp_path) -> None:
    mod = _mod()
    assert mod.clone_is_shallow(tmp_path / "not-a-repo")
