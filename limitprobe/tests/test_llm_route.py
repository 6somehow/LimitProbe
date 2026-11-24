import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from codeside.evaluate import compare_routes
from codeside.extractor import ExtractConfig, extract
from codeside.llm_extractor import LLMOutputError, SoclaasClient, parse_json, collect_context, extract_with_llm, validate_items

FIX = Path(__file__).resolve().parent / "fixtures"
CFG = ExtractConfig(repo=FIX, entry="toy_module.py::sparse_attention", artifact_id="toy")


class FakeClient:
    """Returns a canned answer: two good items, one hallucinated line, one bad outcome."""

    def __init__(self):
        self.prompt = None

    def complete(self, system, user):
        self.prompt = user
        return "Here you go:\n" + json.dumps([
            {"file": "toy_module.py", "function": "sparse_attention", "line": 17,
             "condition": "seq_len < 2 * block_size", "outcome": "fallback", "detail": "dense"},
            {"file": "toy_module.py", "function": "sparse_kernel", "line": 11,
             "condition": "block_size not in {32, 64, 128}", "outcome": "reject"},
            {"file": "toy_module.py", "function": "sparse_attention", "line": 999,
             "condition": "x > 0", "outcome": "reject"},
            {"file": "toy_module.py", "function": "sparse_attention", "line": 16,
             "condition": "seq_len <= 0", "outcome": "crash"},
        ])


def test_context_contains_entry_and_callees_with_line_numbers():
    ctx = collect_context(CFG)
    quals = {c.qual for c in ctx}
    assert {"sparse_attention", "dense_attention", "sparse_kernel"} <= quals
    assert "toy_module.py:17:" in next(c.text for c in ctx if c.qual == "sparse_attention")


def test_validation_rejects_hallucinations_and_counts_them():
    client = FakeClient()
    res = extract_with_llm(CFG, client)
    assert "toy_module.py:17:" in client.prompt
    assert len(res.regions) == 2 and res.raw_items == 4
    assert {r["_reason"] for r in res.rejected} == {"line outside function", "unknown outcome"}
    assert res.hallucination_rate == 0.5
    assert all(r.provenance == "llm" for r in res.regions)


def test_compare_routes_table():
    static = extract(CFG)
    llm = extract_with_llm(CFG, FakeClient()).regions
    gold = [r for r in static if r.outcome in ("fallback", "reject")]
    table = compare_routes(gold, {"static": static, "llm": llm},
                           meta={"llm": {"rejected": 2, "hallucination_rate": 0.5}})
    lines = table.splitlines()
    assert lines[0].split()[0] == "route" and lines[1].startswith("static") and lines[2].startswith("llm")
    assert "0.50" in lines[2]


def _soclaas(monkeypatch, finish_reason):
    openai = pytest.importorskip("openai")
    pytest.importorskip("dotenv")
    monkeypatch.setenv("SOCLAAS_API_KEY", "test-key")
    monkeypatch.setenv("SOCLAAS_BASE_URL", "http://example.invalid/v1/")
    calls = []

    def create(**kw):
        calls.append(kw)
        msg = SimpleNamespace(content="[]")
        return SimpleNamespace(model="served-model", usage=SimpleNamespace(prompt_tokens=3, completion_tokens=4),
                               choices=[SimpleNamespace(message=msg, finish_reason=finish_reason)])

    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    return SoclaasClient(model="x-test-2"), calls


def test_soclaas_client_sends_settings_and_records_served_model(monkeypatch):
    client, calls = _soclaas(monkeypatch, "stop")
    assert client.complete("sys", "usr") == "[]"
    assert client.resolved_model == "served-model"
    assert (client.prompt_tokens, client.completion_tokens) == (3, 4)
    assert calls[0]["model"] == "x-test-2" and calls[0]["temperature"] == 0.0
    assert calls[0]["reasoning_effort"] == "none"
    assert calls[0]["messages"][0] == {"role": "system", "content": "sys"}


def test_soclaas_client_raises_on_truncated_output(monkeypatch):
    client, _ = _soclaas(monkeypatch, "length")
    with pytest.raises(RuntimeError, match="truncated"):
        client.complete("sys", "usr")


def test_validation_accepts_function_names_as_written_in_context_headers():
    item = {"file": "toy_module.py", "function": "toy_module.py::sparse_attention", "line": 18,
            "condition": "seq_len < 2 * block_size", "outcome": "fallback"}
    regions, rejected = validate_items([item], collect_context(CFG), CFG)
    assert len(regions) == 1 and not rejected
    assert regions[0].location.function == "toy_module.py::sparse_attention"


def test_unreadable_output_is_an_error_not_an_empty_answer():
    class Broken:
        def complete(self, system, user):
            return "sorry, I cannot do that"

    with pytest.raises(LLMOutputError):
        extract_with_llm(CFG, Broken())


def test_validation_rejects_conditions_with_names_absent_from_the_function():
    item = {"file": "toy_module.py", "function": "sparse_attention", "line": 18,
            "condition": "made_up_flag > 3", "outcome": "fallback"}
    regions, rejected = validate_items([item], collect_context(CFG), CFG)
    assert not regions and "made_up_flag" in rejected[0]["_reason"]


def test_parse_json_reads_prose_fences_and_a_bare_object():
    assert parse_json('Sure:\n```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert parse_json('{"a": 1}', list) == [{"a": 1}]
    assert parse_json('note [x] {"a": 1}', dict) == {"a": 1}
    with pytest.raises(LLMOutputError):
        parse_json("[1, 2", list)
