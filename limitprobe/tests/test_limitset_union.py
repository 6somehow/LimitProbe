import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/limitset/union_predictions.py"


def test_union_cycles_deduplicates_and_isolates_bad_lines(tmp_path):
    a, b, out = (tmp_path / name for name in ("a.jsonl", "b.jsonl", "union.jsonl"))
    def record(repeat, findings):
        return json.dumps({"case_id": "case", "repeat": repeat, "findings": findings})
    a.write_text(record(0, [{"mechanism": "Fixed block size", "claim": "limits input", "conditions": "x"}]) + "\n" + record(1, []) + "\n")
    b.write_text("invalid\n" + record(8, [{"mechanism": "fixed block size", "claim": "limits input", "conditions": [], "evidence": [{"quote": "proof"}]}]) + "\n")
    cmd = [sys.executable, str(SCRIPT), "--in", str(a), "--in", str(b), "--out", str(out), "--label-tag", "a=first"]
    subprocess.run(cmd, check=True, env=dict(os.environ))
    first = out.read_bytes()
    subprocess.run(cmd, check=True, env=dict(os.environ))
    assert out.read_bytes() == first
    records = [json.loads(line) for line in first.splitlines()]
    assert len(records) == 2
    assert records[0]["findings"][0]["evidence"][0]["quote"] == "proof"
    assert records[1]["findings"][0]["conditions"] == []
    origins = json.loads(out.with_suffix(".origins.json").read_text())
    assert origins[0]["findings"] == [["first", str(b)]]
    assert json.loads(out.with_suffix(".summary.json").read_text())["merged_count"] == 2
