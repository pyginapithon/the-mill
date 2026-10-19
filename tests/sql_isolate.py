"""Per-process throwaway MySQL DB names for @pytest.mark.sql suites.

Concurrent pytest on a shared mill_records_test races wipe.sql (DROP PROCEDURE
while another runner is mid-suite). FK_CHECKS wrap does not serialize runners.
Each process (or xdist worker) gets its own DB name so wipe/apply cannot clobber
a sibling run. Shipper / CI `pytest tests -m sql` pick this up automatically.
"""
from __future__ import annotations

import os
import re

_SAFE = re.compile(r"[^A-Za-z0-9_]+")


def throwaway_db(prefix: str = "mill_records_test") -> str:
    """Return a MySQL schema name unique to this pytest process or xdist worker."""
    worker = (os.environ.get("PYTEST_XDIST_WORKER") or "").strip()
    suffix = worker if worker else str(os.getpid())
    safe = _SAFE.sub("_", suffix).strip("_") or "x"
    base = (prefix or "mill_records_test").strip() or "mill_records_test"
    return f"{base}_{safe}"[:64]
