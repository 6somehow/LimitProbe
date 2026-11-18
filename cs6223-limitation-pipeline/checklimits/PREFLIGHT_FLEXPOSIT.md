# Paper P preflight: FlexPosit (MICRO 2026)

Date 2026-11-16. Candidate chosen by the team (`docs/E2E_PLAN_P0_2026-11-15.md` section 5); fallback QoServe / Niyama only if this fails.
Produced by `python -m checklimits provision flexposit --commit e42a2191a72c09f0353e801061c76b7499e137ce --extras dev`
(`checklimits/provision.py`), from an empty venv, with no hand-written install script.

| | |
|---|---|
| paper | FlexPosit: Tunable Fractional Precision for LLM Inference Accelerators (MICRO 2026), https://arxiv.org/abs/2609.04724 |
| repository | https://github.com/hplp/FlexPosit, `main`, release 0.2.1 |
| **pinned commit** | `e42a2191a72c09f0353e801061c76b7499e137ce` (2026-09-26) |
| package layout | `src/flexposit/` (about 1070 lines of Python), tests in `tests/`, RTL in `hardware/` (not used) |
| Python | 3.11 (the package supports 3.10 to 3.12); torch 2.4.1 CPU wheel, transformers 4.45.2, numpy 1.26.4: the versions in the repository's `requirements.txt` |
| GPU needed | no. The README example (Mistral-7B) needs about 17 GB of GPU memory, but the repository's tests use tiny random Llama and GPT-2 models and run on CPU. `tests/gpu/verify_on_gpu.py` is excluded |
| guards in the package | 28 `raise` statements and 208 `if` / `while` statements (`api.py`: 6 raises, `formats.py`: 8): enough for `reject` and `fallback` Findings |
| manual steps | none |

One fix the provisioner needed: the repository pins `numpy<2.0` but not `pyarrow`, so pip installs a pyarrow built for NumPy 2 and `import datasets` fails (the repository's own `test_all_modules_import` caught it). `provision` now adds `pyarrow<21` whenever numpy is pinned below 2 (`COMPAT_CONSTRAINTS`, with a unit test). Without that line the result was 59 passed, 1 failed.

What is **not** known yet: the entry points. The ranking below is only the functions the repository's own tests and docs call most. The pipeline's step 2 and the paper side decide the real ones. Suggested for `data/flexposit/artifact.json`: `src/flexposit/api.py::quantize` and `src/flexposit/api.py::plan_windows` (package root `src`).

The rest of this file is the machine-written `PREFLIGHT.md`.

---

# Preflight: flexposit

- status: **ok**
- repository `scratch/preflight/flexposit/repo` at `e42a2191a72c`
- python 3.11.16 (requires >=3.10), packages: {'accelerate': '1.10.1', 'datasets': '3.0.2', 'numpy': '1.26.4', 'pytest': '9.2.0', 'scipy': '1.15.3', 'tokenizers': '0.20.1', 'torch': '2.4.1+cpu', 'transformers': '4.45.2'}
- declared dependencies: ['torch>=2.1', 'transformers>=4.40', 'accelerate', 'datasets', 'safetensors', 'numpy', 'tqdm']; requirements.txt lines: 14
- torch installed first as `torch==2.4.1` from the CPU wheel index
- repository unchanged by the install and the tests: True

## Steps

| step | ok | note |
|---|---|---|
| create venv | yes |  |
| install torch==2.4.1 (CPU wheel) | yes |  |
| install requirements.txt pins | yes |  |
| pip install -e .[dev] | yes |  |
| import flexposit | yes | <checklimits>/scratch/preflight/flexposit/repo/src/flexposit/__init__.py
 |
| repository tests | yes | {"passed": 60, "skipped": 1} |

## Repository tests (CPU, `tests/gpu` ignored): {'passed': 60, 'skipped': 1}

## Entry point candidates (public functions the repository's tests and docs call most)

| function | defined in | mentions |
|---|---|---|
| `quantize` | flexposit/api.py::quantize | 9 |
| `search_channels` | flexposit/core.py::search_channels | 5 |
| `quantizable_layers` | flexposit/utils.py::quantizable_layers | 4 |
| `sensitivity_csv` | flexposit/api.py::sensitivity_csv | 3 |
| `plan_windows` | flexposit/api.py::plan_windows | 3 |
| `default_device` | flexposit/utils.py::default_device | 3 |
| `to_cout_first` | flexposit/utils.py::to_cout_first | 3 |
| `posit_values` | flexposit/formats.py::posit_values | 3 |
| `float_quantize` | flexposit/formats.py::float_quantize | 3 |
| `posit_quantize` | flexposit/formats.py::posit_quantize | 3 |
| `save` | flexposit/api.py::save | 2 |
| `perplexity` | flexposit/eval.py::perplexity | 2 |

This ranking is a starting point. The entry points are decided by step 2 and the paper side.
