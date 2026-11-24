#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if command -v uv >/dev/null 2>&1; then
  uv pip install --python .venv/bin/python -e .
else
  .venv/bin/python -m ensurepip --upgrade
  .venv/bin/python -m pip install -e .
fi
.venv/bin/python -m paperprobe doctor
