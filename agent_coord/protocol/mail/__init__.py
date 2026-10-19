"""Mill mailbox pure helpers (addressing, filters, read-party).

Mailbox names. No database.
"""

from .constants import (
    DEAD_LETTER_DST,
    MAIL_BODY_MAX,
    MAIL_TTL_DEAD_DESK_S,
    MAIL_TTL_HUMAN_S,
    MAIL_TTL_PRODUCT_S,
    MAIL_TTL_READ_S,
    MAIL_TTL_ROLE_S,
    MAIL_TTL_STAR_S,
)
from agent_coord.client.outbound.addressing import inbox_dst_boxes, mail_addr_kind, parse_mail_to
from .filters import expand_mail_filter_keys, flatten_mail_keys
from .read_party import format_read_who, normalize_read_party

__all__ = [
    "DEAD_LETTER_DST",
    "MAIL_BODY_MAX",
    "MAIL_TTL_DEAD_DESK_S",
    "MAIL_TTL_HUMAN_S",
    "MAIL_TTL_PRODUCT_S",
    "MAIL_TTL_READ_S",
    "MAIL_TTL_ROLE_S",
    "MAIL_TTL_STAR_S",
    "expand_mail_filter_keys",
    "flatten_mail_keys",
    "format_read_who",
    "inbox_dst_boxes",
    "mail_addr_kind",
    "normalize_read_party",
    "parse_mail_to",
]
