# Limitations and software testing

The software under test is a systems research project; a limit is analogous to a bug. A reference label and the list of possible defeaters form an oracle: a way to judge whether a candidate matches the reference. A missing oracle yields an unknown result, not a yes or no. Executed tests use L0–L3; analysis without execution uses A0–A2. These tiers describe evidence, not probability of correctness.

Fault detection effectiveness and test adequacy map to **limit coverage**: reference limits found divided by reference limits with an oracle, reported by category and split with a 95% Wilson interval. Categories are applicability limitation, unclear mechanism origin, and method shortcoming. Extra findings are candidate novel limits for triage, not false positives. There is one reference per case and no negatives, so precision, accuracy and false-positive rate cannot be inferred.

Flaky tests map to **repeat stability**: the fraction of independent repeats that re-find a limit. The caller matches claims by similarity and records the resulting booleans; no repeats means unknown, not zero stability. Test independence and N-version testing map to **cross-source agreement**: independently produced paper swarm, code-side, and test-result assessments can support or disagree with a claim. An independent judge assesses coverage. Agreement does not itself prove independence. Bug severity and priority map to **importance**, the existing process-confidence impact information; it is separate from confidence.

## Confidence rules

`confidence_limitset.score_confidence(record, repeats=None, sources=None, code_available=True)` accepts a checklimits-test-report/1 record or a Finding. Repeats are matched booleans, and sources map names to true (support), false (disagreement), or null (unknown). The caller determines code availability. A tested `yes` uses its L tier; a not-run analysis uses its A tier. Other verdicts and missing or invalid tiers start at C0. Initial ranks are L0/A0=C0, L1/A1=C1, L2/A2=C2, L3=C3. Paper-only caps the effective evidence at A1 and the band at C1. C3 additionally requires at least two repeats, all finding the limit, and at least two supporting sources with no disagreement. C2 requires measured stability of at least one half and two supporting sources with no disagreement. Failure of these conditions caps the band at the next applicable level. Any non-eliminated defeater caps it at C1. Missing data never implies agreement or replication. Each result includes the original and effective tier, counts and fraction, source assessments, open defeaters, code availability, and separate importance. Bands always say **uncalibrated**: these thresholds are operational rules, not validated probabilities.

`reliability_table` groups validation observations `{band, found}` (found is boolean or null for no oracle), returning observed coverage, n, and 95% Wilson CI per observed band. Nulls are excluded. Groups with fewer than 10 observations say `n too small` by default. A table alone does not change the uncalibrated label.

## Report inputs

The report command is `conda run -n findlimit python -m scripts.limitset.report --score score.json --records records.json --out OUTPUT`. `score.json` has the minimal shape:

```json
{"cases": [{"case_id": "CS6223-01", "category": "applicability_limitation", "split": "validation", "found": true, "fields": {}}], "reproducibility": {"commits": {}, "models": {}, "seeds": {}, "hashes": {}}}
```

`found` is true, false, or null if there is no oracle; `fields` holds scorer-specific field results and does not change the denominator. `records.json` maps each case ID to a list of checklimits report records. Optional record keys `repeat_results`, `cross_source`, and `code_available` feed the confidence function. The command writes `SUMMARY.md` and one `<case_id>/LIMITATIONS.md` per case. Reproducibility values must be supplied by the caller; missing values remain empty. The 17-case dataset, one label each, absent negatives, LLM judge, and paper-only cases limit conclusions.
