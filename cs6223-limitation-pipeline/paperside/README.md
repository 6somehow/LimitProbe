# Paper side (Zhaopeng), v1

This module adds paper extraction, independent mechanism decomposition, static paper→code conformance review, and a native handoff for the shared `schema` / `codeside.verify3b` consumer. Existing team code and schema are unchanged. Use commands below from this `paperside/` directory.

The checked-in SparTA snapshot contains 206 behaviors: 199 assessed and 7 pending. `paper_side.json` contains 204 claims, 26 scope items, 29 evaluation points, and 26 navigation bindings. There are **0 scalar solver bindings**. Review adjustments preserve two withheld evaluation records alongside two pending claim records (four pending paper records total); see `review-adjustments.json` and `review-notes.json` in the handoff. Existing code-side conditions still return `unknown` for paper scope; scope matching remains unresolved. These are development artifacts and static hypotheses, with independent human review pending. No target system execution or confirmed runtime bugs are claimed.

## Install

Python >=3.10 and Git are required. Create an isolated environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[team,vision,dev]'
```

Core dependency: pypdf. The `team` extra supplies pydantic, z3-solver and rank-bm25 needed by the existing consumer's import path; `vision` supplies PyMuPDF for PDF page images. No GPU or target-system packages are needed. Node.js >=20 is needed for Pi scripts. To launch Pi model runs separately, install its locked dependencies with `npm ci --prefix tools/pi-mechanism-agent`; node_modules is deliberately excluded. Offline Node validation tests need no npm install.

`PAPERPROBE_TEAM_REPO` optionally selects a shared consumer checkout containing `schema/` and `codeside/`. Otherwise it is located by walking this installed source's ancestors. In this repository the default resolves to the parent directory of `paperside/`. No machine-specific runtime paths are required.

## Offline checks

```sh
.venv/bin/python scripts/validate_delivery.py
.venv/bin/python -m unittest discover -s tests -v
node --test tools/pi-mechanism-agent/*.test.mjs
.venv/bin/python scripts/run_complete_corpus.py --help
```

These checks do not call models or run the analyzed target systems. Catalog tests skip when omitted PDFs/target repositories are absent; a skip does not verify source acquisition. The independent algebra fixture is local synthetic arithmetic, not target execution. `scripts/validate_delivery.py` checks native schema, actual consumer loading and ScopeChecker behavior, frozen handoff hashes, row accounting, pending states, and the absence of scalar solver bindings.

## Rerun with fresh source inputs

Acquisition downloads PDFs and clones pinned repositories without executing them:

```sh
.venv/bin/python scripts/prepare_team_paper_sources.py --team "${PAPERPROBE_TEAM_REPO:-..}"
```

This reads team `data/*/artifact.json` and `workstreams/zhaopeng/team-reviewed.json`, checks PDF hashes and commits, and populates ignored `data/repos/team-*` and the shared checkout's `third_party/papers`. A full corpus rerun additionally needs the authorized `SOCLAAS_API_KEY` environment variable. Obtain it through the team's approved channel; never put its value into Git or command history. The endpoint/model route is recorded in `src/paperprobe/team_paper_side.py` and the Pi runner. Set the key in the invoking shell before the following paid model run:

```sh
.venv/bin/python scripts/run_complete_corpus.py --papers flexprefill minference infinigen nnsmith
```

The pipeline writes ignored `runs/team-complete-v1/` and new `handoffs/paper-side-v1/<paper>/` records. Existing requests/results are preserved and resumed according to stage checks; do not reuse a run directory after changing its inputs, pins, prompts or code. Archive it first, or use a clean checkout for an independent new run. It copies the Pi runtime to each run and links the installed `node_modules`. Structural repair and failed attempts remain recorded. `scripts/recover_corpus_failed.py` offers bounded explicit recovery of failed mechanism stages; inspect its CLI help before use. Parallelism is bounded within the pipeline; output is not a controlled accuracy comparison.

`scripts/build_paper_handoff.py` creates the initial native handoff; `scripts/finalize_handoff.py` adds navigation bindings and guards solver bindings. They require the full recorded run/source inputs. SparTA-specific `prepare_sparta_delivery.py` and `review_sparta_interface.py` are preserved stage scripts tied to archived SparTA runs; they are not standalone fresh-corpus entry points. Finalizing SparTA also expects its local audit HTML. The checked-in lightweight handoff is intended for offline inspection and consumer integration, not as a replacement for all run evidence.

## What is included

`src/paperprobe`, scripts, tests, configuration/catalog pins, Pi runner source and package-lock, and the lightweight `handoffs/paper-side-v1/sparta/` JSON snapshot are included. `source-distribution.json` identifies omissions and hashes the included snapshot. `original-bundle-index.json` preserves the original full bundle's hashes, including omitted files. Absolute archive paths inside provenance describe the original run; they are not portable live links.

PDFs, target checkouts, raw runs/API logs, node_modules, credentials, ZIPs and large HTML dashboards remain outside Git. Source-read excerpts and pinned repository identities are included for review. See `README.legacy.md` and `tools/pi-mechanism-agent/README.md` for earlier workflows and their limitations; earlier run counts are historical, not fresh verification of this checkout.
