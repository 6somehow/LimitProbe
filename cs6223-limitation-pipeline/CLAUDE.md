# CLAUDE.md — CS6223 limitation pipeline (code side)

## What the project is

NUS CS6223 course project. Given a systems research paper and its code repository, the paper side and the code side
each find limitations, cross-check each other, integrate them into findings, then generate and run tests to confirm.
Full description: `docs/00_project_overview.md`.

This repository is currently developed by **Wanting (code side)**, who owns:
- Step 2: the code side finds limitations (a region table). **Both routes are built and compared** (`docs/06_two_routes.md`):
  route A static analysis `codeside/extractor.py`; route B static + LLM `codeside/hybrid_extractor.py`; B-agent free exploration `codeside/agent_extractor.py`; B-sweep chunked read-through `codeside/sweep_extractor.py` + review `codeside/relevance_filter.py`; control group, pure LLM `codeside/llm_extractor.py`
- Step 3b: code -> paper verification, `codeside/verify3b.py`; description and results in `docs/06_3b_eval.md`; the end-to-end B -> 3b run is in `docs/07_pipeline_b_3b.md`
- Step 4: integrate into Findings (dedup, classification, priority, witness_hint): `codeside/integrate.py` + `codeside/step4_llm.py` + `codeside/witness.py`; description and results in `docs/09_step4_findings.md`
  - effect-label check `codeside/effect_anchor.py`, call chain and argument mapping `codeside/callgraph.py`, replacing callee names with entry-point names `codeside/chain_bind.py` (2026-11-15, W1–W3 of `E2E_PLAN.md`); Finding IDs are stable across runs
  - process confidence `codeside/process_confidence.py` (2026-11-21): every Finding that has a code-side record carries static evidence (8 checks, repeated measurements, predicted ceiling of the test tier, an importance number; the code side does not assign a tier). It travels with the Finding to the test side; see `docs/11_process_confidence.md`
- Shared schema: `schema/models.py`

Teammates: Zhaopeng (paper side: steps 1 and 3a, agent orchestration, baseline; code in `paperside/`), Shanghao (steps 5–6: test generation and execution).

**Entry point of the whole pipeline**: `python -m pipeline run <id>` (`pipeline/run.py`, description in `docs/10_pipeline.md`).
It runs the code side, the paper side (calling the scripts in `paperside/`), 3b and step 4 in order and writes `results/step4/<id>/limitations_for_tests.json`; steps whose output already exists are skipped.

## What to do next

Read `TASKS.md` and start from the first unfinished milestone (M1 needs a meeting; code can start directly from M2).
Method details are in `docs/03_codeside_spec.md`; the background of the pilot is in `docs/04_pilot_flexprefill.md`.

**The development set is four papers**: SparTA, MInference, InfiniGen, NNSmith (`docs/05_dataset.md`,
metadata in `data/<id>/artifact.json`). Use these four for development and debugging; FlexPrefill is the annotated demonstration pilot.
Numbers on these four are development-set numbers; claims about generalization may only come from the held-out artifacts agreed at the end.

## Directories

```
schema/            shared schema (pydantic) and exported JSON Schema
codeside/          extractor.py (step 2), evaluate.py, cli.py
pipeline/          one command that runs the whole pipeline (both sides + integration)
paperside/         Zhaopeng's paper side (steps 1, 3a); do not change his code
data/<artifact>/   artifact.json, gold_*.json (manual), draft_*.json (drafts), paper_side_stub.json
docs/              overview, related work, schema notes, method specification, pilot analysis, prompt templates
tests/             pytest; fixtures/ holds minimal cases
scripts/           fetch_pilot.sh (clones the pilot at a fixed commit)
third_party/       analyzed repositories (not committed)
out/               generated results (not committed)
```

## Common commands

```bash
python -m pipeline status                       # which steps are finished for each paper
python -m pipeline run <id> --pdf P --run-paper-side   # new paper: run the whole pipeline (init first, see docs/10_pipeline.md)
python -m pipeline test <id> [--run-agent]      # test side: one report.json per Finding + LIMITATIONS.md
pip install -e ".[dev]"            # dependencies: pydantic; tests: pytest; optional: z3-solver
scripts/fetch_pilot.sh             # clone FlexPrefill @ a24b27b
scripts/fetch_dataset.sh           # clone the four papers + pilot at fixed commits from data/*/artifact.json
python -m pytest -q                # must stay green
python -m codeside.cli extract --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --out out/flexprefill_regions.json
python -m codeside.cli evaluate --pred out/flexprefill_regions.json \
  --gold data/pilot_flexprefill/gold_regions.json
python -m codeside.cli to-limitations --regions out/flexprefill_regions.json \
  --out out/flexprefill_code_limitations.json
python -m codeside.cli extract --repo third_party/InfiniGen \
  --entry speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen --artifact infinigen \
  --out out/infinigen_mha_gen.json --package-root speedup/infinigen --package-root speedup/flexgen
python -m codeside.cli extract-llm --repo third_party/FlexPrefill \
  --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
  --artifact flexprefill --model x-test-2 --out out/llm_run1.json   # needs .[llm] + .env
python -m codeside.cli compare --gold data/pilot_flexprefill/gold_regions.json \
  --pred static=out/flexprefill_regions.json --pred llm1=out/llm_run1.json
scripts/fetch_papers.sh            # download the five paper PDFs to third_party/papers/
python -m codeside.verify3b --limitations data/pilot_flexprefill/gold_code_limitations.json \
  --artifact data/pilot_flexprefill/artifact.json --pdf third_party/papers/flexprefill.pdf \
  --repo third_party/FlexPrefill --paper-side data/pilot_flexprefill/paper_side_stub.json \
  --model x-test-2 --repeats 3 --out out/3b/flexprefill.json   # needs .[verify] + .env
python scripts/eval_3b.py          # known-answer test of 3b
python scripts/run_pipeline.py --out-dir out/pipeline_ps --seed-cache out/pipeline   # B -> 3b (paper side uses the handoff package)
python scripts/run_step4.py --code-dir results/pipeline   # reproduce the committed step 4: by default it reads out/pipeline_ps (not in git, content may differ); input hashes are written to `inputs` of findings.report.json and a mismatch warns
python scripts/run_step4.py        # step 4: Finding + witness_hint, written to results/step4/ (calls a model, cached; --no-llm skips the call)
python scripts/run_step4.py --process-only   # recompute only the code-side static evidence (no model call, everything else unchanged), then run make_handoff_doc.py
python -m codeside.cli validate data/*/*.json
python -m schema.export_json_schema
```

## Rules

1. **The schema is the interface between the three of us.** Changing a field means raising `SCHEMA_VERSION`, updating `docs/02_schema.md`, re-exporting the JSON Schema and running the tests.
2. **Gold files are manual annotations; never overwrite them with a program.** Write generated results to `out/`; after review, save a draft as a new gold file.
3. **Keep decisions deterministic where possible.** An LLM is used only for understanding and locating (reading the paper, filling in dynamic dispatch, semantic matching); scope intersection, evaluation coverage and feasibility use code or z3.
4. **Evidence must be checkable.** Every record carries provenance; a quote must appear verbatim in its source and the code must check it; locations are paths relative to the repository root, line numbers refer to Artifact.commit.
5. **Every new extraction rule gets a minimal case in `tests/fixtures/`**, and evaluate is run on the pilot to see the change in recall and extra predictions.
6. **Numbers on the pilot do not show generalization.** The v0 rules were written against FlexPrefill; claims about generalization may only come from new artifacts whose rules were not tuned (TASKS.md M3).
7. Do not modify code under `third_party/`.
8. **The two routes must be compared fairly**: same entry and context, same checks, same gold and matching rules; record the LLM model ID, temperature and prompt version; do not repeatedly tune a prompt or rule against the gold.

## Current state (at handoff)

- Schema v0.2.0 (draft, to be confirmed by the three of us: 7 Finding categories + review fields); all 165 tests pass (`checklimits/` has another 239). The limitset work later raised the schema to 0.2.1 and the main test count, see `docs/12_swarm_interface.md` and `docs/13_limitset_results.md`.
- `python -m pipeline test <id>` calls the test side (`checklimits/CONTRACT_TEST_REPORT.md`) and writes `results/tests/<id>/` and `results/report/<id>/LIMITATIONS.md`.
- Route B (static + LLM) ran 3 times on the pilot and on every entry of the four papers (`x-test-2`, prompt `hybrid-v3`, only adding, never deleting the results of A); results are in `out/routes/`.
- Route A on the pilot: recall 16/16, extra 10, cond_exact 13/13.
- The extractor supports class methods (`file::Class.method`), `self.method()`, one level of nested functions (`file::outer.inner`) and `--package-root`.
- The four development papers have pinned versions and a first run; the gaps it exposed are listed in `docs/05_dataset.md` and TASKS.md M2.
- Extractor v0 on the pilot: recall 16/16, 10 extra predictions (6 unreachable paths, 2 redundant, 2 internal invariants), corresponding to TASKS.md M2.
- Paper side delivered: `paperside/handoffs/paper-side-v1/<paper>/paper_side.json`; `run_pipeline.py` uses it by default (only FlexPrefill has one parameter mapping, `tau`; every other scope is unknown).
- Step 4 is implemented: 289 Findings for five papers are in `results/step4/`; the single file handed to Shanghai is `results/step4/limitations_for_tests.json`, described in `results/step4/HANDOFF.md` (generated by `scripts/make_handoff_doc.py`).
- 3b is implemented: on the pilot all 13 paper-level limitations are not_found; it agrees 8/13 with the unreviewed draft result, see `docs/06_3b_eval.md`.
- Appendix F.2 of the paper compares block_size 64 and 128, while S2 of the stub only says 128, which makes the scope judgement of F02 wrong; Zhaopeng needs to handle it.
- F02 (hard-coded `// 128`) and F03 (module-level causal_mask cache) are candidate findings and have not been confirmed by execution yet.
