# Limitset runner

Run `conda run -n findlimit python -m pipeline limitset run --split validation --dry-run` to build the isolated inputs and print the plan. Remove `--dry-run` to generate predictions. Select one case with `--case`, set `--repeats`, `--workers`, `--timeout` (seconds), `--out`, or `--raw` as needed.

Each repeat gets its own input and results under `runs/<case>/r<n>`. Completed predictions are reused on resume; failures are recorded and retried on the next run. The manifest records the model, revision, input PDF hashes and timestamps. Predictions use `unclassified` when the source does not supply a limitset category. CS6223-03 also includes existing InfiniGen step-4 findings when available. The generator requires the existing paper-only lane's model configuration and relay.
