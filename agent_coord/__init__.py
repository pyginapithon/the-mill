"""Transactional multi-project locks and a small mailbox."""

import sys

# Import-time gate: refuse <3.10 before coord/presence (3.10-only syntax).
# Inline sys only so 3.8 can parse this module and exit cleanly (exit 2).
if sys.version_info < (3, 10):
    sys.stderr.write(
        "Python %d.%d is too old; mill needs Python 3.10+.\n"
        "Hint: use uv + CPython 3.12 (e.g. uv python install 3.12; "
        "uv venv --python 3.12).\n"
        % (sys.version_info[0], sys.version_info[1])
    )
    raise SystemExit(2)

from agent_coord.helpers.errors import CoordError, HoldHeld, LockHeld
from agent_coord.helpers.owner import default_owner
from agent_coord.helpers.ident import file_key, slug, this_host
from agent_coord.install.packver import package_version

__version__ = package_version()

__all__ = [
    "__version__",
    "CoordError",
    "HoldHeld",
    "LockHeld",
    "default_owner",
    "file_key",
    "slug",
    "this_host",
]
