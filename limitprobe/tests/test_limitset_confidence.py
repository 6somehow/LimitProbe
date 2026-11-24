import json
import os
import subprocess
import sys

import pytest

from confidence_limitset import reliability_table, score_confidence, wilson_interval
from scripts.limitset.report import render_report


def test_bands_and_items():
    record = {"status": "tested", "verdict": "yes", "level": "L3", "defeaters": {"D1": "eliminated"}, "finding": {"process_confidence": {"importance": {"impact": 3}}}}
    result = score_confidence(record, [True, True], {"paper": True, "code": True})
    assert result["band"] == "C3" and result["label"] == "uncalibrated"
    assert result["importance"] == {"impact": 3}
    assert score_confidence(record, [True, True], {"paper": True, "code": True}, False)["band"] == "C1"
    assert score_confidence(record)["band"] == "C1"
    record["defeaters"]["D3"] = "residual"
    assert score_confidence(record, [True, True], {"paper": True, "code": True})["band"] == "C1"
    record["verdict"] = "no"
    assert score_confidence(record)["band"] == "C0"
    assert score_confidence({"status": "not_run", "analysis": {"tier": "A2"}}, [True, False], {"paper": True, "test": True})["band"] == "C2"
    with pytest.raises(ValueError):
        score_confidence(record, [1])


def test_reliability_and_no_oracle():
    rows = reliability_table([{"band": "C1", "found": True}, {"band": "C1", "found": False}, {"band": "C1", "found": None}])
    assert rows[0]["n"] == 2 and rows[0]["coverage"] == 0.5 and rows[0]["assessment"] == "n too small"
    assert rows[0]["wilson_ci"][0] < 0.5 < rows[0]["wilson_ci"][1]
    assert wilson_interval(0, 0) is None


def test_report_and_command(tmp_path):
    cases = [{"case_id": "case1", "category": "shortcoming", "split": "test", "found": True, "fields": {}}, {"case_id": "case2", "category": "shortcoming", "split": "test", "found": None, "fields": {}}]
    record = {"finding": {"summary": "a | b", "category": "shortcoming", "disclosure": "known"}, "status": "not_run", "analysis": {"tier": "A1"}}
    output = render_report(cases, [record])
    assert "1/1" in output and "a \\| b" in output and "uncalibrated" in output
    score = tmp_path / "score.json"
    records = tmp_path / "records.json"
    score.write_text(json.dumps({"cases": cases}))
    records.write_text(json.dumps({"case1": [record]}))
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": os.getcwd()}
    result = subprocess.run([sys.executable, "-m", "scripts.limitset.report", "--score", str(score), "--records", str(records), "--out", str(tmp_path / "out")], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out" / "case1" / "LIMITATIONS.md").exists()
    assert (tmp_path / "out" / "SUMMARY.md").exists()
