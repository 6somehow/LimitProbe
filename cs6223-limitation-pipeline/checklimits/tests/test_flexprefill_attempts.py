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
    # the negative runs the whole sparse path (real get_active_blocks + CPU stand-ins) and returns
    assert r.negative.effect is False and r.negative.exception is None
    assert r.negative.returned.startswith("Tensor(1, 512, 2, 128)")
    assert {m.symbol.rsplit(".", 1)[1]: (m.on_path, m.sim_class) for m in r.fidelity.mocks} == {
        "triton_bnhd_pool": (False, "independent_native"), "triton_block_wise_attention": (False, "repo_reference")}
    assert r.audit.rate == 1.0 and r.fidelity.ast_diff.statements_changed == 0 and r.fidelity.ast_diff.git_status_clean
    assert r.oracle.verified_tier == "O4" and r.oracle.revisions_after_first_run == 0
    # observations: the verdict rests on direct evidence; the downstream behaviour is supplementary and simulated
    bearing = [i for i in r.information if i.verdict_bearing]
    assert len(bearing) == 2 and {i.evidence_state for i in bearing} == {"direct"}
    extra = [i for i in r.information if not i.verdict_bearing]
    assert len(extra) == 1 and extra[0].evidence_state == "simulated:fake" and len(extra[0].depends_on_mocks) == 2
    # every defeater has been measured and eliminated
    c = r.confidence
    assert {d.id: d.status for d in c.defeaters} == {f"D{i}": "eliminated" for i in range(1, 15)}
    assert c.level == "L3" and not c.calibrated and c.next_steps == []
    mu = r.checks.mutation
    assert mu.generated >= 4 and mu.killed == mu.generated and mu.wilson_lower >= 0.5
    assert r.checks.bva.adjacent and r.checks.bva.full_scale_positive and r.checks.bva.full_scale_negative is False
    assert r.checks.repeat.runs == 5 and r.checks.repeat.identical and r.checks.replay.ok
    out = harness.write_outputs(res, tmp_path)
    json.loads(out["report"].read_text())
