# Swarm paper-side interface

The bridge imports a frozen Swarm report or gap receipt. It reads the report and its original PDF.
For a code-backed run, the pipeline still runs its code-side extraction, 3b verification and
Step 4 integration. For a paper-only run, Checklimits writes Findings and A1 analysis reports
directly from the candidate evidence.

## Commands

Run from the repository root.

```sh
conda run -n findlimit python -m paperside_bridge.swarm_to_paper_side toy \
  --report path/to/final.txt --pdf path/to/toy.pdf --out path/to/handoffs/toy

conda run -n findlimit python -m pipeline run toy \
  --paper-side-source swarm --swarm-report path/to/final.txt --pdf path/to/toy.pdf

conda run -n findlimit python -m pipeline test toy --paper-side-source swarm

conda run -n findlimit python -m pipeline paper-only toy \
  --swarm-report path/to/final.txt --pdf path/to/toy.pdf
```

The converter and paper-only command run offline. The code-backed commands use the existing
artifact setup and the model-backed stages of the code pipeline. The code-backed Swarm run
stores its handoffs and 3b outputs under `out/` and its Step 4 and Checklimits results under
`results/swarm/`. Choose the same source for `pipeline test`. The default pipeline source is
`v1`. The two sources have separate 3b caches and Step 4 results.

The default PDF extractor is `pypdf`. Use `--pdf-extractor pymupdf` in the standalone converter
or `--swarm-pdf-extractor pymupdf` in the pipeline if the report cites that extractor's text.
Every citation must match on its physical PDF page, with only whitespace collapsed for comparison.
The original quote is preserved. Candidates with missing or mismatching quotes, withdrawn
candidates, and candidates from refuting receipts are listed with reasons and skipped.
Malformed reports, duplicate candidate IDs, and artifact mismatches fail conversion.

## Field mapping

| Swarm category or field | Shared record |
| --- | --- |
| `applicability_limitation` | `Limitation.swarm_category`, level L3, Finding category `paper_hypothesis` |
| `mechanism_origin_unclear` | `Limitation.swarm_category`, level L3, Finding category `paper_hypothesis` |
| `method_shortcoming` | `Limitation.swarm_category`, level L3, Finding category `paper_hypothesis` |
| `trigger` or `conditions` | `Limitation.condition_text` |
| `consequence`, then claim, causal argument, limitation, or title | `Limitation.effect_text`, effect type `other` |
| Paper quote and physical page | `Limitation.paper_evidence` and the handoff's `candidate_evidence` |
| Candidate ID, report path and hash, PDF hash, extractor and receipt verdict | `Limitation.swarm_provenance` |
| Full candidate, including origin IDs, code spans, mitigation and proposed comparison | Archived in `Limitation.swarm_provenance.candidate` |

When a report uses the study's older `kind` field, `disclosed_boundary` maps to
`applicability_limitation`. `method_hypothesis`, `implementation_discrepancy`, and unspecified
or other kinds map to `method_shortcoming`. The original kind stays in the archived candidate.
An explicit category must be one of the three shared Swarm categories.

The handoff includes the four v1 arrays. They are empty because the candidate format does not
provide formal claims, scope predicates, evaluation configurations, or code parameter bindings.
3b uses Swarm quotes to find additional retrieval passages in its own index of the same PDF.
The usual documentation judge and quotation gate still determine the verdict.

Step 4 uses the candidate's trigger as prose, with no runnable witness. Code spans and comparison
plans stay in provenance. The bridge does not promote them to verified code locations, 3a
verdicts, or executable tests. Paper hypotheses have unknown scope and priority 3. Code-side
Findings retain their normal confidence checks, using the current Swarm run's 3b agreement.
Paper-only Findings have null process confidence, A1 analysis and no test verdict.

The converter imports the candidate list. Separate inventories such as `known_boundaries`,
rejected candidates, run transcripts and worker ledgers stay in the original run archive.
The report hash and candidate provenance support tracing back to that archive.

`Finding.origin` records the paper source used for the run, including for Findings produced
from code alone. Historical records without the field default to `v1`. The field supports
later comparisons. The interface makes no estimate of Swarm's effect on finding quality.
