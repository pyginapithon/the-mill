"""Cloud docs spine: printed runbook names the playbook; skeletons stay unmeasured.

No apt, systemctl, ssh, or provider CLI. Reads the tree and the runbook strings.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.install.catalog import cloud_runbook
from agent_coord.install.host import cloud_notes

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ("aws", "azure", "gcp", "self")
PHASES = (
    "## Account and login",
    "## Region and size",
    "## Network",
    "## VM",
    "## Static IP",
    "## Harden",
    "## Install over SSH",
    "## Join",
    "## Cost and tear-down",
    "## Errors a first-timer will hit",
)


@pytest.mark.parametrize("provider", PROVIDERS)
def test_runbook_points_at_unmeasured_playbook(provider):
    path = f"docs/install/cloud/{provider}.md"
    assert path in cloud_runbook(provider)
    notes = cloud_notes(provider)
    assert path in notes
    assert f"share/the-mill/docs/install/cloud/{provider}.md" in notes
    page = (ROOT / path).read_text(encoding="utf-8")
    assert page.splitlines()[2] == "Status: unmeasured"
    for heading in PHASES:
        assert heading in page


def test_other_provider_prints_self_playbook():
    text = cloud_runbook("hetzner")
    assert "docs/install/cloud/self.md" in text
    assert "docs/install/cloud/hetzner.md" not in text


def test_spine_links_modes_and_playbooks():
    spine = (ROOT / "docs" / "install" / "CLOUD.md").read_text(encoding="utf-8")
    for provider in PROVIDERS:
        assert f"cloud/{provider}.md" in spine
    assert "cloud-install.json" in spine
    assert "mill install cloud --ssh" in spine
    assert "127.0.0.1" in spine
    assert "#502" in spine


def test_pack_data_files_ship_playbooks():
    pack = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for provider in PROVIDERS:
        assert f'"docs/install/cloud/{provider}.md"' in pack
