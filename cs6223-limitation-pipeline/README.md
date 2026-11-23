# CS6223 limitation pipeline

This project finds limitations in systems-research prototypes using a paper and its repository. The paper side and code side independently identify limitations, cross-check them, integrate findings, and generate and run tests. The Limitation Testset experiments compare the pipeline with baselines and score reference coverage. See [the artifact map](docs/ARTIFACT.md) and [documentation index](docs/INDEX.md).

## Pipeline

1. The paper side extracts claims and limitations from the paper; the code side examines implementation regions using static and model-assisted routes.
2. Each side checks the other side's limitations against its evidence. Findings are integrated with provenance and test hints.
3. The test side generates and executes tests and records results. The Limitset runner also supports paper-only, mechanism, and optional swarm generators; baselines and a separate judge enable comparison.

## Repository layout

- `schema/`: shared models and schemas.
- `codeside/`: code extraction, verification, and finding integration.
- `paperside/`: teammate's paper-side implementation.
- `paperside_bridge/`: paper-side and swarm handoff conversion.
- `checklimits/`: test generation and execution harness.
- `pipeline/`: orchestration and Limitset runner.
- `scorer_limitset/`: reference coverage scorer.
- `confidence_limitset/`: confidence model.
- `limitset_baselines/`: baseline implementations.
- `scripts/`: data preparation, experiments, and reporting.
- `tests/`: pipeline tests and fixtures.
- `data/`: artifact metadata and derived dataset records.
- `results/`: committed derived findings and experimental results.
- `docs/`: specifications, reports, and development notes.
- `examples/`: offline demo and fixtures (no keys, network or PDFs needed).

The git repository also holds `tools/` (agent dispatch scripts), `development/` (task packages and project workflow records) and `docs/harness/`; they are development scaffolding and are left out of the course ZIP archive.

## Requirements and setup

Python 3.10 or newer is required; the recorded environment uses Python 3.14.10. Other versions in the declared range have not all been tested. The artifact's offline demo does not need a GPU. Individual third-party prototypes or their tests can require additional packages, different versions, or a GPU. Node is needed only for the optional swarm lane.

```bash
conda env create -f environment.yml
conda activate findlimit
pip install -e ".[dev,llm,verify]"
```

The project requires `pydantic`; the selected extras install `pytest`, `openai`, `python-dotenv`, `anthropic`, `pymupdf` (imported as `fitz`), `pypdf`, `jsonschema`, `rank-bm25`, and `z3-solver`. The separate `solver` extra also provides `z3-solver`. Prototype-specific tests may additionally need `torch`, `einops`, `transformers`, and `triton`; see `checklimits/ENV.md` for the historical environment and version caveats.

## Model service

Model runs use an OpenAI-compatible relay at `127.0.0.1:8787`. Give the real service credential only to the relay; child processes receive a placeholder key and the local relay URL. Configure using environment variable names `SOCLAAS_API_KEY`, `SOCLAAS_BASE_URL`, `SOCLAAS_IFACE`, and `PIPELINE_MODEL`; do not commit credentials. A second or third relay can listen on ports 8788 or 8789. Generator overrides include `LIMITSET_GEN_MODEL`, `LIMITSET_GEN_RELAY_PORT`, and `LIMITSET_GEN_OMIT_SAMPLING`; judge overrides include `LIMITSET_JUDGE_MODEL`, `LIMITSET_JUDGE_RELAY_PORT`, `LIMITSET_JUDGE_TIMEOUT`, and `LIMITSET_JUDGE_CHUNK`. See [runner](docs/12_limitset_runner.md) and [scoring](docs/12_limitset_scoring.md) for details.

## Run

```bash
# Offline tests and synthetic demo
python -m pytest -q
bash examples/offline_demo.sh

# With a model relay and prepared raw dataset (replace paths as appropriate)
python -m pipeline limitset run --dataset limitset2 --split test --raw /path/to/raw --out out/limitset
python -m pipeline limitset baseline --dataset limitset2 --method b1 --split test --raw /path/to/raw --out out/baseline
python -m scorer_limitset --dataset limitset2 --root /path/to/raw --labels data/limitset2/labels.jsonl --pred out/limitset/predictions.jsonl --judge relay --out out/score

# Full pipeline for an initialized paper and its checked-out repository
python -m pipeline run flexprefill --pdf /path/to/flexprefill.pdf --run-paper-side
python -m pipeline test flexprefill --run-agent

# Reproduce tables offline from the committed results bundle
python scripts/limitset/reproduce_tables.py
```

`make test`, `make demo`, and `make tables` provide shortcuts. The table bundle and reproduction script are delivered by AR-5; they may not be present in an earlier checkout. The fake judge in the demo is deterministic and its output is not an experimental result.

## Data and status

Paper PDFs and third-party repositories are not included. Obtain repositories with `scripts/fetch_dataset.sh` or `scripts/fetch_pilot.sh`, and papers with `scripts/fetch_papers.sh`; metadata and paper URLs are in `data/*/artifact.json` and `data/limitset2/cases.jsonl`. Prepare Limitset case directories with `scripts/limitset/make_case_dir.py` and build limitset2 records with `scripts/limitset/build_limitset2.py`; raw inputs must be obtained separately. Dataset records, metadata, derived findings, and the results bundle are included where committed. Generation is blind to Limitset labels, reference material, and evaluator evidence; the scorer uses labels separately.

See [results and limitations](docs/13_limitset_results.md). Goal (c) has not been demonstrated; full use of the swarm lane is planned for the next round. The CS6223 Limitation Testset and limitset2 are project datasets; papers and prototype repositories belong to their respective third-party owners and retain their own licenses.
