"""The adapter takes the real call chain from step 4 (witness_hint.call_chain) when it is there."""
from checklimits.adapter import load_task
from checklimits.models import PIPELINE_ROOT

DATA = PIPELINE_ROOT / "data" / "pilot_flexprefill"
FILE = PIPELINE_ROOT / "results" / "step4" / "flexprefill" / "limitations_for_tests.json"
OPS = "flex_prefill/ops/flex_prefill_attention.py"


def test_region_gets_the_chain_with_the_middle_function():
    r = load_task("flexprefill-F007", DATA, FILE).regions[0]
    assert r.call_chain == [f"{OPS}::flex_prefill_attention", f"{OPS}::triton_block_wise_attention",
                            f"{OPS}::triton_block_wise_prefill_attention"]
    assert r.entry_point == r.call_chain[0] and r.location.function == r.call_chain[-1]


def test_without_a_chain_the_old_two_step_chain_is_kept():
    t = load_task("flexprefill-F019", DATA, FILE)  # vLLM patch: step 4 finds no chain from the entry
    assert t.finding.witness_hint["call_chain_status"] == "not_found"
    assert len(t.regions[0].call_chain) <= 2
