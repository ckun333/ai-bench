#!/usr/bin/env bash
# ai-bench installer — run directly:
#   curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/install.sh | bash
set -e

BIN="${HOME}/.local/bin"
mkdir -p "$BIN"

echo "⬇️  Downloading ai-bench…"
curl -sL -o "${BIN}/ai-bench" \
  https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py
chmod +x "${BIN}/ai-bench"

echo "✅ ai-bench installed → ${BIN}/ai-bench"
echo "   Run: ai-bench --help"
