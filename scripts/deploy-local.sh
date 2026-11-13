#!/usr/bin/env bash
# Install agent-hub from this checkout onto the local Mac as uv tools.
# Run by the owner on the Mac from the repo root: ./scripts/deploy-local.sh
# Needs uv (https://docs.astral.sh/uv/) and tmux 3.3+ on PATH. Installs nothing else.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install it first, then re-run." >&2
  exit 1
fi

uv tool install --force .

# Verify the installed commands answer.
cao --help >/dev/null
cao-server --help >/dev/null 2>&1 || true
echo "Installed. Commands: cao, cao-server, cao-mcp-server, cao-ops-mcp-server"
