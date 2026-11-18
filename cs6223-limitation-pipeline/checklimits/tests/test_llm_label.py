import csv
import io
import json
import urllib.error

import pytest

from checklimits import labels, llm_label

KEY = "sk-test-0123456789abcdefghijklmnop"


def _results(tmp_path):
    root = tmp_path / "res"
    t = root / "tests" / "toy" / "toy-F1"
    (t / "attempt").mkdir(parents=True)
    (t / "attempt" / "driver.py").write_text("def run(inputs):\n    return entry(inputs['n'])\n")
    (t / "attempt" / "form.json").write_text(json.dumps({
        "design": {"expected": {"positive": "AssertionError at a.py:1", "negative": "no exception at a.py:1"}},
        "execution": {"entry_called": "a.py::entry", "entry_reason": None, "mocks": [{"symbol": "x", "kind": "fake_module", "behavior": "n", "reason": "r"}]}}))
    (t / "execution_report.json").write_text(json.dumps({"positive": {"inputs": {"n": 2}}, "negative": {"inputs": {"n": 1}},
                                                          "confidence": {"level": "L3", "defeaters": []}, "final_verdict": "yes"}))
    (t / "report.json").write_text(json.dumps({
        "finding_id": "toy-F1", "verdict": "yes", "level": "L3", "defeaters": {"D1": "eliminated"},
        "finding": {"summary": "n must be 1", "category": "undisclosed", "location": "a.py:1", "condition": "n != 1"},
        "evidence": {"paper": [{"quote": "q"}], "code": []},
        "observed": {"positive": "AssertionError at a.py:1", "negative": "no exception at a.py:1"}}))
    (t.parent / "index.json").write_text(json.dumps({"findings": [
        {"finding_id": "toy-F1", "status": "tested", "verdict": "yes", "level": "L3", "not_run": None}]}))
    return root


def _sheet(tmp_path, root):
    out = tmp_path / "sheets"
    labels.sample(root, out, n=1, raters=("r1",))
    return out


def _opener(answers):
    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def open_(req, timeout=0):
        body = json.loads(req.data)
        assert req.headers["Authorization"] == f"Bearer {KEY}" and body["model"] == "gpt-6.1-sol" and body["n"] == len(answers)
        return R(json.dumps({"choices": [{"message": {"content": a}} for a in answers], "usage": {"total_tokens": 100}}).encode())
    return open_


def test_prompt_has_the_evidence_but_not_what_the_harness_concluded(tmp_path):
    root = _results(tmp_path)
    sheets = _sheet(tmp_path, root)
    row = next(iter(labels.read_sheet(sheets / "sheet_r1.csv").values()))
    p = llm_label.build_prompt(row, root, "no/such/repo")
    assert "n must be 1" in p and "driver.py" in p and "entry(inputs['n'])" in p and "fake_module" in p
    assert "AssertionError at a.py:1" in p and "q1" in p and "q2" in p
    for leak in ("L3", "eliminated", "defeater", "verdict", "yes/L"):
        assert leak not in p, leak


def test_labelling_writes_one_sheet_per_sample_in_the_human_format(tmp_path):
    root = _results(tmp_path)
    sheets = _sheet(tmp_path, root)
    kf = tmp_path / "k.txt"
    kf.write_text(KEY + "\n")
    ans = ['{"q1":"true","q1_reason":"assert is there","q2":"valid","q2_reason":"ok"}',
           '{"q1":"TRUE","q1_reason":"x","q2":"maybe","q2_reason":"y"}',
           'not json at all']
    res = llm_label.label(sheets / "sheet_r1.csv", root, tmp_path / "llm", kf, samples=3, repo_of=lambda a: "no/repo",
                          opener=_opener(ans))
    assert res["errors"] == [] and res["total_tokens"] == 100 and len(res["sheets"]) == 3
    rows = [list(labels.read_sheet(tmp_path / "llm" / s).values())[0] for s in res["sheets"]]
    assert [(r["q1_finding_true"], r["q2_test_valid"]) for r in rows] == [("true", "valid"), ("true", "unclear"), ("unclear", "unclear")]
    assert set(rows[0]) == set(labels.COLUMNS)
    everything = "".join(p.read_text() for p in (tmp_path / "llm").iterdir())
    assert KEY not in everything                                   # the key never reaches a file


def test_the_key_is_removed_from_error_messages(tmp_path):
    def boom(req, timeout=0):
        raise urllib.error.HTTPError("u", 401, "x", {}, io.BytesIO(f"bad key {KEY}".encode()))
    with pytest.raises(llm_label.LLMError) as e:
        llm_label.chat("p", KEY, opener=boom)
    assert KEY not in str(e.value) and "<KEY>" in str(e.value)
    root = _results(tmp_path)
    sheets = _sheet(tmp_path, root)
    kf = tmp_path / "k.txt"
    kf.write_text(KEY)
    res = llm_label.label(sheets / "sheet_r1.csv", root, tmp_path / "llm", kf, samples=2, repo_of=lambda a: "x", opener=boom)
    assert res["errors"] == ["L01"] and KEY not in "".join(p.read_text() for p in (tmp_path / "llm").iterdir())


def test_compare_lists_items_the_llm_does_not_confirm(tmp_path):
    root = _results(tmp_path)
    sheets = _sheet(tmp_path, root)
    kf = tmp_path / "k.txt"
    kf.write_text(KEY)
    ans = ['{"q1":"true","q1_reason":"a","q2":"invalid","q2_reason":"driver copies the logic"}'] * 3
    res = llm_label.label(sheets / "sheet_r1.csv", root, tmp_path / "llm", kf, samples=3, repo_of=lambda a: "x", opener=_opener(ans))
    diff = llm_label.compare([tmp_path / "llm" / s for s in res["sheets"]], sheets / "key.json")
    assert len(diff) == 1 and diff[0]["harness"] == "yes/L3" and diff[0]["llm_q2"] == "invalid" and "copies" in diff[0]["note"]
    ans = ['{"q1":"true","q1_reason":"a","q2":"valid","q2_reason":"b"}'] * 3
    res = llm_label.label(sheets / "sheet_r1.csv", root, tmp_path / "llm2", kf, samples=3, repo_of=lambda a: "x", opener=_opener(ans))
    assert llm_label.compare([tmp_path / "llm2" / s for s in res["sheets"]], sheets / "key.json") == []
