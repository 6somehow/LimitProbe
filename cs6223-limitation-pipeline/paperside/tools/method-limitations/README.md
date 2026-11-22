# CS6223 method-limitations study

The study uses original research papers and fixed author repositories to propose testable method limitations. Model generation has read-only evidence tools. The human reference enters the separate evaluator after final reports are frozen.

**Current experiment.** The [targeted review pilot](#compare-self-review-with-delegated-evidence-checks) compares self-review and delegation from the same frozen draft. Use it to develop and validate the new role prompts. The A–D study below remains the comparison for selecting a method for Test.

| Condition | Workflow |
|---|---|
| A | One DeepSeek API request with the fixed evidence packet |
| B | One Pi session with read-only evidence tools |
| C | Ordinary Pi Swarm with up to two workers |
| D | Two independent procedure investigations, a targeted cross-check, and a traceable final report |

The four Dev papers are NNSmith, MInference, InfiniGen, and SparTA. The paired Test cases with code are Prompt Cache, SpinQuant, KVQuant, and DX100. The four additional paper-only Test cases have a separate archive and comparison. Earlier pilots used these papers. The Test set is held out from iteration on the current protocol.

In the completed four-paper A–D Dev comparison, A, C, and D scored zero core and zero partial matches. B scored one partial match on MInference. No method qualified for Test. The targeted review prompts are a separate Dev experiment.

## Setup and run

Run these commands from `cs6223-limitation-pipeline/paperside/`. The study needs Git, curl, Python with `pypdf` and `pymupdf`, Node.js 20 or later, and approved access to the original AgentSwarm-Serve repository and the SoCLaaS model route.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pypdf pymupdf
npm ci --prefix tools/method-limitations --ignore-scripts
.venv/bin/python tools/method-limitations/prepare_study_inputs.py runs/study-originals
.venv/bin/python tools/method-limitations/swarm_study.py prepare runs/study-dev \
  --previous-runs runs/study-originals --swarm-source /path/to/sglang-swarm --policy mechanism
.venv/bin/python tools/method-limitations/swarm_study.py run runs/study-dev \
  --split dev --conditions evidence_gap_swarm plain_swarm api_once single_agent
```

The input builder checks publisher PDF hashes, author commits, and exact excerpt hashes. If a download is interrupted, use `--resume` to reuse the inputs already verified. The runtime is rebuilt from AgentSwarm-Serve commit `6e46093badbbc109c5be7296c24fe2f09efb00ae`. The renderer and extractor can differ across library versions, so use the frozen paper text and page images to replay an existing run exactly. The runner reads `SOCLAAS_API_KEY` and optional `SOCLAAS_BASE_URL` from `~/.config/soclaas/soclaas.env`. Each run directory archives the exact inputs, model requests, responses, source reads and usage. Store these outputs outside version control.

When a Pi session grows, Pi automatically checks its context between turns and can continue with a summary and recent messages. B, C and D share this policy and have up to eight task replies plus two native summary requests per condition. The experiment uses a local 131,072-token window, a 40,960-token reserve, and a 32,768-token task output cap. The separate summary cap is at most 12,288. These values are frozen alongside each run.

The `mechanism` policy gives D a controlled-pair discovery task. Each worker proposes comparable valid cases, fixes the relevant configuration or budget, and traces where their behavior diverges. B and C keep their original workflow. The optional `stress` policy assigns explicit acceptance/coverage, structure, representation, and sharing lenses to the two workers. It uses a separate worker system prompt and archives the invariant and contrasted cases. Both policies are experimental. Dev changes never add individual reference answers to any generation prompt.

## Evaluate and select a method

Use the team reference transcription authorized for evaluation only. Packet generation attaches the reference and mechanically checks citations. Semantic grades remain a separate review. Keep `mapping.json` away from the grader when conducting a blinded comparison.

```sh
.venv/bin/python tools/method-limitations/swarm_evaluation.py reference /path/to/rubric.md /path/to/reference.json
.venv/bin/python tools/method-limitations/swarm_evaluation.py packet runs/study-dev /path/to/dev-packet /path/to/reference.json --split dev
.venv/bin/python tools/method-limitations/swarm_evaluation.py summarize /path/to/dev-packet /path/to/dev-grades /path/to/dev-metrics.json
.venv/bin/python tools/method-limitations/swarm_evaluation.py release-test runs/study-dev /path/to/dev-packet /path/to/dev-grades
.venv/bin/python tools/method-limitations/swarm_study.py run runs/study-dev --split test
```

Grade each complete report as core, partial, or miss against one retained record. A Dev winner must have more paired wins than losses and at least as many core hits against **each** of A and B on all four Dev cases. Either C or D can qualify. Core hits, partial hits and known token use break ties when both qualify. The Test release records the selected method before running all four conditions. Report both confirmatory baseline comparisons on Test and preserve failures separately from diagnosis misses.

Additional indicators include source and paper citation traceability, test-design readiness, complete-report rate, and actual calls and tokens. Proposed tests are assessed for a controlled comparison and an oracle. The study never treats hypothetical tests as executed coverage.

For D, each completed cell in `mapping.json` records how many candidate items a worker returned, how many passed parsing, how many appeared in the archived final request, and how many retained IDs were referenced in the final report. A missing raw count means the worker response could not be counted as a structured list. The verification receipt is checked against the actual final request. These fields measure evidence delivery and attribution. Semantic matching is graded separately.

## Compare self-review with delegated evidence checks

The Dev-only targeted review pilot runs one lead session per paper. The lead follows method rules into their consumers and identifies one unanswered evidence question. Its exact report is shared by both arms. In self-review, the root investigates and writes the final. In delegated review, a separate Pi session investigates and sends its memo to the root. The original inputs, model, evidence question and maximum review and final reply counts match. Self-review retains its own tool history. The delegated root gets the exact memo and can reopen original evidence.

```sh
.venv/bin/python tools/method-limitations/targeted_review.py prepare runs/targeted-dev \
  --previous-runs runs/study-originals --swarm-source /path/to/sglang-swarm
.venv/bin/python tools/method-limitations/targeted_review.py run runs/targeted-dev
.venv/bin/python tools/method-limitations/swarm_evaluation.py packet runs/targeted-dev /path/to/review-packet /path/to/reference.json --split dev
.venv/bin/python tools/method-limitations/swarm_evaluation.py summarize /path/to/review-packet /path/to/grades /path/to/targeted-dev-metrics.json
```

Compare the frozen drafts with the two finals to measure the effect of checking original evidence. Compare the two finals directly to measure the effect of delegation. `pair-audit.json` verifies that each final request received the exact frozen draft and review memo. Semantic scores, source citations and test-ready comparisons are evaluated separately. This pilot can inform a new D configuration for the A/B/C/D comparison.

The default `method-path` prompt policy gives each role a concrete deliverable.

| Role | Deliverable |
|---|---|
| Lead | A frozen draft anchored in the evaluated call path. It contrasts two in-scope cases at fixed configuration and resources and identifies one evidence gap to check. |
| Evidence investigator | A memo tracing the first behavioral divergence to its consumer and checking the mitigation, with original citations and a way to refute the claim. |
| Final writer | A ranked report with a causal explanation and a measurable comparison. Artifact differences and scope caveats go under `known_boundaries`. |

The runner freezes and hashes the three prompt files. Use `--prompt-policy original` at preparation to run the previous wording in a new directory. Use `run --draft-only` for a lead-prompt comparison. A later `run` reuses those drafts for the two review arms.

| Output in the run directory | What to check |
|---|---|
| `protocol.json` and `input-index.json` | Model, limits, input revisions, and exact prompt hashes |
| `<paper>/frozen_draft/final.txt` | Lead candidates and the chosen evidence question |
| `<paper>/{self_review,delegated_review}/final.txt` | Reports to score against the reference |
| `pair-audit.json` | Draft hashes and confirmation of memo delivery in each final request |

Commit source, tests, and documentation to the paper-side branch. The SoCLaaS credential file, reference annotations, PDF and repository snapshots, and raw API archives stay outside Git.
