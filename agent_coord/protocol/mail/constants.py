"""Mail TTL / dead-letter constants (purge-mail schedule)."""

# Do not wipe on every presence death.
MAIL_TTL_READ_S = 7 * 86400
MAIL_TTL_DEAD_DESK_S = 3 * 86400
MAIL_TTL_ROLE_S = 30 * 86400
MAIL_TTL_HUMAN_S = 90 * 86400
MAIL_TTL_PRODUCT_S = 30 * 86400
MAIL_TTL_STAR_S = 2 * 86400
DEAD_LETTER_DST = "dead-letter"
# agent_msg.body + mill send cap. Other 500-char cols stay.
MAIL_BODY_MAX = 4096
