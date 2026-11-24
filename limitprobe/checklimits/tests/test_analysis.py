"""Analysis lane: static check, probes run by the harness, tiers (CONFIDENCE_SPEC.md §22)."""
import json
from pathlib import Path

from checklimits import analysis as A


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "run.sh").write_text("#!/bin/sh\npython main.py --n 3\n")
    (tmp_path / "README.md").write_text("# demo\nrun it\n")
    return tmp_path


def _raw(file="run.sh", line=2, snippet="python main.py --n 3"):
    return {"finding_id": "x-F001", "summary": "script does not download the dataset", "category": "impl_deviates",
            "effect_type": "other", "level": "L2",
            "limitations": [{"paper_evidence": [{"quote": "scripts download data", "locator": "p1"}],
                             "code_evidence": [{"file": file, "line_start": line, "line_end": line, "snippet": snippet}]}]}


def _ask(**kw):
    ans = {"assessment": "supports", "reasoning": "no wget", "hardware_needed": False, "would_confirm": "run it",
           "probes": [{"file": "run.sh", "regex": "wget|curl", "expect": "absent", "control": "python main", "meaning": "no download command"}]}
    ans.update(kw)
    return lambda prompt: json.dumps(ans)


def test_static_check_finds_file_and_snippet(tmp_path):
    st = A.static_check(_raw(), _repo(tmp_path))
    assert st["grounded"] and st["items"][0]["snippet_found"] is True


def test_static_check_missing_file_and_escape(tmp_path):
    r = _repo(tmp_path)
    assert not A.static_check(_raw(file="nope.sh"), r)["grounded"]
    assert not A.static_check(_raw(file="../etc/passwd"), r)["grounded"]       # never leaves the repository


def test_probe_runs_in_harness_and_confirms(tmp_path):
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="k", ask=_ask())
    assert out["tier"] == "A2" and out["probes"][0]["status"] == "confirmed" and out["calibrated"] is False


def test_probe_contradicting_the_reading_gives_a0(tmp_path):
    r = _repo(tmp_path)
    (r / "run.sh").write_text("wget http://x\npython main.py\n")
    out = A.analyze(_raw(snippet="wget http://x", line=1), r, model="m", base_url="u", key="k", ask=_ask())
    assert out["probes"][0]["status"] == "refuted" and out["tier"] == "A0"


def test_probe_outside_cited_files_is_not_run(tmp_path):
    bad = _ask(probes=[{"file": "README.md", "regex": "x", "expect": "present"}])
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="k", ask=bad)
    assert out["probes"][0]["status"] == "not_run" and out["tier"] == "A1"


def test_paper_only_is_a1_and_no_repo_needed():
    raw = {"finding_id": "t-F001", "summary": "s", "category": "docs_only", "effect_type": "other", "level": "L2",
           "limitations": [{"paper_evidence": [{"quote": "q", "locator": "p"}], "code_evidence": []}]}
    out = A.analyze(raw, None, model="m", base_url="u", key="k", ask=_ask(probes=[]))
    assert out["tier"] == "A1" and "paper text alone" in out["tier_note"]


def test_model_failure_is_a0_and_key_not_in_result(tmp_path):
    def boom(prompt):
        raise RuntimeError("HTTP 502 from the model gateway")
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="SECRETKEY", ask=boom)
    assert out["tier"] == "A0" and "SECRETKEY" not in json.dumps(out)


def test_answer_is_cached(tmp_path):
    calls = []
    def ask(p):
        calls.append(1)
        return _ask()(p)
    kw = dict(model="m", base_url="u", key="k", cache_dir=tmp_path / "c", ask=ask)
    r = _repo(tmp_path)
    A.analyze(_raw(), r, **kw)
    A.analyze(_raw(), r, **kw)
    assert len(calls) == 1


def test_absence_probe_without_control_does_not_count(tmp_path):
    p = _ask(probes=[{"file": "run.sh", "regex": "wgett", "expect": "absent", "meaning": "typo passes"}])
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="k", ask=p)
    assert out["probes"][0]["status"] == "unanchored" and out["tier"] == "A1"


def test_absence_probe_with_control_that_misses_does_not_count(tmp_path):
    p = _ask(probes=[{"file": "run.sh", "regex": "wget", "expect": "absent", "control": "zzz", "meaning": "x"}])
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="k", ask=p)
    assert out["probes"][0]["status"] == "unanchored"


def test_empty_answer_is_retried_once(tmp_path):
    calls = []
    def ask(p):
        calls.append(1)
        return "" if len(calls) == 1 else _ask()(p)
    out = A.analyze(_raw(), _repo(tmp_path), model="m", base_url="u", key="k", ask=ask)
    assert len(calls) == 2 and out["tier"] == "A2"
