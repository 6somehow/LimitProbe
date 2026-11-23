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
    assert case["fields"]["mechanism"] is True
    assert result["aggregate"]["split"]["validation"]["found"]["total"] == 0
