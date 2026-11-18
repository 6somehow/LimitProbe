# Preflight: minference

- status: **ok**
- repository `/home/somehow6/lesson/CS6223/cs6223-limitation-pipeline/third_party/MInference` at `427b1ddbd285`
- python 3.11.16 (requires None), packages: {'accelerate': '1.16.0', 'numpy': '1.26.4', 'tokenizers': '0.23.3', 'torch': '2.15.0+cpu', 'transformers': '5.23.0'}
- declared dependencies: []; requirements.txt lines: 0
- warning: the package itself was not built; the checkout is used from its directory
- torch installed first as `torch` from the CPU wheel index
- repository unchanged by the install and the tests: True

## Steps

| step | ok | note |
|---|---|---|
| pip install -e . | yes | the package cannot be built on this machine; its setup.py requirements were installed (skipped: flash_attn, pycuda==2023.1); the checkout is used in place |

## Entry point candidates (public functions the repository's tests and docs call most)

| function | defined in | mentions |
|---|---|---|
| `minference_patch` | minference/patch.py::minference_patch | 2 |
| `generate` | experiments/ruler/pred/serve_trt.py::generate, experiments/ruler/pred/serve_vllm.py::generate, minference/modules/inf_llm.py::generate | 1 |
| `get_support_models` | minference/configs/model2path.py::get_support_models | 1 |
| `block_sparse_attention` | minference/ops/block_sparse_flash_attention.py::block_sparse_attention | 1 |
| `vertical_slash_sparse_attention` | minference/ops/pit_sparse_flash_attention_v2.py::vertical_slash_sparse_attention | 1 |
| `streaming_forward` | minference/ops/streaming_kernel.py::streaming_forward | 1 |

This ranking is a starting point. The entry points are decided by step 2 and the paper side.
