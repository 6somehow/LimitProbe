from pathlib import Path

import pytest
from pydantic import TypeAdapter

from codeside.evaluate import evaluate_regions
from codeside.extractor import ExtractConfig, extract
from schema.models import Region

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"


def _toy():
    return extract(ExtractConfig(repo=FIX, entry="toy_module.py::sparse_attention", artifact_id="toy"))


def _by(regions, outcome):
    return [r for r in regions if r.outcome == outcome]


def test_reject_includes_callee_assert():
    exprs = {r.condition.expr for r in _by(_toy(), "reject")}
    assert "not (seq_len > 0)" in exprs
    assert "not (block_size in {32, 64, 128})" in exprs


def test_fallback_detected_with_boundary():
    fb = _by(_toy(), "fallback")
    assert len(fb) == 1 and fb[0].condition.expr == "seq_len < 2 * block_size"


def test_state_env_suspicious_variant_mechanism():
    regions = _toy()
    assert len(_by(regions, "state_dependent")) == 1
    assert len(_by(regions, "env_dependent")) == 1
    sus = _by(regions, "suspicious")
    assert len(sus) == 1 and sus[0].condition.expr == "block_size != 128"
    assert _by(regions, "mechanism_variant")[0].condition.expr == "x < budget"
    mech = _by(regions, "mechanism")
    assert len(mech) == 1 and "not (seq_len < 2 * block_size)" in mech[0].condition.path_prefix


def test_callee_regions_carry_path_prefix():
    callee = [r for r in _toy() if r.location.function.endswith("::sparse_kernel")][0]
    assert "not (seq_len < 2 * block_size)" in callee.condition.path_prefix
    assert callee.call_chain[0].endswith("::sparse_attention")


PILOT = ROOT / "third_party" / "FlexPrefill"


@pytest.mark.skipif(not PILOT.is_dir(), reason="run scripts/fetch_pilot.sh first")
def test_pilot_recall_regression_guard():
    pred = extract(ExtractConfig(
        repo=PILOT, entry="flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention",
        artifact_id="flexprefill"))
    gold = TypeAdapter(list[Region]).validate_json(
        (ROOT / "data/pilot_flexprefill/gold_regions.json").read_text())
    ev = evaluate_regions(pred, gold)
    assert ev.recall >= 0.9, ev.report(gold, pred)


def test_method_entry_and_self_call():
    regions = extract(ExtractConfig(repo=FIX, entry="toy_module.py::Searcher.search", artifact_id="toy"))
    funcs = {r.location.function.split("::")[1] for r in regions}
    assert "Searcher._step" in funcs  # followed self._step(...)
    assert any(r.outcome == "fallback" for r in regions)
    rej = [r for r in regions if r.outcome == "reject"]
    assert rej and rej[0].condition.expr == "not (lr > 0)"
