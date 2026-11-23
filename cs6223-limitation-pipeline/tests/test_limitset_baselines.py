"""Offline tests for the baseline command's current planning interface."""
import pytest
from pipeline import limitset_baselines as baseline


def test_execution_fails_closed():
    with pytest.raises(SystemExit) as exc:
        baseline.main(['--method', 'b1', '--split', 'validation'])
    assert exc.value.code == 2


def test_rejects_case_outside_split():
    with pytest.raises(SystemExit) as exc:
        baseline.main(['--method', 'b2', '--split', 'validation', '--case', 'CS6223-12', '--dry-run'])
    assert exc.value.code == 2
