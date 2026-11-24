# CS6223 limitation pipeline

Find, cross-check and test the **limitations** of systems-research prototypes, starting from a paper and its code repository.

A paper-side analysis and a code-side analysis each propose limitations. Each side checks the other side's claims against its own evidence, the results are integrated into *findings* with provenance and test hints, and a test side generates and runs tests to confirm them. A separate experiment harness (the *Limitation Testset* runner, baselines and a blind scorer) measures how many reference limitations each generator recovers.

This repository started as a course project (NUS CS6223) by three teammates: the code side and integration, the paper side, and the test side.

> **Status: research prototype.** The measured results are small-sample and descriptive. Read [`docs/13_limitset_results.md`](docs/13_limitset_results.md) before drawing conclusions. A per-finding confidence band exists in code but is not demonstrated in the reported runs.

## Results at a glance

On *limitset2* (11 papers, 22 human-reviewed reference limitations, 1 repeat, one LLM judge), the share of reference limitations covered by each system:

| Generator model | One-request baseline (B1) | Mechanism generator (v3c) | v3c + B1 |
|---|---|---|---|
| Claude Sonnet 5.5 | 5 / 22 | 12 / 22 | 15 / 22 |
| `x-test-2` (DeepSeek-class model behind a relay) | 3 / 22 | 7 / 22 | 8 / 22 |

The 95% Wilson intervals are wide (for example 12 / 22 is [0.35, 0.73]); most differences are not significant. Most v3c findings cite paraphrased rather than verbatim quotes, and the labels were drafted by a model of the same family as one generator. All caveats are listed in the results document. Coverage of reference limitations is **not** accuracy: extra findings are candidates for human review, not errors.

## Quick start (offline, no keys, no GPU, no PDFs)

```bash
conda env create -f environment.yml        # or: python -m venv .venv && source .venv/bin/activate
conda activate findlimit
pip install -e ".[dev,llm,verify]"

python -m pytest -q                        # unit tests
bash examples/offline_demo.sh              # synthetic scorer + comparison demo (fake judge)
python scripts/limitset/reproduce_tables.py --root results/limitset_final --out tables.md
```

`make test`, `make demo` and `make tables` are shortcuts. The demo uses a deterministic fake judge, so its output is a smoke test, not an experimental result. `reproduce_tables.py` rebuilds the results tables from the committed bundle in `results/limitset_final/` without any model call.

## How it works

1. **Paper side** extracts claims and limitations from the paper. **Code side** examines implementation regions with static analysis, with an LLM-assisted route, or both (`codeside/`).
2. Each side verifies the other's limitations against its evidence. Findings are integrated with provenance, a triggering condition and a witness hint (`codeside/integrate.py`).
3. **Test side** (`checklimits/`) turns findings into tests and runs them, recording the evidence tier of each result.
4. The **Limitation Testset runner** (`pipeline/limitset.py`) runs generators on isolated per-paper inputs: paper-only reading, the mechanism generator (seven generic reasoning lenses), an optional agent-swarm lane, and baselines. `scorer_limitset/` scores coverage of reference limitations with an LLM judge that sees the reference but the generators never do.

Design rules: LLMs are used to understand and locate; decisions that can be deterministic are made by code or a solver; every quote must appear verbatim in its source, with a check in code; generators never read labels.

## Repository layout

| Path | Contents |
|---|---|
| `schema/` | shared record models (pydantic) and exported JSON Schema |
| `codeside/` | code-side extraction, verification (3b) and finding integration (step 4) |
| `paperside/` | paper-side implementation by a teammate; see [AgentSwarm study](paperside/tools/agentswarm-study/README.md) for the Dev/Test split, A/B/S rerun commands and the end-to-end handoff |
| `paperside_bridge/` | converts swarm and paper-side output into the pipeline's records |
| `checklimits/` | test generation and execution harness (the test side) |
| `pipeline/` | one-command pipeline and the Limitset runner |
| `scorer_limitset/` | reference-coverage scorer and judge client |
| `confidence_limitset/` | confidence model (auditable evidence items, uncalibrated) |
| `limitset_baselines/` | baseline generators (one request; an agent baseline) |
| `scripts/` | data preparation, experiments, result tables |
| `data/` | artifact metadata and dataset records (see *Data and licensing*) |
| `results/` | committed findings, test reports and the final results bundle `results/limitset_final/` |
| `docs/` | specifications and reports; start with [`docs/ARTIFACT.md`](docs/ARTIFACT.md) and [`docs/INDEX.md`](docs/INDEX.md) |
| `examples/` | offline demo and fixtures |
| `tests/` | pipeline tests |

## Setup details

Python 3.10 or newer; the recorded environment is Python 3.14. Node is needed only for the optional swarm lane. No GPU is needed for the demo and the unit tests; some analyzed prototypes need extra packages (`torch`, `einops`, `transformers`, `triton`) or a GPU to run their own tests (see `checklimits/ENV.md`).

The selected extras install `pytest`, `openai`, `python-dotenv`, `anthropic`, `pymupdf`, `pypdf`, `jsonschema`, `rank-bm25` and `z3-solver`.

### Model service

Model runs go through a local OpenAI-compatible **relay** at `127.0.0.1:8787`. Only the relay process holds the real credential; child processes receive a placeholder key and the relay URL. Copy `.env.example` to `.env` (git-ignored) or export the variables `SOCLAAS_API_KEY`, `SOCLAAS_BASE_URL`, `SOCLAAS_IFACE` and `PIPELINE_MODEL`. Never commit credentials.

A second or third relay can serve a different model (ports 8788 and 8789). Generator overrides: `LIMITSET_GEN_MODEL`, `LIMITSET_GEN_RELAY_PORT`, `LIMITSET_GEN_OMIT_SAMPLING`. Judge overrides: `LIMITSET_JUDGE_MODEL`, `LIMITSET_JUDGE_RELAY_PORT`, `LIMITSET_JUDGE_TIMEOUT`, `LIMITSET_JUDGE_CHUNK`. See [runner](docs/12_limitset_runner.md) and [scoring](docs/12_limitset_scoring.md).

## Running with a model

```bash
# Limitset runner, baseline and scorer (prepare the raw dataset first; see "Data and licensing")
python -m pipeline limitset run --dataset limitset2 --split test --raw /path/to/raw --out out/limitset
python -m pipeline limitset baseline --dataset limitset2 --method b1 --split test --raw /path/to/raw --out out/baseline
python -m scorer_limitset --dataset limitset2 --root /path/to/raw --labels data/limitset2/labels.jsonl \
  --pred out/limitset/predictions.jsonl --judge relay --out out/score

# Full pipeline for one paper whose repository is checked out
python -m pipeline run flexprefill --pdf /path/to/flexprefill.pdf --run-paper-side
python -m pipeline test flexprefill --run-agent
```

Re-scoring with a real judge is not bit-for-bit repeatable: the judge model accepts only its default temperature. Commands for re-scoring the committed predictions are in [`results/limitset_final/README.md`](results/limitset_final/README.md).

## Data and licensing

- **Code and original documentation: MIT**, see [`LICENSE`](LICENSE).
- **Not covered by the MIT license:** the Limitation Testset records and labels in `data/limitset/`, the limitset2 labels in `data/limitset2/`, model outputs in `results/`, the paper-side artifacts in `paperside/`, and every third-party paper or repository. [`NOTICE.md`](NOTICE.md) lists each one with its terms and the steps to take before publishing.
- **Not included:** paper PDFs and the analyzed prototype repositories. Fetch repositories with `scripts/fetch_dataset.sh` or `scripts/fetch_pilot.sh` and papers with `scripts/fetch_papers.sh`. Paper URLs are in `data/*/artifact.json` and `data/limitset2/cases.jsonl`. Build per-case inputs with `scripts/limitset/make_case_dir.py`.

## Contributing

Run `python -m pytest -q` and `python -m pytest -q checklimits/tests` before sending a change. The schema is the interface between the three components: changing a field means raising `SCHEMA_VERSION`, updating `docs/02_schema.md`, re-exporting the JSON Schema and running the tests. Add a minimal fixture for every new extraction rule. Do not tune prompts or rules against the reference labels; keep a held-out set.

## Acknowledgements

Built for NUS CS6223 by three teammates: the code side and integration, the paper side (`paperside/`, including the AgentSwarm study), and the test side (`checklimits/`). The analyzed papers and prototypes belong to their authors.
