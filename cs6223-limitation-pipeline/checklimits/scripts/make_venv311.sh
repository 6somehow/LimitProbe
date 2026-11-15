#!/usr/bin/env bash
# Build the temporary Python 3.11 venv that holds the versions FlexPrefill pins
# (torch 2.4.0, triton 3.0.0, transformers 4.44.0); no wheels for these exist for Python 3.14.
# The venv lives in checklimits/scratch/ (git-ignored) and can be deleted at any time.
# Usage: PYTHON311=/path/to/python3.11 bash scripts/make_venv311.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON311:-/home/somehow6/miniconda3/envs/ravel/bin/python}"   # only used to create the venv; never modified
"$PY" --version | grep -q "3\.11" || { echo "need Python 3.11, got: $("$PY" --version)"; exit 1; }
[ -d scratch/venv311 ] || "$PY" -m venv scratch/venv311
V=scratch/venv311/bin/python
$V -m pip install -q --upgrade pip
$V -m pip install -q torch==2.4.0 numpy==1.26.4 --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
$V -m pip install -q triton==3.0.0 transformers==4.44.0 einops==0.8.0 pydantic
$V -m pip list 2>/dev/null | grep -i -E "^(torch|triton|transformers|einops|numpy|pydantic) "
