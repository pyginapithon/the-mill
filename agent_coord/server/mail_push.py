"""MAIL pushes. No watcher. Recipients hear the mail. A receipt returns to the sender."""

from __future__ import annotations

from agent_coord.server.records import mail as rec_mail


def _nm(value: object) -> str:
    """Stored desk name."""
    return str(value or "").strip()

BODY_CAP = 256


def _body(raw: object) -> str:
    return str(raw or "")[:BODY_CAP]


def compact_mail(letter: dict, dest_rows: list[dict], for_desk: str) -> dict:
    """Short mail for one mail_to desk."""
    want = _nm(for_desk)
    tos: list[str] = []
    mine: dict = {}
    for row in dest_rows or []:
        desk = _nm(row.get("desk"))
        if desk:
            tos.append(desk)
        if desk == want:
            mine = row
    return {
        "kind": "mail",
        "id": int(letter.get("id") or 0),
        "created": letter.get("created"),
        "sender": _nm(letter.get("desk") or letter.get("sender")),
        "mail_tos": tos,
        "roster_id": letter.get("sender_roster"),
        "opened": mine.get("opened"),
        "receipt": int(mine.get("receipt") or 0),
        "body": _body(letter.get("body")),
    }


def compact_receipt(row: dict) -> dict:
    """Open of a receipt-flagged mail, for the sender."""
    return {
        "kind": "receipt",
        "id": int(row.get("id") or row.get("mail_id") or 0),
        "created": row.get("created"),
        "body": _body(row.get("body")),
        "mail_to": _nm(row.get("desk") or row.get("opener")),
        "opened": row.get("opened") or row.get("updated"),
    }


def push_mail(cn, mail_id: int) -> None:
    """Async MAIL item to every mail_to desk. Does not plant a watcher."""
    from agent_coord.server.push import emit

    letter = rec_mail.letter_row(cn, int(mail_id))
    if not letter:
        return
    dests = rec_mail.to_list(cn, int(mail_id))
    for row in dests:
        desk = str(row.get("desk") or "")
        if not desk:
            continue
        emit(cn, desk, "mail", compact_mail(letter, dests, desk))


def push_receipt(cn, row: dict) -> None:
    """Async receipt to the sender when this open is the first and receipt is set."""
    from agent_coord.server.push import emit

    if int(row.get("push_receipt") or 0) != 1:
        return
    sender = str(row.get("sender") or "")
    if not sender:
        return
    emit(cn, sender, "receipt", compact_receipt(row))
