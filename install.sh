#!/usr/bin/env bash
# ai-bench installer
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
mkdir -p "$BIN"

ln -sf "${SCRIPT_DIR}/bench.py" "${BIN}/ai-bench"
chmod +x "${SCRIPT_DIR}/bench.py"

echo "✅ ai-bench installed → ${BIN}/ai-bench"
echo "   Run: ai-bench --help"
