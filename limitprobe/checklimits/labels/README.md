# Labelling sheets (20 of 51 tested Findings)

**Baseline: `sheet_shanghao.csv`** (reviewed by Shanghao, also as `sheet_shanghao_reviewed.xlsx`; the other raters' sheets were dropped on 2026-11-17).
The labels in it use another vocabulary than the sheet header says: q1 `True` / `Partially true`, q2 `Unverified` / `Inconsistent`.
`labels.py` normalises them (`true` / `partial`, `unclear` / `invalid`). **`Unverified` for q2 means the reviewer could not
read the test** (the sheet only gave the driver's path, not its source), so q2 is mostly not assessed: 1 of 20 is decided.
`context/Lxx.md` holds, per item, the claim, the code around the location and the full driver with both runs: what is needed
to fill q2. `llm/` holds a first pass by gpt-6.1-sol (3 independent samples).

```bash
python -m checklimits labels evaluate --sheets labels/sheet_shanghao.csv --key labels/key.json     # claim true / test valid per level
python -m checklimits labels baseline --sheet labels/sheet_shanghao.csv --sheets labels/llm/sheet_gpt-61-sol_*.csv
python -m checklimits labels compare  --sheets labels/llm/sheet_gpt-61-sol_*.csv --key labels/key.json
python -m checklimits labels context  --sheet labels/sheet_shanghao.csv --out labels                # regenerate context/
```

* `q1_finding_true`: is the claim true of the code at that location? `true / false / partial / unclear`.
* `q2_test_valid`: does the test show it, with the trigger taking the described path and the contrast not taking it, through the
  product's entry or a function the product calls? `valid / invalid / unclear`.
