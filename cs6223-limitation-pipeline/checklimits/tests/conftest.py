import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
# Make `import checklimits` resolve to the package in checklimits/checklimits even when pytest is
# started from the pipeline root (where the project directory itself looks like a namespace package),
# and make scoring_prototype importable for the regression test.
for p in (str(PROJECT), str(PROJECT / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_oracle_locks(tmp_path_factory, monkeypatch):
    """Tests never touch the real locks/ directory."""
    from checklimits import harness
    monkeypatch.setattr(harness, "LOCKS_DIR", tmp_path_factory.mktemp("locks"))
