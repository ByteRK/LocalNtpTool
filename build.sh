#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller \
  --noconfirm \
  --clean \
  --name LocalNtpTool \
  --windowed \
  run_ntp_tool.py
