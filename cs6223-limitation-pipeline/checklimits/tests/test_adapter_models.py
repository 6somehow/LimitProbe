from pathlib import Path

import pytest
from pydantic import ValidationError

from checklimits import adapter
from checklimits.models import PIPELINE_ROOT, AgentForm, AttemptManifest

DATA = PIPELINE_ROOT / "data" / "pilot_flexprefill"


def test_flat_hint_is_input_value():
    assert adapter.witness_to_inputs({"batch_size": 2, "q_len": 4096}) == ("input_value", [{"batch_size": 2, "q_len": 4096}])


def test_call_hint_is_event_sequence_in_numeric_order():
    hint = {"call_2": {"b": 2}, "call_10": {"b": 10}, "call_1": {"b": 1}}
    assert adapter.witness_to_inputs(hint) == ("event_sequence", [{"b": 1}, {"b": 2}, {"b": 10}])


@pytest.mark.parametrize("bad", [None, {}, {"call_1": {"a": 1}, "x": 3}, {"call_1": 5}])
def test_unsupported_hints_raise(bad):
    with pytest.raises(ValueError):
        adapter.witness_to_inputs(bad)


def test_finding_to_region_chain_on_pilot_data():
    t = adapter.load_task("F07", DATA)
    assert [r.region_id for r in t.regions] == ["R01"]
    assert t.regions[0].location.line_start == 1824
    assert t.witness_type == "input_value" and t.inputs == [{"batch_size": 2, "q_len": 4096}]
    t = adapter.load_task("F01", DATA)
    assert [r.region_id for r in t.regions] == ["R03"] and t.regions[0].location.line_start == 1836
    t = adapter.load_task("F03", DATA)
    assert t.witness_type == "event_sequence" and len(t.inputs) == 2


def test_unknown_finding():
    with pytest.raises(KeyError):
        adapter.load_task("F99", DATA)


def test_models_forbid_extra_fields():
    with pytest.raises(ValidationError):
        AttemptManifest(test_id="t", finding_id="f", artifact_id="a", region_id="r", repo_dir=".", repo_commit="c",
                        surprise=1)
    with pytest.raises(ValidationError):
        AgentForm.model_validate({"test_id": "t"})


def test_shipped_attempt_forms_parse():
    root = Path(__file__).resolve().parents[1] / "attempts" / "flexprefill"
    for fid in ("F07", "F01"):
        AttemptManifest.model_validate_json((root / fid / "manifest.json").read_text())
        AgentForm.model_validate_json((root / fid / "form.json").read_text())
