"""Load hint_handler.lib without colliding with repo-root tools/."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_LIB = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "protocol"
    / "hint-handler"
    / "tools"
    / "hint_handler"
    / "lib.py"
)


@pytest.fixture(scope="session")
def hh():
    name = "hint_handler_lib"
    spec = importlib.util.spec_from_file_location(name, _LIB)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod  # required before dataclass processes HintEvent
    spec.loader.exec_module(mod)
    return mod
