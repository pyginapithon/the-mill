"""#724: the first word of a sentence inside a line reads as prose.

Regression row F91 (name-token-sentence-start). A squash message written at
merge time put an ordinary word right after a period mid-line ("... under
2 KB. Live 0.7.14, ..."), and the name-token rule read it as a person's name,
so main went red. After ". ", "! " or "? " a capitalized word now gets the
line-start rule of #338: it passes only when its lower-case form is an
ordinary word of the tree. A name-like token still fails at any position,
and home paths and emails in the same message are still caught.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_pack as cp  # noqa: E402

# Invented name-like tokens, assembled so no literal sits in this file.
NAME = "Qu" + "illonde"
NAME2 = "Wi" + "bble"
VOCAB = frozenset({"live", "scope", "finding", "behavior", "history"})

# The shape of the message that turned main red (6b333be).
RED_MAIN = (
    "title\n\nAn empty --mine read stays under 2 KB. Live 0.7.14, builder: board\n"
    "154653 bytes on the wire for 159 cards. Regression row F83.\n"
)

PASS = [
    RED_MAIN,
    "title\n\nit landed. Live check done.\n",
    "title\n\nis it main? Scope is main! Finding first.\n",
    "title\n\nthe row (F49). Behavior is unchanged.\n",
    'title\n\nit said "done." History is kept.\n',
]

FAIL = [
    f"title\n\nthe fix landed. {NAME} checked it.\n",  # name at a sentence start
    f"title\n\nis it main? {NAME} asked!\n",
    f"title\n\nsee e.g. {NAME} for the case.\n",  # abbreviation: still a name
    f"title\n\nthe fix came from {NAME} today.\n",  # mid-sentence name
    "title\n\nkeep the Live check\n",  # mid-sentence ordinary word: allow-list rule unchanged
    "title\n\nit landed.Live check\n",  # no space after the period: not a sentence start
    f"title\n\n{NAME2} chose the paragraph. Live check done.\n",
]


def test_names_are_not_ordinary() -> None:
    for n in (NAME, NAME2):
        assert n.casefold() not in VOCAB
        assert n.casefold() not in cp.DESK_WORD_ALLOWLIST


def test_red_main_shape_failed_before_the_fix_without_vocab() -> None:
    # The token is an ordinary word only through vocab; without it the rule is strict.
    assert cp.text_has_personal_name_token(RED_MAIN, frozenset())


@pytest.mark.parametrize("msg", PASS)
def test_sentence_start_ordinary_word_passes(msg: str) -> None:
    assert not cp.text_has_personal_name_token(msg, VOCAB), msg


@pytest.mark.parametrize("msg", FAIL)
def test_name_like_or_mid_sentence_token_still_fails(msg: str) -> None:
    assert cp.text_has_personal_name_token(msg, VOCAB), msg


def test_tree_vocab_reads_the_red_main_token_as_ordinary() -> None:
    vocab = cp.ordinary_words(ROOT)
    assert "live" in vocab
    assert NAME.casefold() not in vocab
    assert not cp.text_has_personal_name_token(RED_MAIN, vocab)


def test_home_paths_and_emails_in_a_passing_message_are_still_caught() -> None:
    login = "qu" + "illonde"
    path_msg = RED_MAIN + "ran it from /" + "home/" + login + "/src. Live again.\n"
    win_msg = RED_MAIN + "C:" + "\\Users\\" + login + "\\src. Live again.\n"
    mail_msg = RED_MAIN + "ask " + login + "@" + "gmail.com. Live again.\n"
    assert not cp.text_has_personal_name_token(path_msg, VOCAB)
    assert cp.text_has_personal_home_path(path_msg)
    assert cp.text_has_personal_home_path(win_msg)
    assert cp.text_has_personal_email(mail_msg)
