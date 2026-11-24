"""provision: the parts that need no network (declared requirements, torch pin, pytest summary, entry candidates)."""
from pathlib import Path

from checklimits import provision as pv


def _repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / "src" / "pkg").mkdir(parents=True)
    (r / "tests").mkdir()
    (r / "pyproject.toml").write_text('[project]\nname = "my-pkg"\nrequires-python = ">=3.10"\n'
                                      'dependencies = ["torch>=2.1", "numpy"]\n[project.optional-dependencies]\ndev = ["pytest"]\n')
    (r / "requirements.txt").write_text("# pins\ntorch==2.4.1\nnumpy<2.0\ntqdm\n")
    (r / "src" / "pkg" / "__init__.py").write_text("")
    (r / "src" / "pkg" / "api.py").write_text("def quantize(x):\n    return _helper(x)\n\ndef _helper(x):\n    return x\n\n"
                                              "def rarely_used():\n    pass\n\nclass C:\n    def method(self):\n        pass\n")
    (r / "tests" / "test_api.py").write_text("from pkg.api import quantize\n\ndef test_a():\n    quantize(1)\n    quantize(2)\n")
    (r / "README.md").write_text("Use `quantize(model)` and `C().method()`.\n")
    return r


def test_declared_requirements_and_torch_pin(tmp_path):
    req = pv.declared_requirements(_repo(tmp_path))
    assert req["package"] == "my-pkg" and req["requires_python"] == ">=3.10"
    assert req["pyproject"] == ["torch>=2.1", "numpy"] and req["requirements"] == ["torch==2.4.1", "numpy<2.0", "tqdm"]
    assert req["extras"] == {"dev": ["pytest"]}
    assert pv.torch_spec(req) == "torch==2.4.1"                       # the exact pin wins over the minimum
    assert pv.torch_spec({"requirements": [], "pyproject": ["torch>=2.1"]}) == "torch"
    assert pv.torch_spec({"requirements": [], "pyproject": ["torchvision", "numpy"]}) is None


def test_missing_files_give_empty_requirements(tmp_path):
    assert pv.declared_requirements(tmp_path)["pyproject"] == []


def test_numpy_below_2_adds_the_pyarrow_constraint():
    assert pv.compat_pins(["numpy<2.0", "tqdm"]) == ["pyarrow<21"]
    assert pv.compat_pins(["numpy==1.26.4"]) == ["pyarrow<21"]
    assert pv.compat_pins(["numpy>=1.24", "tqdm"]) == []


def test_pytest_summary_parsing():
    out = "FAILED tests/a.py::t1 - X\nERROR tests/b.py::t2 - Y\n====== 2 failed, 50 passed, 1 skipped, 1 error in 1.5s ======\n"
    s = pv.parse_pytest_summary(out)
    assert s["counts"] == {"failed": 2, "passed": 50, "skipped": 1, "error": 1}
    assert s["failed"] == ["tests/a.py::t1", "tests/b.py::t2"]
    assert pv.parse_pytest_summary("60 passed, 1 skipped in 4.55s\n")["counts"] == {"passed": 60, "skipped": 1}
    assert pv.parse_pytest_summary("no tests ran")["counts"] == {}


def test_entry_candidates_rank_by_tests_and_docs(tmp_path):
    c = pv.entry_candidates(_repo(tmp_path))
    assert c[0]["name"] == "quantize" and c[0]["defined_in"] == ["pkg/api.py::quantize"] and c[0]["mentions"] >= 3
    assert "_helper" not in {x["name"] for x in c}                    # private names are not entry points
    assert "rarely_used" not in {x["name"] for x in c}                # never called by a test or a doc
    assert "method" in {x["name"] for x in c}                          # mentioned in the README


def test_provision_without_install_records_a_missing_interpreter(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(pv, "PROJECT_ROOT", tmp_path)
    repo = _repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    rec = pv.provision("toyp", repo, install=False, run_tests=False, out_dir=tmp_path / "out")
    assert rec["status"] == "not_ok" and any("no interpreter" in r for r in rec["reasons"])
    assert (tmp_path / "out" / "PREFLIGHT.md").read_text().startswith("# Preflight: toyp")


def test_install_pins_skips_only_what_cannot_be_installed(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, log, timeout, cwd=None, env=None):
        calls.append(cmd[-1])
        bad = "flashinfer>=0.0.5"
        joined = open(cmd[-1]).read() if cmd[-2] == "-r" else cmd[-1]
        return (1 if bad in joined else 0), ""

    monkeypatch.setattr(pv, "_run", fake_run)
    ok, skipped = pv.install_pins(tmp_path / "py", ["numpy  # fast", "flashinfer>=0.0.5", "ray"],
                                  tmp_path / "pins.txt", tmp_path / "log", 10)
    assert not ok and skipped == ["flashinfer>=0.0.5"]
    assert "numpy" in calls and not any("#" in c for c in calls if not c.endswith("pins.txt"))
    ok, skipped = pv.install_pins(tmp_path / "py", ["numpy"], tmp_path / "pins.txt", tmp_path / "log", 10)
    assert ok and skipped == []


def test_setup_py_requires_reads_the_literal_list(tmp_path):
    from checklimits.provision import setup_py_requires
    (tmp_path / "setup.py").write_text('import torch\nINSTALL_REQUIRES = [\n    "transformers>=4.37.0",\n    "torch",\n    "flash_attn",\n]\nQ = ["x"]\n')
    assert setup_py_requires(tmp_path) == ["transformers>=4.37.0", "torch", "flash_attn"]
    assert setup_py_requires(tmp_path / "none") == []


def test_gpu_only_missing_module_is_named_only_for_gpu_packages():
    from checklimits.e2e import _gpu_only_missing
    assert _gpu_only_missing("ModuleNotFoundError: No module named 'flash_attn'") == "flash_attn"
    assert _gpu_only_missing("ModuleNotFoundError: No module named 'flash_attn.layers'") == "flash_attn"
    assert _gpu_only_missing("ModuleNotFoundError: No module named 'transformers'") is None
    assert _gpu_only_missing("ImportError: boom") is None
