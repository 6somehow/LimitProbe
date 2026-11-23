# Limitset2 scoring

Use `python -m scorer_limitset --dataset limitset2 --labels PATH --pred PATH --root PATH --out DIR` with English labels. Each label needs a unique `label_id` within its case. The optional `--splits` file uses the legacy format; without it, all cases are in the test split.

The judge assesses each label against each repeat. A prediction can be assigned to one label per repeat; confidence breaks ties before label and prediction order. Coverage reports labels and cases with Wilson intervals. Unavailable judgments are counted and excluded. The legacy single-label dataset keeps its existing scoring behavior.
