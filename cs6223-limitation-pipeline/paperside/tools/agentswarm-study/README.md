# CS6223 AgentSwarm research harness

This team-owned Python runner compares one API request (A), one tool-using agent (B),
and a lead plus an independent evidence worker (S). It calls SoCLaaS directly.
Install Python 3.10+, Git, curl, and the dependencies below to run it from a regular
CS6223 checkout.

## Dataset

| Group | Papers | Use |
|---|---|---|
| Dev | NNSmith, MInference, InfiniGen, SparTA | Develop prompts and compare A, B, and S |
| Test with author source | Prompt Cache, SpinQuant, KVQuant, DX100 | Frozen comparison on the added papers. Existing runs are post-hoc because some cases were inspected during development |
| Paper-only | OneSidedMW, CXLfork, Juneberry, Twilight / T-LITE | Separate text-only cohort. The source-based runner does not score these as code-backed cases |

[`study-corpus.json`](study-corpus.json) lists the case IDs, publisher URLs, PDF SHA-256
hashes and fixed author commits where available. Preparation fetches originals and
verifies hashes. The extracted text is generated with the pinned parser for new runs.
Use a run's archived inputs when comparing exact request bytes with a historical run.
For the human reference rubric, use the version designated by Shanghao
and supply it to the scoring command after generation.

## Get started

From `cs6223-limitation-pipeline/paperside/tools/agentswarm-study/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'pypdf==6.10.2' 'pytest>=8'
.venv/bin/python -m pytest -q
.venv/bin/python -m swarmlab.prepare_inputs inputs --groups dev
.venv/bin/python -m swarmlab.runner prepare runs/dev --inputs inputs
.venv/bin/python -m swarmlab.runner run runs/dev --split dev \
  --conditions api_once single_agent gap_receipt_swarm
```

Set `SOCLAAS_API_KEY` in your shell before running the model. The runner also accepts
the team's existing `~/.config/soclaas/soclaas.env` and optional `SOCLAAS_BASE_URL`.
Generation uses the `x-test-2` route and checks the returned DeepSeek backend. The
installation and input-preparation steps do not use API quota. To try one case, add
`--papers nnsmith --conditions gap_receipt_swarm` to the run command.

To download the full manifest, use `--groups dev test paper-only --resume`. Make a new
run directory after expanding the input set. To reproduce the exposed-source Test
comparison, use `--split test --allow-posthoc-test`.

## Score and hand off

```bash
.venv/bin/python -m swarmlab.grade packet runs/dev --out out/dev-packets \
  --reference /path/to/team-reference.md
.venv/bin/python -m swarmlab.grade grade out/dev-packets --out out/dev-grades
```

| In `runs/<run>/cells/<paper>/<condition>/` | Use |
|---|---|
| `final.txt` and `validation.json` | Candidate limitation, exact evidence references and format checks |
| `reads.json`, `handoff.json` and `ledger.json` | Read spans and evidence exchanges to verify before promoting a candidate |
| `result.json` | Run status, validation, model and API usage |

Bring the pinned commit, method rule, trigger, source lines and proposed comparison to
Step 4 review. After the team accepts a candidate and creates a shared `Finding`, use
the [team E2E flow](../../../checklimits/HANDOFF.md) to test it and record a verdict.
The Swarm runner produces hypotheses and uses read-only paper/source tools.

## Current evidence and provenance

This portable runner uses the team's local AgentSwarm experiment at revision
`e636bbf` (S s2). The historical s2 Dev run had one core match (NNSmith) and one
partial match (MInference). It had 2 wins and 0 losses versus archived A, and
1 win and 0 losses versus archived B. A later s3 run on the exposed Test set
scored 0 core and 2 partial versus A's 1 core and 2 partial under conservative
grading. The portable runner gives B the same investigation task with a self-review
instruction. The historical archived B grades refer to its original prompt.

AgentSwarm-Serve is a separate team-developed implementation used by the Pi experiments.
This handoff includes the study runner and its offline tests, so the commands above work
without access to that checkout or to the DeepSeek Harness desktop app.
