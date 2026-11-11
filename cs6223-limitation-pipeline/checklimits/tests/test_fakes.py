import os
import sys

from checklimits import fakes, fidelity
from checklimits.models import MockDecl


def test_sequence_numbers_increase_across_fakes_and_tracer_counter():
    rec = fakes.Recorder()
    a = fakes.RecordingFake("a", rec)
    b = fakes.RecordingFake("b", rec)
    a.x
    mid = fakes.next_seq()
    b(1)
    seqs = [e["seq"] for e in rec.events]
    assert seqs == sorted(seqs) and seqs[0] < mid < seqs[1]


def test_behaviors():
    rec = fakes.Recorder()
    assert fakes.RecordingFake("f", rec, "return_first_arg")(7, 8) == 7
    assert fakes.RecordingFake("f", rec, "return_none")(7) is None
    assert isinstance(fakes.RecordingFake("f", rec, "record_only")(7), fakes.RecordingFake)
    assert [e["op"] for e in rec.events] == ["call", "call", "call"]


def test_fake_module_and_env_var_install(monkeypatch):
    rec = fakes.Recorder()
    decls = [MockDecl(symbol="zz_fake_mod", kind="fake_module", reason="t"),
             MockDecl(symbol="ZZ_FLAG", kind="env_var", reason="t", value="1")]
    monkeypatch.delitem(sys.modules, "zz_fake_mod", raising=False)
    monkeypatch.delenv("ZZ_FLAG", raising=False)
    fakes.install_import_time(decls, rec)
    try:
        import zz_fake_mod
        zz_fake_mod.thing.call()
        assert os.environ["ZZ_FLAG"] == "1"
        ops = [(e["symbol"], e["op"]) for e in rec.events]
        assert ("zz_fake_mod", "getattr") in ops and ("zz_fake_mod.thing", "getattr") in ops
        assert rec.accesses("ZZ_FLAG")
    finally:
        sys.modules.pop("zz_fake_mod", None)


def test_dunder_probes_are_not_recorded():
    rec = fakes.Recorder()
    f = fakes.RecordingFake("f", rec)
    assert not hasattr(f, "__wrapped__")
    assert rec.events == []


def test_patch_replaces_attribute():
    rec = fakes.Recorder()
    import types
    mod = types.ModuleType("zz_patch_target")
    mod.func = lambda x: x + 1
    sys.modules["zz_patch_target"] = mod
    try:
        fakes.install_patches([MockDecl(symbol="zz_patch_target.func", kind="patch", reason="t")], rec)
        assert mod.func(5) == 5 and rec.events[0]["symbol"] == "zz_patch_target.func"
    finally:
        del sys.modules["zz_patch_target"]


def test_on_path_rules():
    decls = [MockDecl(symbol="before", kind="fake_module", reason="r"),
             MockDecl(symbol="after", kind="fake_module", reason="r"),
             MockDecl(symbol="pkg.mod.fn", kind="patch", reason="in chain"),
             MockDecl(symbol="never", kind="fake_module", reason="r")]
    events = [{"seq": 1, "symbol": "before", "op": "call", "name": ""},
              {"seq": 9, "symbol": "after.attr", "op": "getattr", "name": ""}]
    recs = {r.symbol: r for r in fidelity.mock_records(decls, [(events, 5)], ["pkg/mod.py::fn"])}
    assert recs["before"].on_path and recs["before"].accesses_before_target == 1
    assert not recs["after"].on_path and recs["after"].accesses_total == 1
    assert recs["pkg.mod.fn"].on_path          # replaces a call-chain function
    assert not recs["never"].on_path
    # target never reached: every access counts as before the target
    recs = {r.symbol: r for r in fidelity.mock_records(decls, [(events, None)], [])}
    assert recs["after"].on_path


def test_fidelity_formulas():
    assert fidelity.s_mod(0, 100) == 1.0 and fidelity.s_mod(5, 100) == 0.0
    assert abs(fidelity.s_mock(1, 2) - 0.5) < 1e-9 and fidelity.s_mock(3, 0) == 0.0
    assert fidelity.s_entry(None, 3) == 0.25 and fidelity.s_entry(0, 1) == 1.0
    assert fidelity.s_entry(0, 3) == 1.0 and fidelity.s_entry(2, 3) == 0.0
    assert fidelity.entry_index(["a::f", "a::g"], "a::g") == 1 and fidelity.entry_index(["a::f"], "b::h") is None
