#!/usr/bin/env bash
# mill empty-machine bootstrap (Linux / WSL) - silent CLI, no installer wizards.
# Agents: run this file once. Do not execute it line by line.
# curl -fsSL https://raw.githubusercontent.com/si4ai/the-mill/main/scripts/bootstrap.sh -o install.sh && bash install.sh && rm -f install.sh
# Chicken-egg: machine may have no mill/python. Agent runs this (not a HUMAN wizard).
# WSL: do NOT hijack Windows MySQL on 127.0.0.1:3306 (mill install preflight enforces).
set -euo pipefail
echo "mill bootstrap: ensure Python 3.10+ (apt/dnf/apk if missing)"

py_ok() {
  command -v python3 >/dev/null 2>&1 || return 1
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)'
}

if ! py_ok; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add --no-cache python3 py3-pip
  else
    echo "Python 3.10+ missing and no apt/dnf/apk. Install python3 via silent CLI, then re-run." >&2
    exit 1
  fi
  py_ok || { echo "Python still missing after package install." >&2; exit 1; }
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
echo "mill bootstrap: pip install mill (repo . or the-mill)"
if [[ -d "$REPO/agent_coord" && -f "$REPO/pyproject.toml" ]]; then
  (cd "$REPO" && python3 -m pip install .)
else
  python3 -m pip install the-mill
fi

echo "mill bootstrap: mill install server --apply (probe + ensure-missing, silent CLI)"
if command -v mill >/dev/null 2>&1; then
  mill install server --apply
else
  python3 -m agent_coord install server --apply
fi
echo "mill bootstrap: done"
