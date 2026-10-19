# Claim - floor trust stamp

Status: **local commit only**. No push, pack, or PyPI action.

## Claims

1. `floor()` stamps the current `mill_trust()` value on its response envelope.
2. `floor_scope()` stamps the same mill trust matrix on scoped floor envelopes, including Stations lan/role requests.
3. The thin SQL-backed floor tests set trust to `limited` and assert the stamp on both envelopes.

## Evidence

- `agent_coord/server/records/floor.py:1097-1098` - `floor()` trust-matrix comment and `trust: mill_trust()` envelope field.
- `agent_coord/server/records/floor.py:1249-1250` - `floor_scope()` trust-matrix comment and `trust: mill_trust()` envelope field.
- `tests/server/records/test_floor_fp.py:74-80` - project floor test sets trust and asserts the response stamp.
- `tests/server/records/test_floor_fp.py:126-136` - scoped floor test sets trust and asserts the response stamp.

## Validation

- `python -m compileall -q agent_coord/server/records/floor.py tests/server/records/test_floor_fp.py` - passed.
- `python -m pytest tests/server/records/test_floor_fp.py -q` - 5 passed; pytest then exited 1 during temporary-directory cleanup with `WinError 5` access denied.
