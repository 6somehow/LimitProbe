import json
from pathlib import Path

from checklimits import paper_only as PO

TEXT = "[page 1]\nOur system achieves 2.3x speedup over the baseline on 64 GPUs.\nThe baseline takes 41.2 s and ours 17.9 s per step."


def test_quote_must_appear_in_text():
    flat = PO._flat(TEXT)
    assert PO.quote_in_text("achieves 2.3x speedup over the baseline on 64 GPUs", flat)
    assert not PO.quote_in_text("achieves 9.9x speedup over the baseline", flat)
    assert not PO.quote_in_text("short", flat)


def test_safe_eval_and_check_numbers_must_come_from_quotes():
    assert PO.safe_eval("41.2/17.9") - 2.3016 < 1e-3
    for bad in ("__import__('os')", "2**99", "a+1"):
        try:
            PO.safe_eval(bad)
            raise AssertionError(bad)
        except Exception as e:
            assert not isinstance(e, AssertionError)
    q = ["The baseline takes 41.2 s and ours 17.9 s per step."]
    ok = PO.run_check({"expr": "41.2/17.9", "expect": "about 2.3"}, q)
    assert ok["status"] == "evaluated" and abs(ok["value"] - 2.3017) < 1e-3
    assert PO.run_check({"expr": "41.2/12.0"}, q)["status"] == "not_run"          # 12.0 is not in a quote


def test_candidate_with_invented_quote_is_dropped_and_records_are_a1():
    cands = [{"kind": "evaluation_scope", "claim": "c", "limitation": "only 64 GPUs",
              "quotes": ["achieves 2.3x speedup over the baseline on 64 GPUs", "The baseline takes 41.2 s and ours 17.9 s per step."], "locator": "p1",
              "check": {"expr": "41.2/17.9", "expect": "2.3"}, "would_confirm": "run on 8 GPUs"},
             {"kind": "other", "claim": "c", "limitation": "l", "quotes": ["this sentence is not in the paper at all"]}]
    recs, dropped = PO.build_records("t", cands, PO._flat(TEXT), "m", {})
    assert dropped == 1 and len(recs) == 1
    r = recs[0]
    assert r.finding_id == "t-P001" and r.analysis["tier"] == "A1" and r.analysis["calibrated"] is False
    assert r.status == "not_run" and r.not_run.code == "no_code_location"
    assert r.analysis["arithmetic_check"]["status"] == "evaluated"


def test_two_passes_cache_and_dedupe(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"pdf")
    monkeypatch.setattr(PO, "pdf_text", lambda _: TEXT)
    quote = "achieves 2.3x speedup over the baseline on 64 GPUs"
    first = {"kind": "evaluation_scope", "claim": "surface", "quotes": [quote]}
    second = {"kind": "method_shortcoming", "claim": "limit", "mechanism": "because", "conditions": ["when"], "reasoning": "fact -> premise -> inference", "quotes": [quote]}
    bad = {**second, "quotes": ["invented words absent from the paper"]}
    responses = [json.dumps({"candidates": [first]}), json.dumps({"candidates": [second, bad]})]
    calls = []
    def ask(prompt):
        calls.append(prompt)
        return responses.pop(0)
    kwargs = dict(title="t", venue="v", results_root=tmp_path, model="m", base_url="", key="", ask=ask)
    result = PO.run_paper_only("a", pdf, **kwargs)
    assert result["n_records"] == 1 and result["dropped"] == 1 and len(calls) == 2
    report = json.loads((tmp_path / "tests/a/a-P001/report.json").read_text())
    assert report["provenance"]["prompt_version"] == PO.MECHANISM_PROMPT_VERSION
    assert report["analysis"]["mechanism"] == "because" and report["analysis"]["tier"] == "A1"
    PO.run_paper_only("a", pdf, **kwargs)
    assert len(calls) == 2
