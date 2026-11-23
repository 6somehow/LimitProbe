# Run the entire pipeline with one command (2026-11-11)

The paper side (Zhaopeng, steps 1 + 3a), code side (Wanting, steps 2 + 3b), and integration (step 4) share one entry point: `python -m pipeline` (code in `pipeline/run.py`). Given a paper and its repository, it outputs **all limitations from both sides** for that paper, in the same format currently handed to Shanghao (`limitations_for_tests.json` + `HANDOFF.md`).

The existing five papers (FlexPrefill, SparTA, MInference, InfiniGen, NNSmith) do not need to be rerun: each step skips and reuses existing output.

## Running a new paper

```bash
# 0. One-time setup: install paper-side dependencies (Python package paperprobe + Pi agent node_modules)
python -m pipeline setup-paperside

# 1. Register the paper: write data/<id>/artifact.json (commit must be the full hash; entry is a function implementing the paper's mechanism, possibly multiple)
python -m pipeline init --id mypaper --title "..." --paper-url https://arxiv.org/abs/... \
  --repo-url https://github.com/org/repo --commit <40-digit hash> --domain sparse_attention \
  --entry pkg/module.py::main_function --entry pkg/other.py::Class.method \
  [--package-root src]             # Needed only when the import root is not the repository root

# 2. Check what is missing
python -m pipeline status mypaper

# 3. Run (calls models and costs money; the paper side is most expensive and requires explicit --run-paper-side)
python -m pipeline run mypaper --pdf /path/to/paper.pdf --run-paper-side

# 4. Test side (Shanghao's checklimits): one report.json per Finding, summarized in LIMITATIONS.md
python -m pipeline test mypaper [--run-agent] [--strict]
```

Results:

| File | Contents |
|---|---|
| `results/step4/<id>/limitations_for_tests.json` | All limitations from both sides for this paper (after deduplication, classification, priority and witness_hint) |
| `results/step4/<id>/HANDOFF.md` | Instructions for the test side (generated on demand by the `doc` stage; not committed) |
| `results/step4/limitations_for_tests.json`, `HANDOFF.md` (generated, not committed) | All papers combined (automatically refreshed each time) |
| `results/tests/<id>/<finding_id>/report.json` | `pipeline test`: test record per Finding (judgment and tier if tested, reason code if not) |
| `results/tests/<id>/index.json`, `ENV.json`, `pipeline_test.log` | Summary and 1:1 check, environment preflight, complete test-side output |
| `results/report/<id>/LIMITATIONS.md` | Summary report, with tiers marked uncalibrated |

It can also be called from Python: `from pipeline.run import run`.

## One entry point: `doctor` and `e2e` (2026-11-17)

Configuration comes only from environment variables (or `.env` in the root directory, with environment variables taking precedence; see `.env.example` for a template):

| Variable | Meaning |
|---|---|
| `SOCLAAS_API_KEY` | Real key. Only the relay process receives it; other processes receive a placeholder |
| `SOCLAAS_BASE_URL` | Upstream model service address, such as `https://host/v1` |
| `SOCLAAS_IFACE` | Interface bound to relay outbound traffic, default `eth0`; set empty for normal routing |
| `PIPELINE_MODEL` | Model name for records and cache, default `x-test-2` (research model; changing it causes cache misses). **Does not read `SOCLAAS_MODEL`** |

```bash
# 0. One-time setup: python -m pipeline setup-paperside; pip install -e ".[llm,verify,dev]"
# 1. Register the paper: python -m pipeline init --id X ...
# 2. Pre-run checks (no model call; --live makes one GET /models call through the relay to verify key, address and interface)
python -m pipeline doctor X --paper-side --agent --live --pdf paper.pdf
# 3. One command: checks -> start relay -> steps 1 through 4 -> test (with --provision) -> stop relay
python -m pipeline e2e X --pdf paper.pdf --run-paper-side --run-agent
```

`e2e` first performs all static `doctor` checks and one live call. Any FAIL stops it before spending money or cloning (exit code 1, message `stopped: ...`). The relay is fixed at `127.0.0.1:8787` (the code agent's sandbox configuration hard-codes this port); an existing listening relay is reused and is neither started nor stopped by the command. All stages skip existing output, so rerunning the same command after a failure resumes progress; the paper side under `--run-paper-side` does not resume an incomplete request, see `checklimits/HANDOFF.md` §0. `pipeline test` also has `--provision`.

## Untestable Findings and papers without code (2026-11-18)

* `python -m pipeline e2e <id> ...` adds an analysis by default at the end for every **untested** Finding (tier A0–A2, **not a test conclusion**, no yes/no). Add `--no-analyze` to skip analysis.
* Add analysis only, without rerunning tests: `python -m pipeline analyze <id> [--force]` (starts and stops the relay automatically).
* Papers without public code (such as Tessera): `python -m pipeline paper-only <id> --pdf P --title T --venue V`. A model reads the PDF and lists limitations; each quote must appear verbatim in the PDF or it is discarded. The highest tier is A1. Output is in `results/tests/<id>/` and `results/report/<id>/LIMITATIONS.md`.
* For tier meanings, probe rules and limitations, see `checklimits/CONFIDENCE_SPEC.md` §22.
* For code requiring a GPU, the agent uses a CPU substitute and uses `sim_check` to demonstrate that the substitute agrees with the reference (numerically or symbolically), see §23.

## What each step does

| Step | Action | Owner's code | Output | Model call |
|---|---|---|---|---|
| fetch | Clone repository at commit and place PDF | — | `third_party/<Repo>`, `third_party/papers/<id>.pdf` | No |
| code | Step 2 final route B: B-sweep and B-agent (both start from route A) → review → merge → Limitation | Wanting `codeside/` | `out/routes_*/<id>/`, `out/pipeline_ps/<id>/limitations.json` | Yes |
| paper | Steps 1 + 3a: `run_complete_corpus.py` (independently find mechanisms → split behaviors → one Pi agent per mechanism checks source → interface) then `finalize_handoff.py` | Zhaopeng `paperside/` | `paperside/handoffs/paper-side-v1/<id>/` | Yes (most expensive) |
| verify3b | Step 3b: whether each code-side item is documented in the paper / README / docstring | Wanting | `out/pipeline_ps/<id>/3b.json` | Yes |
| step4 | Deduplication, classification, priority, witness_hint | Wanting | `results/step4/<id>/` | Yes (cached) |
| doc | Generate instructions | Wanting | `HANDOFF.md` | No |

**test** (`python -m pipeline test <id>`, 2026-11-15): invokes `python -m checklimits test <id> --results-root <pipeline root>/results` in `checklimits/`; see `checklimits/CONTRACT_TEST_REPORT.md` for the interface. It is not a step of `run`: with `--run-agent`, each Finding runs a code agent (5 to 15 minutes).

- Without `--run-agent`, it only re-audits existing test packages in `checklimits/agent_results/` and `results/tests/<id>/`; Findings that can be judged but lack a test package are marked `not_run(not_attempted)`.
- Exit codes follow section 6 of the contract: 0 means the report is complete (including `not_run`); 2 indicates input error, 3 mismatched items, and 1 a test-side exception, stopping with an explanation. 4 (only with `--strict`) means the report was written but contains `not_run` due to environment, agent or harness reasons, and exits as a failure.
- The test line in `status`: `done` means the report is complete and generated from the current step 4 file; `stale` means step 4 was rerun and tests must be rerun; `todo` means no report exists yet.
- The test side preflights the tested repository's environment (`ENV.json`) and installs nothing. If dependencies are missing, Findings that can be judged are marked `not_run(env_unavailable)`, with the reason in the report.

The order is code → paper → verify3b: Zhaopeng's `finalize_handoff.py` reads code-side limitations (`results/pipeline/<id>/limitations.json`, placed automatically by the pipeline), and 3b needs the paper-side `paper_side.json`.

- **Skipping and rerunning**: fetch, code, paper and verify3b check whether output exists and skip if it does; delete the corresponding output to rerun. step4 and doc rerun every time (LLM answers are cached, so they are fast). `--until <step>` runs through the specified step.
- **Why the paper side requires explicit enabling**: it starts one Pi coding agent per mechanism, making far more calls than other steps; it also writes to `paperside/` (run records `paperside/runs/`, handoff packages `paperside/handoffs/`). Without `--run-paper-side`, it stops with an explanation if the handoff package is missing. A package run separately by Zhaopeng can also be placed directly in `paperside/handoffs/paper-side-v1/<id>/`.
- **Paper-side prerequisites**, handled automatically by the pipeline: register the paper's commit and PDF hash in `paperside/workstreams/zhaopeng/team-reviewed.json` (his code requires registration first); place a pinned-commit repository in `paperside/data/repos/team-<id>`. Both are data only and do not modify his code.
- **API key** is read from environment variables or `.env` and is not printed.
- Logs: code side in `out/pipeline_ps/<id>/pipeline.log`, paper side in `out/paperside_logs/<id>.log`.

## Status and limitations

- **The complete flow has not actually run on a new paper yet** (too expensive, and there is no new paper yet). Verified parts:
  - On the five papers, each step can be recognized as complete and reused, and step4 and doc can be regenerated;
  - init, fetch and status were tested with a temporary artifact, as were errors when paper-side prerequisites are missing or `--run-paper-side` is absent;
  - After paper-side dependencies were installed, all 219 of Zhaopeng's unit tests and `validate_delivery.py` passed under schema v0.1.0.
- **Schema v0.2.0 triggers Zhaopeng's hash check**: his `validate_delivery.py` and 10 unit tests compare the hash of `schema/models.py`, so they report “Shared consumer schema changed” under v0.2.0. v0.2.0 changed only Finding, not the four arrays and Limitation he outputs. Once the team confirms v0.2.0, he needs to update this hash. I did not change his files.
- Some paper-side hard-coding applies only to the five papers (such as the SparTA-specific script). New papers use the general `run_complete_corpus.py` flow without a manual `review-adjustments.json`, so the interface has fewer revisions than the five delivered packages.
- The code side uses only the first run (`run1`), consistent with the current results for the five papers.
