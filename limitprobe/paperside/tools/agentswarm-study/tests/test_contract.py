import json
from pathlib import Path

import pytest

from swarmlab.contract import (candidate_groups, normalize_record, parse_finding_report,
                               parse_json, validate_report)


def test_parse_fenced_json_with_preamble():
    text = 'Here is the report:\n```json\n{"paper_id":"demo","candidates":[]}\n```'
    report = parse_finding_report(text)
    assert report["data"]["paper_id"] == "demo"
    assert report["raw_candidate_count"] == 0


def test_truncated_object_is_closed_at_record_boundary():
    text = ('{"paper_id":"demo","target_execution":"not_run","candidates":[{"id":"A","title":"t"},'
            '{"id":"B","title":"trunc')
    report = parse_finding_report(text)
    assert report["raw_candidate_count"] == 1
    assert "closed_truncated_object" in report["repairs"]


def test_alias_fields_are_retained_not_dropped():
    payload = {
        "paper_id": "demo",
        "findings": [
            {
                "candidate_id": "F1",
                "name": "first-artifact reuse",
                "causal_argument": "one saved artifact is replayed",
                "conditions": "same graph",
                "downstream": "only the first input is tested",
                "paper_quotes": [{"page_number": 3, "text": "saved input"}],
                "source_spans": [{"file": "pkg/run.py", "line": 10, "end_line": 20}],
                "comparison": {"controls": "graph", "changed": "inputs",
                               "metric": "coverage", "falsified_if": "no new bugs"},
            }
        ],
    }
    report = parse_finding_report(json.dumps(payload))
    assert report["raw_candidate_count"] == 1
    assert report["parsed_groups"] == ["findings"]
    record = report["records"][0]
    assert record["id"] == "F1"
    assert record["paper_evidence"] == [{"page": 3, "quote": "saved input"}]
    assert record["code_evidence"] == [{"path": "pkg/run.py", "start": 10, "end": 20}]
    assert record["minimal_comparison"]["vary"] == "inputs"


def test_bare_candidate_list_is_kept():
    text = '[{"id":"X","title":"one"}]'
    report = parse_finding_report(text)
    assert report["records"][0]["id"] == "X"


def test_nested_wrapper_is_searched():
    data = {"answer": {"results": [{"id": "N1", "rule": "r"}]}}
    groups = candidate_groups(data)
    assert groups and groups[0][1] == "answer.results"


def test_missing_json_raises():
    with pytest.raises(ValueError):
        parse_json("no report here")


class FakeEvidence:
    meta = {"paper_id": "demo"}
    pages = [{"page": 1, "text": "The compiler saves the first valid input."}]

    def quote_in_page(self, page, quote):
        return page == 1 and quote == "saves the first valid input"

    def span_any_read(self, path, start, end):
        return False


def test_validation_flags_unread_span_and_reports_quote():
    data = {"paper_id": "demo", "target_execution": "not_run", "candidates": [{
        "id": "A", "title": "t", "rule": "r", "trigger": "g", "mitigation": "m",
        "consequence": "c",
        "paper_evidence": [{"page": 1, "quote": "saves the first valid input"}],
        "code_evidence": [{"path": "a.py", "start": 1, "end": 2}],
        "minimal_comparison": {"fixed": "f", "vary": "v", "baseline": "b",
                               "observable": "o", "refuted_if": "r"},
    }]}
    result = validate_report(data, FakeEvidence())
    assert result["json_parsed"]
    assert any("never read" in issue for issue in result["issues"])
