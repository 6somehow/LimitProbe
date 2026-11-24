# Limitset data

Normalize the controller-prepared, read-only dataset with `conda run -n findlimit python scripts/limitset/normalize.py --zip ZIP --raw RAW --out data/limitset`. The frozen split must already exist in the output directory. The manifest records hashes of the inputs, outputs and PDFs; PDFs remain outside the repository. Labels are a separate evaluator-only file and must not be loaded by the pipeline.

Build an isolated input with `conda run -n findlimit python scripts/limitset/make_case_dir.py CS6223-01 --out DIR --raw RAW`. DIR must not exist. It contains only the selected PDF and input metadata. The code pin in metadata does not copy a repository.

Existing project artifact mappings: CS6223-01 → `data/nnsmith/artifact.json`; CS6223-02 → `data/minference/artifact.json`; CS6223-03 → `data/infinigen/artifact.json`; CS6223-04 → `data/sparta/artifact.json`. These mappings identify papers, not permission to use unpinned repositories as case inputs.
