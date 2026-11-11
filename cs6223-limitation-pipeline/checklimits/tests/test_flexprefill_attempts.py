"""Integration: the hand-written F07 / F01 attempts against the real FlexPrefill checkout.

Skipped when third_party/FlexPrefill, torch or triton are not available."""
import json
from importlib import util

import pytest

from checklimits import harness
from checklimits.models import PIPELINE_ROOT, PROJECT_ROOT

REPO = PIPELINE_ROOT / "third_party" / "FlexPrefill"
pytestmark = pytest.mark.skipif(
    not (REPO / "flex_prefill").exists() or util.find_spec("torch") is None or util.find_spec("triton") is None,
    reason="FlexPrefill checkout or torch/triton missing")

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
    assert r.negative.target_reached and r.negative.effect is False
    assert r.negative.exception is None or r.negative.exception.raised_at != loc
    assert [h.outcome for h in r.positive.target_hits] == ["false"] and [h.outcome for h in r.negative.target_hits] == ["true"]
    assert r.audit.rate == 1.0 and r.fidelity.mocks == [] and r.fidelity.probe_effect_free
    assert r.fidelity.ast_diff.statements_changed == 0 and r.fidelity.ast_diff.git_status_clean
    assert r.evidence.condition_translated is False and r.oracle.verified_tier == "O4"
    out = harness.write_outputs(res, tmp_path)
    json.loads(out["report"].read_text())
