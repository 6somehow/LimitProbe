import pytest

from checklimits import agent_batch
from checklimits.models import PIPELINE_ROOT

FF = "results/step4/flexprefill/limitations_for_tests.json"
pytestmark = pytest.mark.skipif(not (PIPELINE_ROOT / FF).exists() or
                                not (PIPELINE_ROOT / "third_party/FlexPrefill/flex_prefill").exists(),
                                reason="step 4 hand-off or FlexPrefill checkout missing")


def test_selection_keeps_only_judgeable_findings_with_a_solved_witness():
    chosen, skipped = agent_batch.select(FF)
    assert len(chosen) + len(skipped) == 65
    for fid in ("flexprefill-F014", "flexprefill-F053", "flexprefill-F026", "flexprefill-F012"):
        assert fid in chosen                      # the four findings the agent has already been run on
    assert "flexprefill-F052" in chosen
    reasons = " ".join(skipped.values())
    assert "no code location" in reasons and "infeasible" in reasons and "suspicious" in reasons
    assert not set(chosen) & set(skipped)


def test_every_skip_has_a_reason():
    _, skipped = agent_batch.select(FF)
    assert skipped and all(isinstance(v, str) and len(v) > 8 for v in skipped.values())
