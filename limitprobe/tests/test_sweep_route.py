import json
from pathlib import Path

from codeside.extractor import ExtractConfig, extract
from codeside.sweep_extractor import chunk_file, import_graph, select_scope, extract_sweep

FIX = Path(__file__).resolve().parent / "fixtures"
FILE = "hybrid_module.py"
CFG = ExtractConfig(repo=FIX, entry=f"{FILE}::top", artifact_id="toy")


class Canned:
    """Fake model: answers every chunk with the same items and records the prompts."""

    def __init__(self, items, fail=False):
        self.items, self.fail, self.prompts = items, fail, []

    def complete(self, system, user):
        self.prompts.append(user)
        if self.fail:
            raise RuntimeError("boom")
        return json.dumps(self.items)


def _repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "core.py").write_text("from . import util\n\ndef entry(x):\n    if x:\n        return util.f(x)\n")
    (tmp_path / "pkg" / "util.py").write_text("import pkg.deep\n\ndef f(x):\n    return x\n")
    (tmp_path / "pkg" / "deep.py").write_text("import pkg.deeper\n")
    (tmp_path / "pkg" / "deeper.py").write_text("y = 1\n")
    (tmp_path / "pkg" / "caller.py").write_text("from pkg.core import entry\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("from pkg.core import entry\n")
    return [str(p.relative_to(tmp_path)) for p in sorted(tmp_path.rglob("*.py"))]


def test_import_graph_resolves_relative_absolute_and_module_imports(tmp_path):
    files = _repo(tmp_path)
    g = import_graph(tmp_path, files, (".",))
    assert g["pkg/core.py"] == {"pkg/util.py", "pkg/__init__.py"}
    assert g["pkg/util.py"] == {"pkg/deep.py"}
    assert "pkg/core.py" in g["pkg/caller.py"]


def test_scope_follows_imports_two_levels_and_callers_one_level_and_skips_tests(tmp_path):
    scope = select_scope(tmp_path, ["pkg/core.py"], (".",), _repo(tmp_path))
    assert list(scope)[0] == "pkg/core.py"
    assert {"pkg/util.py", "pkg/deep.py", "pkg/caller.py"} <= set(scope)
    assert "pkg/deeper.py" not in scope  # three levels away
    assert "tests/t.py" not in scope
    assert "caller" in scope["pkg/caller.py"]


def test_chunks_skip_code_without_any_branch(tmp_path):
    (tmp_path / "m.py").write_text("def a(x):\n    return x\n\ndef b(x):\n    if x:\n        raise ValueError\n")
    chunks, skipped = chunk_file(tmp_path, "m.py", "r")
    assert [(c.start, c.end) for c in chunks] == [(1, 6)] and skipped == 0
    (tmp_path / "n.py").write_text("def a(x):\n    return x\n")
    assert chunk_file(tmp_path, "n.py", "r") == ([], 1)


def test_sweep_keeps_route_a_and_validates_items():
    items = [
        {"line": 34, "code": "if warm:", "condition": "warm", "outcome": "mechanism_variant", "detail": "skews"},
        {"line": 17, "code": "assert mode == \"never\"", "condition": "mode != 'never'", "outcome": "reject",
         "detail": "outside the walk"},
        {"line": 34, "code": "if cold:", "condition": "warm", "outcome": "fallback", "detail": "bad quote"},
        {"line": 999, "code": "x", "condition": "x", "outcome": "reject", "detail": "out of chunk"},
        {"line": 33, "code": "assert x is not None", "condition": "x is None", "outcome": "reject", "detail": "dup of A"},
    ]
    client = Canned(items)
    res = extract_sweep([CFG], client, paper="toy")
    static = extract(CFG)
    assert len(res.regions) == len(static) + 2
    added = res.regions[len(static):]
    assert {(r.location.line_start, r.notes) for r in added} == {
        (34, "sweep: inside the static walk"), (17, "sweep: outside the static walk")}
    reasons = {r["_reason"] for r in res.meta["rejected_items"]}
    assert {"code quote not on that line", "line outside the code shown"} <= reasons
    assert res.meta["duplicates"] >= 1 and res.meta["chunks"] == len(client.prompts) == 1
    assert "Paper: toy" in client.prompts[0] and "hybrid_module.py:34:     if warm:" in client.prompts[0]


def test_failed_calls_are_recorded_and_route_a_stays():
    res = extract_sweep([CFG], Canned([], fail=True))
    assert len(res.regions) == len(extract(CFG)) and res.meta["failed_calls"]


def test_decision_lines_cover_tests_raises_and_conditional_expressions():
    from codeside.sweep_extractor import decision_lines
    src = ("def f(x, y):\n    a = 1\n    if (x and\n            y):\n        raise ValueError\n"
           "    b = 2 if x else 3\n    assert y\n    try:\n        pass\n    except KeyError:\n        pass\n")
    assert decision_lines(src) == {3, 4, 5, 6, 7, 10}


def test_items_on_plain_assignments_are_rejected(tmp_path):
    (tmp_path / "m.py").write_text("def top(cfg):\n    g = cfg.gamma\n    if g > 1:\n        return 0\n    return g\n")
    cfg = ExtractConfig(repo=tmp_path, entry="m.py::top", artifact_id="t")
    items = [{"line": 2, "code": "g = cfg.gamma", "condition": "cfg", "outcome": "mechanism_variant", "detail": "d"},
             {"line": 3, "code": "if g > 1:", "condition": "g > 1", "outcome": "fallback", "detail": "d"}]
    res = extract_sweep([cfg], Canned(items))
    assert [r["_reason"] for r in res.meta["rejected_items"]] == ["line is not a decision point"]


def test_scope_reads_a_symlinked_file_once_under_its_real_path(tmp_path):
    files = _repo(tmp_path)
    (tmp_path / "pkg" / "alias.py").symlink_to("core.py")
    (tmp_path / "pkg" / "user.py").write_text("from pkg import alias\n")
    scope = select_scope(tmp_path, ["pkg/core.py"], (".",), files + ["pkg/alias.py", "pkg/user.py"])
    assert "pkg/alias.py" not in scope and "pkg/core.py" in scope


def test_relevance_filter_drops_only_additions_and_keeps_items_whose_check_failed(monkeypatch):
    from codeside import relevance_filter
    from codeside.relevance_filter import filter_additions

    monkeypatch.setattr(relevance_filter, "BACKOFF_SECONDS", 0)

    class Judge:
        def complete(self, system, user):
            if ":34," in user or "hybrid_module.py:34" in user:
                return '{"verdict": "useful", "reason": "r"}'
            if "hybrid_module.py:17" in user:
                return '{"verdict": "not_useful", "reason": "r"}'
            raise RuntimeError("api down")

    regs = extract_sweep([CFG], Canned([
        {"line": 34, "code": "if warm:", "condition": "warm", "outcome": "mechanism_variant", "detail": "d"},
        {"line": 17, "code": "assert mode == \"never\"", "condition": "mode != 'never'", "outcome": "reject", "detail": "d"},
        {"line": 11, "code": "assert mode in", "condition": "mode not in {'a', 'b'}", "outcome": "reject", "detail": "d"},
    ])).regions
    base = len(extract(CFG))
    added = regs[base:]
    kept, log = filter_additions(Judge(), FIX, added, "toy", [CFG.entry], workers=1)
    lines = {r.location.line_start for r in kept}
    assert 34 in lines and 17 not in lines
    assert log["counts"]["not_useful"] == 1
    assert log["counts"]["error"] == len(added) - 2 and all(r in kept for r in added if r.location.line_start not in (17, 34))
