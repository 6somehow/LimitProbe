#!/usr/bin/env bash
# Temporary Python 3.11 venv for the code under test of the NNSmith artifact (pinned commit a8307f2, tag v0.0.1).
# Lives in checklimits/scratch/ (git-ignored), safe to delete. Usage: PYTHON311=/path/to/python3.11 bash scripts/make_venv_nnsmith.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON311:-<python>}"   # only used to create the venv; never modified
"$PY" --version | grep -q "3\.11" || { echo "need Python 3.11, got: $("$PY" --version)"; exit 1; }
[ -d scratch/venv_nnsmith ] || "$PY" -m venv scratch/venv_nnsmith
V=scratch/venv_nnsmith/bin/python
$V -m pip install -q --upgrade pip
$V -m pip install -q "numpy<2" torch==2.4.0 --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
$V -m pip install -q "z3-solver>=4.11.0" "networkx>=2.6.3" "hydra-core>=1.1.0" hydra_colorlog multipledispatch appdirs "onnx<1.17" "onnxruntime<1.20" "numpy<2" pydantic
$V -m pip list 2>/dev/null | grep -i -E "^(torch|numpy|z3-solver|networkx|hydra-core|onnx|onnxruntime|pydantic|multipledispatch) "
