# Source delivery validation (2026-11-11)

Validation ran in an isolated checkout based on Wanting `43b3a9a866b589bbb9ce5f140406ead5742daa12`, without running target systems or making model/API requests.

- Fresh virtual environment installation: `python -m pip install -e './paperside[team,vision,dev]'` from the shared team directory succeeded.
- Paper side: `python -m unittest discover -s tests -v` from `paperside/`: 204 tests, success, 2 skips. Skips are missing external PDFs and target repositories, which are intentionally excluded from this distribution.
- Existing team suite: `python -m pytest -q -rs` from the shared team directory: 108 passed, 3 skipped. One skip needs the omitted FlexPrefill checkout; two require the optional `openai` dependency.
- Pi validators: `node --test tools/pi-mechanism-agent/*.test.mjs`: 23 passed.
- `python scripts/validate_delivery.py`: native schema and actual consumer checks passed; 206 behaviors, 199 completed, 7 pending, 0 scalar solver bindings. Existing code-side conditions retain unknown scope.
- `python scripts/run_complete_corpus.py --help`: imported generic pipeline and cross-module preparation code successfully.
- `codeside/`, `schema/`, shared tests and existing team files remain byte-for-byte unchanged from the branch base.
- Secret-pattern scanning found no private keys, credential-bearing URLs, recognized API/GitHub/AWS tokens, literal long credential assignments, or the active `SOCLAAS_API_KEY` value. The scanner reported file paths/rule names only, without values.

No fresh source acquisition or complete corpus model run was performed for this Git delivery. Model semantics, pending rows, runtime behavior and paper scope remain subject to independent review. This is source and interface validation, not research-result validation.
