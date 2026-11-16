import csv
import json

from checklimits import labels, stats


def _results(tmp_path, spec):
    """spec: {artifact: [(finding, verdict, level)]}"""
    root = tmp_path / "res"
    for art, fs in spec.items():
        d = root / "tests" / art
        idx = []
        for fid, verdict, level in fs:
            (d / fid).mkdir(parents=True)
            rec = {"finding_id": fid, "verdict": verdict, "level": level, "defeaters": {"D1": "eliminated"},
                   "finding": {"summary": f"claim {fid}", "category": "undisclosed", "location": "a.py:1", "condition": "n != 1"},
                   "evidence": {"paper": [{"quote": "q " + fid}], "code": []},
                   "observed": {"positive": "AssertionError at a.py:1", "negative": "no exception at a.py:1"}}
            (d / fid / "report.json").write_text(json.dumps(rec))
            idx.append({"finding_id": fid, "status": "tested", "verdict": verdict, "level": level, "not_run": None})
        idx.append({"finding_id": f"{art}-skipped", "status": "not_run", "verdict": None, "level": None, "not_run": "no_code_location"})
        (d / "index.json").write_text(json.dumps({"findings": idx}))
    return root


def test_sample_hides_the_harness_answer_and_covers_the_strata(tmp_path):
    root = _results(tmp_path, {"a": [(f"a-F{i}", "yes", "L1") for i in range(8)] + [("a-F9", "yes", "L3"), ("a-F10", "no", "L1")]})
    out = tmp_path / "sheets"
    res = labels.sample(root, out, n=4, raters=("r1", "r2"), seed=1)
    assert res["n"] == 4 and res["n_pool"] == 10
    rows = list(csv.DictReader((out / "sheet_r1.csv").open()))
    assert len(rows) == 4 and set(rows[0]) == set(labels.COLUMNS)
    text = (out / "sheet_r1.csv").read_text()
    assert "L3" not in text and "verdict" not in text.lower().replace("trigger_run", "")        # no verdict or level
    key = json.loads((out / "key.json").read_text())["items"]
    assert {(v["verdict"], v["level"]) for v in key.values()} >= {("yes", "L3"), ("no", "L1")}   # rare strata are drawn
    assert "a-skipped" not in text                                                              # only tested Findings
    assert (out / "sheet_r1.csv").read_text().splitlines()[0] == (out / "sheet_r2.csv").read_text().splitlines()[0]
    assert labels.sample(root, tmp_path / "again", n=4, raters=("r1",), seed=1)["strata"] == res["strata"]


def test_kappa_values():
    assert labels.cohen_kappa(["a", "a", "b", "b"], ["a", "a", "b", "b"]) == 1.0
    assert labels.cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0
    assert labels.fleiss_kappa([["a", "a", "a"], ["b", "b", "b"]]) == 1.0
    assert labels.fleiss_kappa([["a", "b", "a"], ["b", "a", "b"]]) < 0.2
    assert labels.majority(["true", "true", "false"]) == "true" and labels.majority(["true", "false", "unclear"]) is None


def test_evaluate_reports_agreement_and_confirmed_yes_by_level(tmp_path):
    root = _results(tmp_path, {"a": [("a-F1", "yes", "L3"), ("a-F2", "yes", "L1"), ("a-F3", "yes", "L1"), ("a-F4", "no", "L1")]})
    out = tmp_path / "s"
    labels.sample(root, out, n=4, raters=("r1", "r2", "r3"), seed=3)
    key = json.loads((out / "key.json").read_text())["items"]
    truth = {"a-F1": ("true", "valid"), "a-F2": ("true", "valid"), "a-F3": ("false", "valid"), "a-F4": ("true", "valid")}
    for r, flip in (("r1", None), ("r2", None), ("r3", "a-F2")):
        rows = list(csv.DictReader((out / f"sheet_{r}.csv").open()))
        for row in rows:
            fid = key[row["item_id"]]["finding_id"]
            q1, q2 = truth[fid]
            if fid == flip:
                q2 = "invalid"                                     # one dissenter does not change the majority
            row["q1_finding_true"], row["q2_test_valid"] = q1, q2
        with (out / f"sheet_{r}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=labels.COLUMNS)
            w.writeheader()
            w.writerows(rows)
    ev = labels.evaluate([out / f"sheet_{r}.csv" for r in ("r1", "r2", "r3")], out / "key.json")
    assert ev["n_complete"] == 4
    assert ev["agreement"]["q1"]["fleiss_kappa"] == 1.0 and ev["agreement"]["q2"]["fleiss_kappa"] < 1.0
    y = ev["harness"]["yes_confirmed_by_majority"]
    assert y["L3"]["confirmed"] == 1 and y["L1"]["n"] == 2 and y["L1"]["confirmed"] == 1       # F3's claim is false
    assert y["all yes"]["n"] == 3 and y["all yes"]["confirmed"] == 2
    lo, hi = y["all yes"]["wilson95"]
    assert 0 < lo < 2 / 3 < hi < 1


def test_wilson_interval_contains_the_estimate():
    lo, hi = stats.wilson_interval(5, 5)
    assert hi == 1.0 and 0.5 < lo < 0.6               # matches wilson_lower(5, 5)
    assert abs(lo - stats.wilson_lower(5, 5)) < 1e-9
    assert stats.wilson_interval(0, 0) == (0.0, 1.0)
