# Limitset baselines

B1 sends one request per case and repeat through the local relay at temperature 0.
It extracts all PDF text with PyMuPDF and asks for findings in the prediction
format. It does not enrich the response. Invalid JSON or invalid prediction records
are recorded as failures, and failed runs can be retried. Successful runs with a
matching manifest are resumed from their saved prediction and cost. Use a fresh
output directory when changing the method, split, model, or Git revision.

For CS6223-03, B1 includes UTF-8 files from the pinned InfiniGen Git commit if
the paper and repository fit within 400,000 characters. It excludes binary files;
the input information file records whether code was included. The budget is a
character limit, not a guarantee that the model context will accept the request.
The swarmlab api_once implementation requires its frozen study input index and
source packet rather than an arbitrary isolated PDF, so B1 uses a minimal equivalent.
B2 is loaded only when selected and fails clearly until its adapter is installed.

The scorer and baseline runner must not run simultaneously: their shared relay
is stopped when its starter exits. The runner starts the relay once per batch and
records predictions, per-run evidence, cost.jsonl, and a run manifest. The relay
credentials must be supplied in the environment.
