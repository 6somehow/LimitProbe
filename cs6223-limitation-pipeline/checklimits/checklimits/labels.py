"""Human labelling sheets for the tested Findings (C1a) and the agreement / accuracy computation (C1b).

`sample` draws a stratified sample of tested Findings from `results/<root>/tests/*/index.json`, writes one CSV sheet per
rater WITHOUT the harness verdict and level (so the raters are not anchored by it), and a `key.json` with what the
harness said. `evaluate` reads the filled sheets and reports (1) how much the raters agree with each other and
(2) how often the harness's `yes` was confirmed by the raters' majority. Without labels the levels have no empirical
meaning; with them, level-by-level counts and Wilson intervals can be reported next to each level.
"""
from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Optional

from .stats import wilson_interval

Q1 = ("true", "false", "unclear")           # is the Finding true of the code, as stated?
Q2 = ("valid", "invalid", "unclear")        # does the test, as designed, show it?
COLUMNS = ["item_id", "artifact", "finding_id", "claim", "step4_category", "code_location", "condition",
           "paper_or_docs_quote", "trigger_run", "contrast_run", "driver", "q1_finding_true", "q2_test_valid", "notes"]
PUBLIC = COLUMNS[:11]


def collect(results_root: Path, artifacts: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Every tested Finding under results_root/tests/<artifact>/ with its record."""
    rows = []
    for idx in sorted((results_root / "tests").glob("*/index.json")):
        art = idx.parent.name
        if artifacts and art not in artifacts:
            continue
        for f in json.loads(idx.read_text())["findings"]:
            if f["status"] != "tested":
                continue
            rec = json.loads((idx.parent / f["finding_id"] / "report.json").read_text())
            rows.append({"artifact": art, "record": rec, "dir": str((idx.parent / f["finding_id"]).relative_to(results_root))})
    return rows


def sample(results_root: Path, out_dir: Path, n: int = 20, raters: tuple[str, ...] = ("r1", "r2", "r3"), seed: int = 6223,
           artifacts: Optional[list[str]] = None) -> dict[str, Any]:
    pool = collect(results_root, artifacts)
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for r in pool:
        strata[(r["record"]["verdict"], r["record"]["level"])].append(r)
    rng = random.Random(seed)
    for v in strata.values():
        rng.shuffle(v)
    # round robin over the strata (largest first) so that every level that exists is represented
    order = sorted(strata, key=lambda k: -len(strata[k]))
    chosen: list[dict] = []
    while len(chosen) < min(n, len(pool)):
        for k in order:
            if strata[k] and len(chosen) < n:
                chosen.append(strata[k].pop())
    rng.shuffle(chosen)
    out_dir.mkdir(parents=True, exist_ok=True)
    items, key = [], {}
    for i, c in enumerate(chosen, 1):
        rec = c["record"]
        fin, ev = rec["finding"], rec["evidence"]
        iid = f"L{i:02d}"
        quote = (ev.get("paper") or [{}])[0].get("quote", "") if ev.get("paper") else ""
        items.append({"item_id": iid, "artifact": c["artifact"], "finding_id": rec["finding_id"],
                      "claim": fin.get("summary") or "", "step4_category": fin.get("category") or "",
                      "code_location": fin.get("location") or "", "condition": fin.get("condition") or "",
                      "paper_or_docs_quote": quote, "trigger_run": rec["observed"].get("positive", ""),
                      "contrast_run": rec["observed"].get("negative", ""),
                      "driver": f"{c['dir']}/attempt/driver.py"})
        key[iid] = {"finding_id": rec["finding_id"], "verdict": rec["verdict"], "level": rec["level"],
                    "defeaters": rec["defeaters"]}
    for r in raters:
        with (out_dir / f"sheet_{r}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            for it in items:
                w.writerow({**it, "q1_finding_true": "", "q2_test_valid": "", "notes": ""})
    (out_dir / "key.json").write_text(json.dumps({"seed": seed, "n_pool": len(pool), "items": key}, indent=1) + "\n")
    (out_dir / "README.md").write_text(README.format(n=len(items), pool=len(pool), q1="/".join(Q1), q2="/".join(Q2)))
    return {"n": len(items), "n_pool": len(pool), "strata": {f"{k[0]}/{k[1]}": len(v) for k, v in strata.items()},
            "files": sorted(p.name for p in out_dir.iterdir())}


README = """# Labelling sheets ({n} of {pool} tested Findings)

Fill `sheet_<you>.csv` alone, without discussing and without opening `key.json` (it holds what the harness said).

* `q1_finding_true`: read the claim, the code location and the quote. Is the claim true of the code at that location?
  `{q1}`. A claim that is true but trivial still counts as true.
* `q2_test_valid`: open the driver (`driver` column, relative to the results root) and read the two runs. Does the test
  show the claim, with the trigger taking the described path and the contrast not taking it, through a call of the
  product's entry or a function the product calls? `{q2}`.
* `notes`: one line when you answer `unclear` or `invalid`.

Then: `python -m checklimits labels evaluate --sheets sheet_r1.csv sheet_r2.csv sheet_r3.csv --key key.json`.
"""


# --------------------------------------------------------------------------- agreement
def read_sheet(p: Path) -> dict[str, dict[str, str]]:
    with p.open(newline="") as f:
        return {r["item_id"]: r for r in csv.DictReader(f)}


def cohen_kappa(a: list[str], b: list[str]) -> Optional[float]:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def fleiss_kappa(table: list[list[str]]) -> Optional[float]:
    """table: one list of rater labels per item (same number of raters everywhere)."""
    n_items = len(table)
    if n_items == 0:
        return None
    m = len(table[0])
    cats = sorted({x for row in table for x in row})
    counts = [[row.count(c) for c in cats] for row in table]
    p_i = [(sum(c * c for c in row) - m) / (m * (m - 1)) for row in counts]
    p_j = [sum(row[j] for row in counts) / (n_items * m) for j in range(len(cats))]
    pe = sum(p * p for p in p_j)
    pbar = sum(p_i) / n_items
    return None if pe == 1 else round((pbar - pe) / (1 - pe), 3)


def majority(labels: list[str]) -> Optional[str]:
    c = Counter(labels).most_common()
    return c[0][0] if c and (len(c) == 1 or c[0][1] > c[1][1]) else None


def evaluate(sheets: list[Path], key: Path) -> dict[str, Any]:
    data = [read_sheet(p) for p in sheets]
    names = [p.stem.removeprefix("sheet_") for p in sheets]
    k = json.loads(key.read_text())["items"]
    ids = [i for i in k if all(i in d and d[i]["q1_finding_true"] and d[i]["q2_test_valid"] for d in data)]
    out: dict[str, Any] = {"raters": names, "n_items": len(k), "n_complete": len(ids), "agreement": {}, "harness": {}}
    for q, col in (("q1", "q1_finding_true"), ("q2", "q2_test_valid")):
        rows = [[d[i][col].strip().lower() for d in data] for i in ids]
        pair = {}
        for (a, na), (b, nb) in combinations(list(zip(data, names)), 2):
            la = [a[i][col].strip().lower() for i in ids]
            lb = [b[i][col].strip().lower() for i in ids]
            pair[f"{na}-{nb}"] = {"percent": round(sum(x == y for x, y in zip(la, lb)) / max(1, len(ids)), 3),
                                  "cohen_kappa": cohen_kappa(la, lb)}
        out["agreement"][q] = {"pairs": pair, "fleiss_kappa": fleiss_kappa(rows) if len(data) > 1 else None}
    # the harness's `yes` against the raters' majority: a `yes` is confirmed when the Finding is true and the test valid
    by_level: dict[str, list[bool]] = defaultdict(list)
    for i in ids:
        if k[i]["verdict"] != "yes":
            continue
        q1 = majority([d[i]["q1_finding_true"].strip().lower() for d in data])
        q2 = majority([d[i]["q2_test_valid"].strip().lower() for d in data])
        by_level[k[i]["level"]].append(q1 == "true" and q2 == "valid")
    lv = {}
    for level, flags in sorted(by_level.items()):
        lo, hi = wilson_interval(sum(flags), len(flags))
        lv[level] = {"n": len(flags), "confirmed": sum(flags), "rate": round(sum(flags) / len(flags), 3),
                     "wilson95": [round(lo, 3), round(hi, 3)]}
    allf = [f for fl in by_level.values() for f in fl]
    if allf:
        lo, hi = wilson_interval(sum(allf), len(allf))
        lv["all yes"] = {"n": len(allf), "confirmed": sum(allf), "rate": round(sum(allf) / len(allf), 3),
                         "wilson95": [round(lo, 3), round(hi, 3)]}
    out["harness"]["yes_confirmed_by_majority"] = lv
    out["harness"]["note"] = "items without a clear majority count as not confirmed; the sample is small, read the intervals"
    return out
