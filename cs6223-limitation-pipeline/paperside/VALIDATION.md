# Source delivery validation (2026-11-11)

Validation ran in an isolated checkout based on Wanting `43b3a9a866b589bbb9ce5f140406ead5742daa12`, without running target systems or making model/API requests.

- Fresh virtual environment installation: `python -m pip install -e './paperside[team,vision,dev]'` from the shared team directory succeeded.
- Paper side: `python -m unittest discover -s tests -v` from `paperside/`: 206 tests, success, 2 skips. Skips are missing external PDFs and target repositories, which are intentionally excluded from this distribution.
- Existing team suite: `python -m pytest -q -rs` from the shared team directory: 108 passed, 3 skipped. One skip needs the omitted FlexPrefill checkout; two require the optional `openai` dependency.
- Pi validators: `node --test tools/pi-mechanism-agent/*.test.mjs`: 23 passed.
- `python scripts/validate_delivery.py`: both published packages passed native schema, hash/accounting and actual consumer checks. SparTA retains 204/26/29/26 interface rows, 206 behaviors, 199 completed / 7 pending and 0 scalar solver bindings. FlexPrefill has 104/16/23/24 interface rows, 104 behaviors, 96 completed / 8 pending, 1 tau scalar binding and 23 navigation bindings; actual consumer results agree with the recorded per-condition outcomes.
- New solver guards reject evaluation-only or missing explicit-support numeric domains. Scope replacements preserve held original records; the existing reviewed SparTA package is unchanged.
- `node --check scripts/validate_corpus.mjs`: syntax passed. This validator needs complete local runs and pinned Git checkouts; its full evidence checks were not rerun from the lightweight checkout. The FlexPrefill handoff contains the pre-existing local `corpus-acceptance.json` summary (144 requests, 2,602,303 returned tokens, 138 tools, 10 rejected stages), not raw API logs.
- `python scripts/run_complete_corpus.py --help`: imported generic pipeline and cross-module preparation code successfully.
- `codeside/`, `schema/`, shared tests and existing team files remain byte-for-byte unchanged from the branch base.
- Secret-pattern scanning found no private keys, credential-bearing URLs, recognized API/GitHub/AWS tokens, literal long credential assignments, or the active `SOCLAAS_API_KEY` value. The scanner reported file paths/rule names only, without values.

No fresh source acquisition or complete corpus model run was performed for this Git delivery. Model semantics, pending rows, runtime behavior and paper scope remain subject to independent review. This is source and interface validation, not research-result validation.
