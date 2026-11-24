#!/bin/sh
PY="${PY:-python}"   # the Python of the findlimit environment
cd "$(dirname "$0")/.."
$PY -m checklimits batch --artifact nnsmith --batch-id cbn --blind --workers 3 --only nnsmith-F004 --only nnsmith-F035 --only nnsmith-F036 > scratch/batch_cbn.out 2>&1
$PY -m checklimits batch --artifact flexprefill --batch-id cbf --blind --workers 2 --only flexprefill-F007 --only flexprefill-F008 > scratch/batch_cbf.out 2>&1
echo done > scratch/clean_blind.done
