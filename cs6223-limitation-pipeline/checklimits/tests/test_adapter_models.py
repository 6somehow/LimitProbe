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


# --- step 4 hand-off (witness-v2) -------------------------------------------------------------------
STEP4 = PIPELINE_ROOT / "results" / "step4" / "flexprefill" / "limitations_for_tests.json"


def test_parse_witness_v2_gives_a_pair_and_the_names_a_driver_can_take():
    hint = {"format": "witness-v2", "kind": "input_value", "status": "solved",
            "trigger": {"head_dim": 127, "q_len": 2, "q.shape[1]": 2},
            "contrast": {"head_dim": 128, "q_len": 2, "q.shape[1]": 2},
            "atoms": {"head_dim": {"kind": "input"}, "q_len": {"kind": "local"}, "q.shape[1]": {"kind": "derived"}},
            "aliases": {"q_len": "q.shape[1]"}}
    w = adapter.parse_witness(hint)
    assert (w.format, w.kind, w.status) == ("witness-v2", "input_value", "solved")
    assert w.input_keys == {"head_dim", "q_len"} and w.trigger["head_dim"] == 127 and w.contrast["head_dim"] == 128
    assert adapter.witness_to_inputs(hint) == ("input_value", [hint["trigger"], hint["contrast"]])


def test_parse_witness_v2_event_sequence_keeps_its_kind():
    hint = {"format": "witness-v2", "kind": "event_sequence", "status": "solved", "trigger": {"a": 1}, "contrast": {"a": 0}}
    assert adapter.witness_to_inputs(hint)[0] == "event_sequence"


@pytest.mark.skipif(not STEP4.exists(), reason="step 4 hand-off missing")
def test_step4_finding_builds_a_region_from_its_limitation():
    t = adapter.load_task("flexprefill-F014", DATA, STEP4)
    assert t.source == "step4" and t.finding.category == "undisclosed" and t.finding.review in ("unreviewed", "worth_testing")
    r = t.regions[0]
    assert r.location.line_start == 1837 and r.outcome == "reject" and r.condition.expr == "not (head_dim in {16, 32, 64, 128})"
    assert r.call_chain == ["flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention"]
    assert t.witness.format == "witness-v2" and t.trigger["head_dim"] == 127 and t.witness.contrast["head_dim"] == 128


@pytest.mark.skipif(not STEP4.exists(), reason="step 4 hand-off missing")
def test_step4_records_all_parse_and_unknown_id_raises():
    import json
    ids = [r["finding_id"] for r in json.loads(STEP4.read_text())["findings"]]
    assert len(ids) == 65
    for fid in ids:                       # every record loads; paper-side ones simply have no Region
        t = adapter.load_task(fid, DATA, STEP4)
        assert t.finding.finding_id == fid
    with pytest.raises(KeyError):
        adapter.load_task("flexprefill-F999", DATA, STEP4)
