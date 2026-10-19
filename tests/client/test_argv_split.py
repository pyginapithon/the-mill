# -*- coding: utf-8 -*-
"""mill route stores list2cmdline on Windows. Split must round-trip that string."""
import os
import shlex
import subprocess
import sys

from agent_coord.client.route_chain import split_cmd


def test_split_round_trip_paths_and_spaces() -> None:
    argv = [sys.executable, os.path.join("work", "on mail.py"), "need,status"]
    cmd = subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)
    assert split_cmd(cmd) == argv


def test_split_blank() -> None:
    assert split_cmd("  ") == []
