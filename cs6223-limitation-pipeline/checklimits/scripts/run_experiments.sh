#!/bin/sh
# A2/A4 (c2), S5a repeats (r2, r3) and S5b blind (bl) on the same findings. Sequential batches, 3 workers each.
PY=<python>
cd <project-root>/checklimits
only() { for f in "$@"; do printf -- '--only %s ' "$f"; done; }
NN_ALL="nnsmith-F001 nnsmith-F018 nnsmith-F003 nnsmith-F035 nnsmith-F034 nnsmith-F036 nnsmith-F012 nnsmith-F004"
NN_S5="nnsmith-F004 nnsmith-F035 nnsmith-F036"
FP_S5="flexprefill-F007 flexprefill-F008"
$PY -m checklimits batch --artifact nnsmith --batch-id c2n --workers 3 $(only $NN_ALL) > scratch/batch_c2n.out 2>&1
$PY -m checklimits batch --artifact flexprefill --batch-id c2f --workers 2 $(only $FP_S5) > scratch/batch_c2f.out 2>&1
for r in r2 r3; do
  $PY -m checklimits batch --artifact nnsmith --batch-id ${r}n --workers 3 $(only $NN_S5) > scratch/batch_${r}n.out 2>&1
  $PY -m checklimits batch --artifact flexprefill --batch-id ${r}f --workers 2 $(only $FP_S5) > scratch/batch_${r}f.out 2>&1
done

$PY -m checklimits batch --artifact nnsmith --batch-id bln --blind --workers 3 $(only $NN_S5) > scratch/batch_bln.out 2>&1
$PY -m checklimits batch --artifact flexprefill --batch-id blf --blind --workers 2 $(only $FP_S5) > scratch/batch_blf.out 2>&1
echo done > scratch/experiments.done
