from pathlib import Path

from codeside.dedup import CallGraph, dedup_additions, normalise
from schema.models import CodeLocation, Condition, Region

SRC = '''\
def entry(q, mode):
    assert q.dim() == 4
    return inner(q) if mode else other(q)


def inner(q):
    assert q.dim() == 4
    return q


def other(q):
    if q.dim() != 4:
        raise ValueError
    return q


def side(q):
    assert q.dim() == 4
    return q


def caller_a(cfg):
    if cfg.flag:
        return 1


def caller_b(cfg):
    if cfg.flag:
        return 2
'''


def reg(line, fn, expr, outcome="reject", rid="D"):
    return Region(region_id=f"{rid}{line}", artifact_id="t", entry_point="m.py::entry",
                  condition=Condition(expr=expr), outcome=outcome,
                  location=CodeLocation(file="m.py", line_start=line, function=f"m.py::{fn}"), provenance="llm")


def test_normalise_treats_negated_comparisons_as_the_same():
    assert normalise("not (q.dim() == 4)") == normalise("q.dim() != 4")
    assert normalise("not (x in {1, 2})") == normalise("x not in {1, 2}")


def test_checked_upstream_is_dropped_and_route_a_is_untouched(tmp_path):
    (tmp_path / "m.py").write_text(SRC)
    static = [reg(2, "entry", "not (q.dim() == 4)", rid="R")]
    added = [reg(7, "inner", "q.dim() != 4"), reg(12, "other", "q.dim() != 4"), reg(18, "side", "q.dim() != 4"),
             reg(23, "caller_a", "cfg.flag", "mechanism_variant"), reg(28, "caller_b", "cfg.flag", "mechanism_variant")]
    kept, log = dedup_additions(tmp_path, static, added, CallGraph(tmp_path))
    lines = [r.location.line_start for r in kept]
    assert 7 not in lines and 12 not in lines  # only called from entry, which already checks it
    assert 18 in lines and "route-A region at line 2" in next(r for r in kept if r.location.line_start == 18).notes
    assert 23 in lines and 28 not in lines  # same switch twice in one file
    assert "line 28" in next(r for r in kept if r.location.line_start == 23).notes
    assert sorted(log["checked_upstream"]) == ["m.py:12", "m.py:7"]


def test_to_limitations_exports_variants_only_when_asked(tmp_path):
    import json, subprocess, sys
    regs = [reg(3, "entry", "mode", "mechanism_variant"), reg(2, "entry", "q.dim() != 4")]
    src = tmp_path / "r.json"
    src.write_text(json.dumps([r.model_dump(mode="json") for r in regs]))
    def run(*extra):
        out = tmp_path / f"l{len(extra)}.json"
        subprocess.run([sys.executable, "-m", "codeside.cli", "to-limitations", "--regions", str(src), "--out", str(out), *extra],
                       check=True, capture_output=True, cwd=Path(__file__).resolve().parents[1])
        return json.loads(out.read_text())
    assert [l["effect_type"] for l in run()] == ["reject"]
    assert sorted(l["effect_type"] for l in run("--include-variants")) == ["path_change", "reject"]
