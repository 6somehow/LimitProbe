# Preflight: infinigen

- status: **not_ok** (pip install -e . failed: ERROR: file:///home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/InfiniGen does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.
)
- repository `/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/InfiniGen` at `3754f52d131c`
- python ? (requires None), packages: {}
- declared dependencies: []; requirements.txt lines: 7
- torch installed first as `torch==2.0.1` from the CPU wheel index

## Steps

| step | ok | note |
|---|---|---|
| create venv | yes |  |
| install torch==2.0.1 (CPU wheel) | yes |  |
| install requirements.txt pins | yes |  |
| pip install -e . | **no** | ERROR: file:///home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/InfiniGen does not appear to be a Python project: neither 'setup.py' nor 'pypr |
