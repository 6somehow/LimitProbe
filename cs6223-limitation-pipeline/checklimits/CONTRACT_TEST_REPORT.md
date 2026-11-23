# test / report interface contract (version `checklimits-test-report/1`, 2026-11-15)

Corresponds to P0-4 in `docs/E2E_PLAN_P0_2026-11-15.md`. Producer: Shanghao. Consumers: Wanting (the `pipeline` test stage) and the whole group (the report).

## 1. Invocation

Run from the `cs6223-limitation-pipeline/checklimits/` directory (`python -m checklimits` fails from the repository root because the directories have the same name; pipeline specifies `cwd=` when invoking it):

```bash
python -m checklimits envcheck <artifact>                 # Environment precheck; writes ENV.json
python -m checklimits test     <artifact> [选项]          # Select, test, and write report.json and LIMITATIONS.md
python -m checklimits report   <artifact> [--results-root] # Regenerate LIMITATIONS.md using existing report.json files only
```

In the command above, `[选项]` is an original-language placeholder [options].

Options for `test`:

| Option | Meaning |
|---|---|
| `--results-root DIR` | Output root, default `checklimits/results/e2e`. Pass `<pipeline 根>/results` when connecting the pipeline. |
| `--attempts-root DIR` (repeatable) | Directory to search for existing test packages (attempts). Default: `agent_results/` and `<results-root>/tests/<artifact>/`. |
| `--run-agent` | Run a code agent for each Finding that can be assessed but has no test package (requires relay and SoCLaaS credentials; about 5 to 15 minutes per Finding). Without it, these Findings are recorded as `not_run(not_attempted)`. |
| `--only ID` (repeatable) | Test only the specified Finding; the report still includes all Findings, using existing records for the rest (see §5). |
| `--workers N` | Parallelism, default 3. |
| `--fast` | Perform fewer repetitions and mutations (for smoke testing only; the level will be lower). |
| `--strict` | Exit with code 4 if there is any `env_unavailable` / `agent_failed` / `harness_error`. |
| `--skip-envcheck` | Skip the environment precheck. |
| `--provision` | If the environment precheck fails but the repository is checked out, first create `scratch/venv_<artifact>` (`provision`: install the CPU version of torch and dependencies at the versions pinned by the repository, without running the repository's own tests), then check again. Record the process in `provisioned` in `ENV.json`. The pipeline `test` command does not yet pass this option through. |

In `<pipeline 根>/results`, `根` is an original-language placeholder [root].

Inputs: `results/step4/<artifact>/limitations_for_tests.json` (schema 0.2.0) and `data/*/artifact.json` (the one whose `artifact_id` matches).

## 2. Output layout

Under `<results-root>`:

```
tests/<artifact>/ENV.json                    Environment precheck result
tests/<artifact>/index.json                  Summary: input count, record count, counts by status, 1:1 check result
tests/<artifact>/<finding_id>/report.json    One per Finding, see §3
tests/<artifact>/<finding_id>/execution_report.json   Only for status=tested: full harness report (models.ExecutionReport)
tests/<artifact>/<finding_id>/testcase.json  Only for status=tested: codeside TestCase record (validated by `codeside.cli validate`)
tests/<artifact>/<finding_id>/attempt/       Only for status=tested: copy of the audited test package, replayable
report/<artifact>/LIMITATIONS.md             Summary report
```

`<finding_id>` is the full step 4 id, for example `nnsmith-F004`.

## 3. `report.json` (one per Finding, whether tested or not)

```json
{
  "schema_version": "checklimits-test-report/1",
  "finding_id": "nnsmith-F004",
  "artifact_id": "nnsmith",
  "status": "tested",
  "not_run": null,
  "verdict": "yes",
  "level": "L1",
  "calibrated": false,
  "confidence_label": "uncalibrated",
  "level_note": "...",
  "verdict_reason": "...",
  "observed": {"positive": "AssertionError at ...", "negative": "no exception at ..."},
  "defeaters": {"D1": "eliminated", "D3": "residual", "...": "..."},
  "open_doubts": [{"id": "D3", "name": "...", "status": "residual", "evidence": "..."}],
  "next_steps": ["..."],
  "finding": {"category": "...", "step4_level": "L2", "effect_type": "path_change", "priority": 1,
              "summary": "...", "review": "worth_testing", "review_note": "...", "scope_status": "unknown",
              "witness_status": "solved", "location": "nnsmith/graph_gen.py:260", "function": "...",
              "condition": "..."},
  "evidence": {"paper": [{"quote": "...", "source": "paper", "locator": "..."}],
               "code": [{"file": "...", "line_start": 260, "function": "...", "snippet": "..."}]},
  "files": {"execution_report": "execution_report.json", "testcase": "testcase.json", "attempt": "attempt"},
  "provenance": {"findings_file": "results/step4/nnsmith/limitations_for_tests.json", "findings_sha256": "...",
                 "source": "reaudit", "attempt_origin": "agent_results/batch_nnsmith/F004-n1-f004",
                 "n_attempts_found": 1, "profile": "default-v1", "generated_at": "2026-11-15T17:00:00+08:00"}
}
```

| Field | Rule |
|---|---|
| `status` | `tested`: the harness produced a full report for this Finding (`verdict` may still be `inconclusive`). `not_run`: not run; the `not_run` field is required. |
| `not_run` | `{"code": ..., "reason": "..."}`; see §4 for `code` values. `null` when `status=tested`. |
| `verdict` | `yes` / `no` / `inconclusive`; `null` when `not_run`. |
| `level` | `L0` / `L1` / `L2` / `L3` / `invalid` / `n/a`; `null` when `not_run`. |
| `calibrated` | Currently always `false`, and `confidence_label` is always `"uncalibrated"`. The level indicates which known reasons for error have been measured and ruled out; it is **not** empirical accuracy. |
| `defeaters` | `eliminated` / `residual` / `open` / `refuted`; see `CONFIDENCE_SPEC.md` for definitions. |
| `open_doubts` | All defeaters that are not `eliminated`, with their evidence; the unresolved doubts in the report. |
| `evidence` | Taken from the original step 4 data without rewriting. |

`analysis` (optional, 2026-11-18): a `not_run` record may carry an analysis block with fields `kind="analysis_only"`, `tier` (A0/A1/A2), `assessment`, `reasoning`, `static`, `probes`, `would_confirm`, and `calibrated=false`. It is not a test; `status` remains `not_run`, and `verdict`/`level` remain `null`. See `CONFIDENCE_SPEC.md` §22.

Compatibility rule: only add optional fields; do not rename or remove fields or change enum meanings. Any such change requires a bump to `checklimits-test-report/2`.

## 4. `not_run.code` values

| code | Meaning | Who can resolve it |
|---|---|---|
| `no_code_location` | Finding has no code location (paper-side only, or Limitation has no code_evidence). | Zhaopeng (Z3 provides testability hints and code locations). |
| `outcome_unsupported` | The harness cannot assess the effect type or target statement (for example, `reject` is attached to a statement that cannot raise an exception; `fallback` is attached to an assignment; the effect is `suspicious`). | Wanting (W2 labeling conventions). |
| `witness_unusable` | The step 4 witness has no usable trigger (status `trigger_only`, `unsat`, `unknown`). | Wanting (W1, W3). |
| `env_unavailable` | The repository is not checked out, or the interpreter or dependencies for the artifact are unavailable. | Shanghao (S3) or manual environment setup. **An environment failure is not a Finding failure.** |
| `input_unreadable` | The Finding or its location cannot be read (file missing, line number out of range, JSON field missing). | Upstream data. |
| `not_attempted` | The harness can assess it, but there is no test package and `--run-agent` was not enabled. | Run `--run-agent`. |
| `agent_failed` | `--run-agent` was enabled, but the agent did not produce an auditable test package (budget exhausted, crash). | Rerun. |
| `harness_error` | The harness raised an exception while reauditing an existing test package. | Shanghao (bug). |

## 5. No dropped entries (1:1)

* `n_input` in `index.json` is the number of Findings in the step 4 file, `n_records` is the number of `report.json` files, and each Finding appears once as a table row and once as a subsection in `LIMITATIONS.md`. The three counts must be equal and the id sets must match; `one_to_one` is `true`.
* If they do not match, `test` exits with code 3 and lists the differences in `problems` in `index.json`.
* `--only` limits which Findings are tested in this run; records for the other Findings are reused from existing `report.json` files under `<results-root>/tests/<artifact>/`, or recorded as `not_run` per §4 if none exists.

## 6. Exit codes

| Code | Meaning |
|---|---|
| 0 | Report complete (1:1 check passed). `not_run` does not affect this. |
| 2 | Input error: artifact not registered, findings file missing, or not schema 0.2.0. |
| 3 | 1:1 check failed, or written files cannot be read back. |
| 4 | Only with `--strict`: report complete, but there are `not_run` records for environment, agent, or harness reasons. |
| 1 | Other unhandled exception. |

`envcheck` exit codes: 0 for `ok`, 4 for `not_ok`, and 2 for input error.

The last output on stdout is a JSON object (`artifact`, `n_input`, `counts`, `one_to_one`, `report`, `exit_code`) that pipeline can parse directly.

## 7. Environment precheck `ENV.json`

```json
{"artifact_id": "nnsmith", "status": "ok", "reasons": [],
 "repo": {"path": "third_party/nnsmith", "exists": true, "head": "a8307f2...", "expected": "a8307f2...", "matches": true, "clean": true},
 "python": {"path": "scratch/venv_nnsmith/bin/python", "exists": true, "version": "3.11.9"},
 "imports": [{"module": "nnsmith.graph_gen", "ok": true, "error": null}],
 "execution_env": ["cpu"]}
```

`status` is `ok` or `not_ok`. When `not_ok`, all Findings that can be assessed are recorded as `not_run(env_unavailable)`, with `reason` referring to the reasons in ENV.json. The precheck only checks and records; it does not install anything.

## 8. Outside today's scope

* The `python -m pipeline test <id>` integration (W6) is in `pipeline/run.py` and belongs to Wanting. Integration only needs to invoke `python -m checklimits test <id> --results-root ../results` with `cwd=checklimits/` and interpret exit codes per §6.
* Level calibration (C1).
