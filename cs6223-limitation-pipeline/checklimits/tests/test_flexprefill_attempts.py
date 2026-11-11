"""Integration: the hand-written F07 / F01 attempts against the real FlexPrefill checkout.

They run in the Python 3.11 venv with the repository-pinned torch 2.4.0 / triton 3.0.0
(scripts/make_venv311.sh). Skipped when the checkout or the venv is missing."""
import json

import pytest

from checklimits import harness
from checklimits.models import PIPELINE_ROOT, PROJECT_ROOT

REPO = PIPELINE_ROOT / "third_party" / "FlexPrefill"
VENV = PROJECT_ROOT / "scratch" / "venv311" / "bin" / "python"
pytestmark = pytest.mark.skipif(not (REPO / "flex_prefill").exists() or not VENV.exists(),
                                reason="FlexPrefill checkout or scratch/venv311 missing")

EXPECT = {"F07": ("T07", 1824), "F01": ("T01", 1836)}


@pytest.mark.parametrize("fid", sorted(EXPECT))
def test_attempt_confirms_finding(fid, tmp_path):
    test_id, line = EXPECT[fid]
    res = harness.run_attempt(PROJECT_ROOT / "attempts" / "flexprefill" / fid)
    r = res["report"]
    loc = f"flex_prefill/ops/flex_prefill_attention.py:{line}"
    assert r.test_id == test_id and r.verdict == "yes" and r.final_verdict == "yes" and r.exec_result == "confirmed"
    assert r.positive.target_reached and r.positive.exception.type == "AssertionError"
    assert r.positive.exception.raised_at == loc
    assert [h.outcome for h in r.positive.target_hits] == ["false"] and [h.outcome for h in r.negative.target_hits] == ["true"]
    # the negative now runs the whole sparse path (real get_active_blocks + CPU stand-ins) and returns
    assert r.negative.effect is False and r.negative.exception is None
    assert r.negative.returned.startswith("Tensor(1, 512, 2, 128)")
    # two stand-ins, both used only after the target
    assert {m.symbol.rsplit(".", 1)[1]: m.on_path for m in r.fidelity.mocks} == {
        "triton_bnhd_pool": False, "triton_block_wise_attention": False}
    assert r.fidelity.s_mock == pytest.approx(0.9) and r.fidelity.probe_effect_free
    assert r.audit.rate == 1.0 and r.fidelity.ast_diff.statements_changed == 0 and r.fidelity.ast_diff.git_status_clean
    assert r.oracle.verified_tier == "O4" and r.oracle.revisions_after_first_run == 0
    # information confidence: positive confirmed at full witness scale and independent of stand-ins
    pos, passed, after = r.information
    assert pos.confidence == 1.0 and not pos.depends_on_mocks
    assert passed.confidence == pytest.approx(0.9) and not passed.depends_on_mocks
    assert after.confidence == pytest.approx(0.9 * 0.75 * 0.9, abs=1e-3) and len(after.depends_on_mocks) == 2
    assert any("scale check" in n and "AssertionError" in n for n in r.notes)
    assert not any(n.startswith("T3") for n in r.notes)
    out = harness.write_outputs(res, tmp_path)
    json.loads(out["report"].read_text())
