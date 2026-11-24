# Mechanism-level Pi investigation

Uses the actual Pi SDK (`@earendil-works/pi-coding-agent` 1.5.2, the current package from pi-mono's successor repository) and SoCLaaS's `x-test-2` route. The separate two-request native tool probe returned `deepseek-v4.1-flash-1017`. This is one Pi session per mechanism, not one model judgment per behavior. Behaviors remain a frozen checklist.

The agent can list tracked paths, search literal text, read pinned Git blobs, look up Python static symbol edges, and read original paper pages. No built-in shell/edit tools, project extensions or target execution are enabled. File reads are capped; final evidence must fit actually read spans. Search hits alone cannot pass the citation check. API credentials are referenced through the environment and never saved in run artifacts.

Run from the project root, using a fresh output directory:

```sh
npm ci --prefix tools/pi-mechanism-agent --ignore-scripts --no-audit --no-fund
.venv/bin/python tools/pi-mechanism-agent/prepare.py --output runs/sparta-pi-mechanism-M02-next
source ~/.config/soclaas/soclaas.env
node tools/pi-mechanism-agent/run.mjs runs/sparta-pi-mechanism-M02-next
node --test tools/pi-mechanism-agent/validation.test.mjs
```

Each run saves the exact runner snapshot, system prompt, initial paper/mechanism/behavior input, actual request bodies, completed model messages, tool results, read spans, raw final response and validation status. Image payloads in logs are replaced by hashes; original images and hashes are preserved in the prepared input. `runner.snapshot.mjs` is the actually used code; later refactoring does not rewrite it.

Budgets: at most 14 model requests, 45 tool calls, 900 seconds, 6,500 output tokens per response. The observed cumulative token target is 104,080; a final request may exceed this soft target because usage arrives after each response. Tool completion does not imply semantic correctness.

Completed attempts: v1 rejected for unread final citations (6 requests, 9 tools, 115,981 tokens); v2 accepted structurally (9 requests, 18 tools, 103,760 tokens). Both are preserved. v2 raw labels: 5 partial, 9 unlocated. They are not independent human judgments. README and sampled experiments point to NNI's `sparta_artifact` branch; that dependency has not been inspected. Do not infer whole-system absence from the local mock entry.

Official SDK source: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## Explicit judgments with the installed artifact dependency

`run-adjudication.mjs` uses a different output contract: every frozen behavior has a `local_entry` and an `artifact` verdict, explicit implemented/missing parts, aligned entry, read citations and counterevidence. Labels are `implemented`, `partially_implemented`, `not_implemented`, `not_assessable`; no `unlocated` label is permitted. Absence of a proof assertion is not proof of nontermination. The structured validator does not decide semantic correctness.

The dependency must be read before decisive artifact verdicts are accepted. `prepare_judgment.py` freezes the dependency and generates AST navigation for the actual `propagate_mask` method invoked by experimental scripts. The method name is source navigation, not a supplied semantic verdict. The primary README branch resolves to the same primary commit; `image/Dockerfile` installs a separate `zheng-ningxin/nni:artifact` fork, pinned here to `8c656fb380c577a984a6b4430b9d53fe91c8bd6e`. This current snapshot is not evidence of the exact historical Docker version.

```sh
.venv/bin/python tools/pi-mechanism-agent/prepare_judgment.py --output runs/sparta-pi-judgment-M02-next
source ~/.config/soclaas/soclaas.env
node tools/pi-mechanism-agent/run-adjudication.mjs runs/sparta-pi-judgment-M02-next
node --test tools/pi-mechanism-agent/judgment.test.mjs
```

`prepare_revision.py` can assemble **verbatim prior read_repo results** and the unaccepted draft into a separate revision input. `--finalize-only` forces one final model request with no tools. Supplied read ranges are recorded alongside new tool reads, with origin IDs; no model conclusion is mechanically rewritten. Finalization is now reserved on the last permitted request to prevent the hard request cap from blocking an answer. All earlier attempts, failures and costs remain in the report.

Compact finalization (`compact_finalization: true`) de-duplicates source references through evidence IDs and expands them mechanically into the canonical report. This changes transport only, never verdict semantics. The actual system prompt includes explicit semantic alignment rules: binary pruning masks can represent pruning TeSA, multiplying masks represents the union of pruned positions, separate functions can realize per-node propagation, and returning updated attributes need not literally return a graph object. A prior model draft can be reviewed against these rules; both versions and the actual prompts remain available. B08 is classified as a mathematical guarantee rather than an executable implementation obligation in this bounded protocol.

A source citation crossing adjacent read ranges is permitted; a citation crossing an unread gap is rejected. Repo aliases are part of citation identity. A prior stream error may report no token usage despite producing partial text; cumulative returned usage is then a lower bound, not complete usage or monetary cost.

## Earlier conformance run (historical four-label protocol)

The main categories now answer whether the code fulfills the paper, not how much code exists:

- `supports`: code supports the stated behavior and conditions, including equivalent realizations.
- `deviates`: a related implementation exists but an inspected step, condition, update, scheduling or return obligation differs from the paper.
- `absent`: the claimed core behavior is missing from the aligned inspected path.
- `insufficient`: a precise barrier prevents a verdict; these rows are excluded from findings.

Each row first identifies the paper requirement, original quote/page and claim type (`mechanism_step`, `semantic_effect`, `guarantee`). It then records actual code, discrepancy or uncertainty barrier, equivalence analysis and effect status separately in two pinned scopes. A scheduling mismatch does not require an observed bad output; it must not be presented as proof that outputs fail. Empty equivalence analysis is allowed only for an uncertain row whose barrier explains why the property is not assessed.

Run from the project root:

```sh
source ~/.config/soclaas/soclaas.env
.venv/bin/python tools/pi-mechanism-agent/run_conformance.py --output runs/sparta-pi-conformance-replay
node --test tools/pi-mechanism-agent/conformance.test.mjs
```

This executes two bounded Pi stages: whole-mechanism exploration/draft (at most 4 model requests and 12 new tool calls, soft 110,000 token target), then one model semantic-consistency review (soft 70,000 target). Both reuse verified exact pinned source reads; the first sees no previous verdicts. The review sees only this new-taxonomy draft and checks all paper qualifiers and cross-row consistency. There are no automatic network retries or target execution. Old implementation labels are rejected, never converted automatically. Structural gates check IDs, citation ranges and field consistency; the LLM still performs semantic judgments, so independent review remains necessary.

Realized run: `runs/sparta-pi-conformance-M02-v1` (draft) + `runs/sparta-pi-conformance-M02-v2` (review). Total 5 actual requests, 6 new tool calls, 154,501 returned tokens. In the review, A03 changed from supports to deviates because operator-type handling alone does not fulfill variation across pruning and quantization attribute kinds. M02-B06-R01 is deviates for the specified scheduling/stopping mechanism, with functional equivalence/failure not established. Actual prompts, raw outputs, both stages and full code are embedded in the main HTML.


## Current result schema: exactly three conclusions

Completed checks now use ONLY `supports`, `deviates`, or `absent`. `review_state` is separate: `completed` has one of those three verdicts; `pending` has `verdict: null` and a concrete `pending_reason`. Pending work is not a fourth result category and is excluded from conclusion counts and findings. Report structure may be complete while `assessment_complete` is false; the workflow reports remaining work instead of claiming every check is finished.

The validator rejects `insufficient` as a completed verdict and rejects a verdict attached to pending work. Existing raw prompts and model outputs are immutable. `paperprobe.conformance_view.three_conclusion_view` preserves all 13 completed model conclusions and projects previously uncompleted B08 into a workflow task with no verdict. This presentation migration makes zero API calls and is not a new semantic judgment. The main HTML shows three result categories and a separate progress/task section. The current Pi prompt follows the new schema; its actual API behavior has not been re-run solely for this presentation/schema change.

## SparTA remaining-mechanism rollout (current three-conclusion protocol)

`prepare_mechanism.py` accepts a frozen mechanism ID. It preserves the existing paper-only behaviors verbatim, unions their cited pages with the mechanism pages, and gives every exploration the same neutral README/build/core orientation. It does not provide old judgments, Wanting's findings, or a mechanism-specific ranked source packet. The Pi session selects the relevant library, experiment and dependency entries itself. There is no universal propagation entry for other mechanisms.

The available read-only repository aliases are `primary`, `nni`, `nnfusion`, `tvm`. The last two are source snapshots of the branches declared by the Dockerfile; no submodules or dependencies were built. Their pins are `be0c5ca8cc372c5571a87e17f12dcb94a9d2b690` and `2eca7030aaceaad969eb6326cf5d107ba6e6f29b`. They are not proof of the historical execution environment.

The batch freezes its actual runner, prompts, preparation code and dependency pins under `runtime/`, with SHA-256s in `protocol.json`. That runtime directory, including `prepare_mechanism.py`, is the authoritative full batch code snapshot. The older per-stage `prepare.snapshot.py` filename still contains the M02 predecessor preparer; it is not the generic preparer used for this rollout.

Nominal budget per mechanism: seven exploration requests, 24 tool calls, one complete semantic-review request. At most one additional completion request for a structurally rejected draft and one for a rejected review; zero automatic network retries. Output allowance is scaled by the frozen behavior count. Usage targets are soft (170,000 draft / 90,000 review tokens); the actual server-returned usage, requests, repairs and failures are retained. Pi reads Git blobs, never runs the target.

Real runs are `runs/sparta-remaining-preflight-v1` (M01 and M08 capacity preflight) and `runs/sparta-remaining-rollout-v1` (the other 17). Their joint index is `runs/sparta-remaining-cohort-v1/cohort.json`. M02 is reused from its existing conformance run. This is a development rollout, not a controlled accuracy experiment or a novelty claim.

```sh
# Use a fresh output directory; completed attempts cannot be overwritten.
source ~/.config/soclaas/soclaas.env
.venv/bin/python tools/pi-mechanism-agent/run_sparta_batch.py \
  --output runs/sparta-remaining-replay --workers 2
node scripts/validate_sparta_batch.mjs runs/sparta-remaining-cohort-v1
```

`validate_sparta_batch.mjs` checks every final ID and citation against its frozen runtime validator, preserves the original paper-side behaviors, and compares archived source reads with actual Git blobs at the declared commits. This verifies provenance, not the semantic correctness of model judgments. The HTML exposes both scoped judgments, every original prompt/request/response, source excerpts, revisions, failures and code snapshots. Image bytes are represented by hashes in request logs; original paper page images remain embedded in the HTML.


Completed rollout: 19 accepted mechanism reports / 192 frozen behaviors, 186 artifact verdicts (88 supports / 51 deviates / 47 absent), six pending checks in M18. Total: 188 actual requests, 277 tool calls, 4,050,858 returned tokens. Supplemental source-path attempts, source-cache finalization and the Rammer/NNFusion identity correction are separately recorded in the cohort protocol and per-stage completion protocols. These do not erase rejected stages. Full acceptance and evidence checks are in the cohort acceptance.json; independent semantic ground truth and target execution remain pending/not run.
