# limitset2: held-out set v2 (2026-11-23)

- 11 papers that are not in the 17-case Limitation Testset: FlexPrefill, FlexPosit, QoServe, Tessera, DistServe, Sarathi-Serve, StreamingLLM, H2O, Quest, AWQ, vAttention.
- 22 reference labels (2 per paper): applicability 10, method shortcoming 9, mechanism origin unclear 3.
- Labels are drafts by claude-opus-5-5. The labelers read only the paper text, one example label (CS6223-01) and the dataset rubric. They did not read pipeline outputs or the prompt v3 plan. Every verbatim quote was checked against the paper text.
- Status: `human_reviewed` (2026-11-23): the dataset owner reviewed all 22 labels (3 keep, 19 edit, 0 drop); edited text from `HUMAN_REVIEW.md` was synced into `labels.jsonl` by `scripts/limitset/sync_human_review.py` (fields synced: headline, claim, critical_link, necessary_conditions, defeaters, source_locations; reasoning_chain, mechanism_insight, caveats, do_not_infer and verbatim_quotes are still the original draft text). Report results as "scored against human-reviewed labels".
- Rule: generators and prompt designers must not read `labels.jsonl` or `REVIEW.md`. Run each system once on this set.
- Known caveats: the pipeline has run on FlexPrefill, FlexPosit, QoServe and Tessera before (not with labels). Quest label 2 (GQA) is the same type as validation case CS6223-03.
- PDFs are not in git. Raw root: `/home/somehow6/lesson/CS6223/limitset2-raw/` (arXiv PDFs + project copies; hashes in `manifest.json`). Rebuild: `python scripts/limitset/build_limitset2.py`.
