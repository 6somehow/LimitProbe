#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
work="$(mktemp -d /tmp/codex-AR-1-XXXXXX)"
trap 'rm -rf "$work"' EXIT
python -m pytest -q --basetemp "$work/pytest"
mkdir -p "$work/pred" "$work/score"
python scripts/limitset/union_predictions.py --in examples/fixtures/predictions.jsonl --in examples/fixtures/predictions.jsonl --out "$work/pred/predictions.jsonl"
python -m scorer_limitset --dataset limitset2 --root examples/fixtures --labels examples/fixtures/labels.jsonl --pred "$work/pred/predictions.jsonl" --judge fake --out "$work/score"
cat "$work/score/score.json"
python scripts/limitset/compare.py --system "synthetic=$work/score:$work/pred" --split test --out "$work/comparison.md"
cat "$work/comparison.md"
