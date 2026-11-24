# Artifact map

Start with the [README](../README.md) for setup and the offline demo, then consult [results](13_limitset_results.md) for experiment status and limitations. The [index](INDEX.md) lists specifications and historical notes.

The paper side (`paperside/`), code side (`codeside/`), shared models (`schema/`), orchestration (`pipeline/`), and test side (`checklimits/`) implement the report's pipeline. `scorer_limitset/`, `confidence_limitset/`, and `limitset_baselines/` implement evaluation and comparison. `scripts/limitset/` contains experiment and reporting tools. `data/` contains metadata and derived dataset records; `results/` contains committed derived results. The committed `results/limitset_final/` bundle and `scripts/limitset/reproduce_tables.py` reproduce the report tables offline. The synthetic example in `examples/` checks the workflow, not the reported experiment. External PDFs and source repositories must be obtained separately as described in the README.
