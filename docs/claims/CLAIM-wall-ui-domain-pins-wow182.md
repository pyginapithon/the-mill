# CLAIM wall-ui-domain-pins-wow182

## Bug / ask
Host Nest under `/projects/finance`: `todo.js` / `mail.js` / `score.js` â†' Unexpected token '<' (HTML). Stale relative domain loads resolve to `/projects/finance/mail/mail.js`; Hub SPA fallthrough served board HTML. Score pin still wow162; `lib/lazy.js` unpinned (24h cache kept old DOMAINS).

## Fix (local tip; no push)
1. **Root-absolute domain pins tip wow182** â€" `lib/lazy.js` + `board.html` inert seams: `/mail|/score|/todo` JS+CSS `?v=wow182` (was wow162; now wow182).
2. **Pin lazy loader** â€" `board.html` `/lib/lazy.js?v=wow182` so Nest hard-refresh cannot keep pre-wow177 relative DOMAINS.
3. **Hub SPA harden** â€" `_is_nest_board_path` returns False for static suffixes (`.js`/`.css`/â€¦); `/projects/.../mail/mail.js` never board HTML. Root `/mail/*.js` still static JS.
4. Tip bust `boot.js?v=wow182` + `board.css?v=wow182`. Marker `WALL_DOMAIN_PINS_WOW182`.

## Glance (Host)
Hard-refresh: `https://192.0.2.10/?v=wow182` or open `/` then Nest `/projects/finance` â€" Network must show `/mail/mail.js?v=wow182` (JS), not `/projects/finance/mail/...`.

```text
curl -skI https://192.0.2.10/mail/mail.js          -> text/javascript
curl -skI https://192.0.2.10/projects/finance/mail/mail.js -> NOT text/html board
```

## Self-test
```
pytest tests/server/test_asgi.py tests/wall/test_wall_ui_perf_lazy.py tests/wall/test_score_rules.py -q
```

## Out of scope
Push / pack / PyPI. Host recycle (checkout-served tip needs hard-refresh only if wall_ui is checkout-live).
