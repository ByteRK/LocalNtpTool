#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  echo "Using project virtual environment: $PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
  echo "Using system Python: $PYTHON_BIN"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
  echo "Using system Python: $PYTHON_BIN"
else
  echo "Python was not found. Create .venv or install Python first." >&2
  exit 1
fi

exec "$PYTHON_BIN" "$ROOT_DIR/run_ntp_tool.py" "$@"
