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
