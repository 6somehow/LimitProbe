import json

import pytest

from scorer_limitset import FakeJudge, score
from scorer_limitset.scoring import FIELDS, wilson


def fixture():
    label = {"case_id": "CS6223-01", "category_code": "method_shortcoming", "critical_link_zh": "cache allocation", "necessary_conditions_zh": ["large input"], "defeaters_zh": ["small input"]}
    finding = {"claim": "claim", "category_code": "method_shortcoming", "mechanism": "cache allocation", "conditions": ["large input"], "evidence": [], "caveats": ["small input"]}
    return label, finding


def test_repeats_and_novel():
    label, finding = fixture()
    decisions = [{"matched": True, "coverage": {f: f != "disclosure" for f in FIELDS}},
                 {"matched": False, "coverage": {f: False for f in FIELDS}}]
    records = [{"case_id": label["case_id"], "findings": [finding]}, {"case_id": label["case_id"], "findings": [finding]}]
    result = score([label], records, {"validation": [label["case_id"]], "test": []}, FakeJudge(decisions))
    case = result["cases"][0]
    assert case["stability"]["fraction"] == 0.5
    assert case["repeats"][1]["novel_for_human_review"] == [0]
    assert result["aggregate"]["split"]["validation"]["fields"]["mechanism"]["covered"] == 1
    assert wilson(0, 0)["fraction"] is None
    assert not any(term in json.dumps(result).lower() for term in ("accuracy", "precision", "false-positive"))


def test_validation_and_empty_prediction():
    label, finding = fixture()
    splits = {"validation": [], "test": [label["case_id"]]}
    result = score([label], [{"case_id": label["case_id"], "findings": []}], splits, FakeJudge())
    assert result["cases"][0]["repeats"][0]["found"] is False
    with pytest.raises(ValueError):
        score([label], [], {"validation": [], "test": []}, FakeJudge())
    with pytest.raises(ValueError):
        score([label], [{"case_id": "unknown", "findings": [finding]}], splits, FakeJudge())


def test_schema_errors_and_case_level_coverage():
    label, finding = fixture()
    label_schema = {"type": "object", "required": ["case_id", "category_code"]}
    prediction_schema = {"type": "object", "required": ["case_id", "findings"], "properties": {
        "findings": {"type": "array", "items": {"type": "object", "required": ["claim"]}}}}
    records = [{"case_id": label["case_id"], "findings": [finding]},
               {"case_id": label["case_id"], "findings": []},
               {"case_id": label["case_id"], "findings": [{}]}]
    result = score([label], records, {"validation": [label["case_id"]], "test": []},
                   FakeJudge(), label_schema, prediction_schema)
    case = result["cases"][0]
    assert case["found"] is True
    assert case["validation_errors"][0]["record"] == "prediction"
    group = result["aggregate"]["split"]["validation"]
    assert group["found"]["total"] == 1
    assert group["mean_per_repeat_rate"] == 0.5
    bad_label = dict(label)
    del bad_label["category_code"]
    case = score([bad_label], [], {"validation": [label["case_id"]], "test": []},
                 FakeJudge(), label_schema, prediction_schema)["cases"][0]
    assert case["found"] is None and case["validation_errors"]


def test_unavailable_judge_keeps_deterministic_fields():
    from scorer_limitset.scoring import JudgeUnavailable

    class Offline(FakeJudge):
        def judge(self, label, finding, signals):
            raise JudgeUnavailable()

    label, finding = fixture()
    result = score([label], [{"case_id": label["case_id"], "findings": [finding]}],
                   {"validation": [label["case_id"]], "test": []}, Offline())
    case = result["cases"][0]
    assert case["judge_unavailable"] and case["found"] is None
    assert case["fields"]["mechanism"] is None
    assert case["repeats"][0]["evaluations"][0]["signals"]["mechanism"] is True
    assert result["aggregate"]["split"]["validation"]["found"]["total"] == 0


def test_relay_batch_fallback_and_chunks(tmp_path, monkeypatch):
    import io
    import urllib.request
    from scorer_limitset.scoring import RelayJudge
    import pipeline.e2e as e2e

    (tmp_path / "evaluation").mkdir()
    (tmp_path / "evaluation" / "RUBRIC_zh.md").write_text("rubric")
    monkeypatch.setattr(e2e, "relay_up", lambda: True)
    calls = []
    decision = {"matched": True, "coverage": {f: True for f in FIELDS}}

    def transport(request, timeout):
        payload = json.loads(request.data)
        prompt = payload["messages"][1]["content"]
        data = json.loads(prompt[prompt.index("\n") + 1:])
        calls.append(data)
        if "predictions" in data:
            content = {"matches": [{"index": x["index"], **decision} for x in data["predictions"]]}
        else:
            content = decision
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", transport)
    label, finding = fixture()
    judge = RelayJudge(tmp_path, "test")
    splits = {"validation": [label["case_id"]], "test": []}
    result = score([label], [{"case_id": label["case_id"], "findings": [finding] * 61}], splits, judge)
    assert [len(c["predictions"]) for c in calls] == [30, 30, 1]
    assert result["judge"]["calls"] == 3
    assert len(result["cases"][0]["repeats"][0]["evaluations"]) == 61

    calls.clear()
    def invalid_batch(request, timeout):
        payload = json.loads(request.data)
        prompt = payload["messages"][1]["content"]
        data = json.loads(prompt[prompt.index("\n") + 1:])
        calls.append(data)
        content = {"matches": []} if "predictions" in data else decision
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode())
    monkeypatch.setattr(urllib.request, "urlopen", invalid_batch)
    judge = RelayJudge(tmp_path, "test")
    result = score([label], [{"case_id": label["case_id"], "findings": [finding, finding]}], splits, judge)
    assert result["judge"]["calls"] == 3
    assert result["cases"][0]["found"] is True


def test_relay_lifetime_and_parallel_repeats(tmp_path, monkeypatch):
    import threading
    import pipeline.e2e as e2e
    from scorer_limitset.scoring import RelayJudge

    events = []
    class Relay:
        def __init__(self, env): events.append(("init", env))
        def __enter__(self): events.append("enter")
        def __exit__(self, *args): events.append("exit")
    monkeypatch.setattr(e2e, "relay_up", lambda: False)
    monkeypatch.setattr(e2e, "Relay", Relay)
    barrier = threading.Barrier(2)
    judge = RelayJudge(tmp_path, "test", env={})
    def batch(label, findings, sigs):
        barrier.wait(timeout=3)
        return [{"matched": True, "coverage": dict(sig)} for sig in sigs]
    monkeypatch.setattr(judge, "judge_batch", batch)
    label, finding = fixture()
    score([label], [{"case_id": label["case_id"], "findings": [finding]}] * 2,
          {"validation": [label["case_id"]], "test": []}, judge, workers=2)
    assert events == [("init", {}), "enter", "exit"]


def test_english_signals_and_judge_input(tmp_path, monkeypatch):
    from scorer_limitset.scoring import RelayJudge
    label, finding = fixture()
    label['necessary_conditions_zh'] = ['大输入']
    english = dict(label, necessary_conditions_zh=['large input'])
    prompts = []
    judge = RelayJudge(tmp_path, 'test')
    monkeypatch.setattr(judge, '_request', lambda prompt: prompts.append(prompt) or {
        'matches': [{'index': 0, 'matched': True, 'coverage': {f: True for f in FIELDS}}]})
    monkeypatch.setattr(judge, '__enter__', lambda: judge)
    import pipeline.e2e as e2e
    monkeypatch.setattr(e2e, 'relay_up', lambda: True)
    result = score([label], [{'case_id': label['case_id'], 'findings': [finding]}],
                   {'validation': [label['case_id']], 'test': []}, judge, labels_en=[english])
    evaluation = result['cases'][0]['repeats'][0]['evaluations'][0]
    assert evaluation['signals']['conditions'] and not evaluation['signals_zh']['conditions']
    assert 'signals' not in prompts[0] and 'large input' in prompts[0] and '大输入' not in prompts[0]
    assert result['judge']['prompt_version'] == 'judge-v3-en'
    with pytest.raises(ValueError):
        score([label], [], {'validation': [label['case_id']], 'test': []}, FakeJudge(), labels_en=[])


def test_translation_cache_and_structure(tmp_path):
    from scripts.limitset.translate_labels import translate_labels
    label = {'case_id': 'C1', 'claim_zh': '中文', 'source_locations': ['src/file.py']}
    calls = []
    def translate(value):
        calls.append(value)
        return dict(value, claim_zh='English')
    out = tmp_path / 'labels_en.jsonl'
    translate_labels([label], out, translate, 'fake')
    translate_labels([label], out, translate, 'fake')
    assert len(calls) == 1
    assert json.loads(out.read_text())['claim_zh'] == 'English'
    assert json.loads((tmp_path / 'labels_en.manifest.json').read_text())['model_id'] == 'fake'
    with pytest.raises(ValueError):
        translate_labels([label], out, lambda v: dict(v, case_id='changed'), 'other')


def test_translated_labels_are_scorer_only():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for directory in ('pipeline', 'limitset_baselines', 'checklimits'):
        for path in (root / directory).rglob('*.py'):
            if 'scratch' in path.parts or 'node_modules' in path.parts:
                continue
            assert 'labels_en.jsonl' not in path.read_text(encoding='utf-8', errors='ignore'), str(path)
