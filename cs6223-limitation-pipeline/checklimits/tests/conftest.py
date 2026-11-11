import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
# Make `import checklimits` resolve to the package in checklimits/checklimits even when pytest is
# started from the pipeline root (where the project directory itself looks like a namespace package),
# and make scoring_prototype importable for the regression test.
for p in (str(PROJECT), str(PROJECT / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)
