# CS6223 method-limitations study

The study uses original research papers and fixed author repositories to propose testable method limitations. Model generation has read-only evidence tools. The human reference enters the separate evaluator after final reports are frozen.

| Condition | Workflow |
|---|---|
| A | One DeepSeek API request with the fixed evidence packet |
| B | One Pi session with read-only evidence tools |
| C | Ordinary Pi Swarm with up to two workers |
| D | Two independent procedure investigations, a targeted cross-check, and a traceable final report |

The four Dev papers are NNSmith, MInference, InfiniGen, and SparTA. The paired Test cases with code are Prompt Cache, SpinQuant, KVQuant, and DX100. The four additional paper-only Test cases have a separate archive and comparison. Earlier pilots used these papers. The Test set is held out from iteration on the current protocol.

## Setup and run

Run these commands from `cs6223-limitation-pipeline/paperside/`. The study needs Git, Python with `pypdf` and `pymupdf`, Node.js 20 or later, and approved access to the original AgentSwarm-Serve repository and the SoCLaaS model route.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pypdf pymupdf
npm ci --prefix tools/method-limitations --ignore-scripts
.venv/bin/python tools/method-limitations/prepare_study_inputs.py runs/study-originals
.venv/bin/python tools/method-limitations/swarm_study.py prepare runs/study-dev \
  --previous-runs runs/study-originals --swarm-source /path/to/sglang-swarm
.venv/bin/python tools/method-limitations/swarm_study.py run runs/study-dev \
  --split dev --conditions evidence_gap_swarm plain_swarm api_once single_agent
```

The input builder checks publisher PDF hashes, author commits, and exact excerpt hashes. The runtime is rebuilt from AgentSwarm-Serve commit `6e46093badbbc109c5be7296c24fe2f09efb00ae`. The runner reads `SOCLAAS_API_KEY` and optional `SOCLAAS_BASE_URL` from `~/.config/soclaas/soclaas.env`. Each run directory archives the exact inputs, model requests, responses, source reads and usage. Store these outputs outside version control.

When a Pi session grows, Pi automatically checks its context between turns and can continue with a summary and recent messages. B, C and D share this policy and have up to eight task replies plus two native summary requests per condition. The experiment uses a local 131,072-token window, a 40,960-token reserve, and a 32,768-token task output cap. The separate summary cap is at most 12,288. These values are frozen alongside each run.

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
