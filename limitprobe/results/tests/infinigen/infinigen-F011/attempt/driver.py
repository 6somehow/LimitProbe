"""Driver: call SelfAttention.forward (the Region's function) on a decoding step.

The declared entry TorchDevice.mha cannot reach the target: it is the prefill compute
method that SelfAttention.forward itself calls (self.compute.mha), so the dependency runs
the other way.  The step-4 static analysis also reported call_chain_status=not_found.
We therefore call the target function of the Region, SelfAttention.forward, with the real
runtime objects it expects (ValueHolder buffers and TorchTensor values), so the target
branch runs inside the real function body and with the real condition.
"""

import os
import sys

import numpy as np
import torch


def _find_repo():
    """The child puts the repository root at sys.path[0]; the flexgen packaging root is
    <repo>/speedup/flexgen and the controller package is <repo>/speedup/infinigen."""
    candidates = list(sys.path) + [os.getcwd()]
    for p in candidates:
        if not p:
            continue
        fg = os.path.join(p, "speedup", "flexgen")
        if os.path.isfile(os.path.join(fg, "infinigen", "flex_opt.py")):
            return os.path.join(p, "speedup", "infinigen"), fg
    raise RuntimeError("flexgen/infinigen repository not found on sys.path")


_INF_DIR, _FG_DIR = _find_repo()
for _p in (_INF_DIR, _FG_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import infinigen.flex_opt as flex_opt  # noqa: E402
from flexgen.pytorch_backend import TorchTensor  # noqa: E402
from flexgen.utils import ExecutionEnv, ValueHolder  # noqa: E402

torch.set_num_threads(1)


def _tensor(shape, dtype, device):
    if dtype == torch.bool:
        data = torch.ones(*shape, dtype=torch.bool)
    else:
        data = torch.randn(*shape).to(dtype) * 0.1
    return TorchTensor.create_from_torch(data, device)


def run(inputs):
    seed = int(inputs.get("rng_seed", 0))
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(1)

    n_head = int(inputs.get("n_head", 2))
    input_dim = int(inputs.get("input_dim", 8))
    dtype = getattr(torch, str(inputs.get("dtype", "float16")))
    layer_id = int(inputs.get("layer_id", 1))
    alpha = int(inputs.get("alpha", 4))
    max_num_kv = int(inputs.get("max_num_kv", 4))
    partial_weight_ratio = float(inputs.get("partial_weight_ratio", 0.2))
    num_gpu_batches = int(inputs.get("num_gpu_batches", 1))
    gpu_batch_size = int(inputs.get("gpu_batch_size", 1))
    kv_seq_len = int(inputs.get("kv_seq_len", 6))
    decode_step = int(inputs.get("decode_step", 1))
    attn_sparsity = float(inputs.get("attn_sparsity", 1.0))
    enable_prefetching = bool(inputs["enable_prefetching"])

    head_dim = input_dim // n_head
    batch = gpu_batch_size

    device = flex_opt.TorchDevice("cpu")
    env = ExecutionEnv(gpu=device, cpu=device)

    config = type("Config", (), {
        "n_head": n_head,
        "input_dim": input_dim,
        "dtype": np.float16 if dtype == torch.float16 else np.float32,
        "num_hidden_layers": 3,
    })()

    policy = flex_opt.Policy(
        gpu_batch_size=gpu_batch_size,
        num_gpu_batches=num_gpu_batches,
        w_gpu_percent=100, w_cpu_percent=0,
        cache_gpu_percent=100, cache_cpu_percent=0,
        act_gpu_percent=100, act_cpu_percent=0,
        overlap=False,
        sep_layer=True,
        pin_weight=False,
        cpu_cache_compute=False,
        attn_sparsity=attn_sparsity,
        compress_weight=False,
        comp_weight_config=None,
        compress_cache=False,
        comp_cache_config=None,
    )

    attn = flex_opt.SelfAttention(
        config, env, policy, layer_id, enable_prefetching,
        partial_weight_ratio=partial_weight_ratio, alpha=alpha, max_num_kv=max_num_kv)

    hidden = ValueHolder()
    hidden.val = _tensor((batch, 1, input_dim), dtype, device)

    attention_mask = ValueHolder()
    attention_mask.val = _tensor((batch, kv_seq_len), torch.bool, device)

    weight_read_buf = ValueHolder()
    weight_shapes = [
        (input_dim, input_dim), (input_dim,),
        (input_dim, input_dim), (input_dim,),
        (input_dim, input_dim), (input_dim,),
        (input_dim, input_dim), (input_dim,),
        (input_dim,), (input_dim,),
    ]
    weight_read_buf.val = tuple((_tensor(shape, dtype, device), False) for shape in weight_shapes)

    cache_read_buf = ValueHolder()
    cache_read_buf.val = (
        (_tensor((kv_seq_len, batch * n_head, head_dim), dtype, device), False),
        (_tensor((kv_seq_len, batch * n_head, head_dim), dtype, device), False),
    )

    cache_write_buf = ValueHolder()

    partial_weight_read_buf = ValueHolder()
    partial_weight_read_buf.val = _tensor((n_head, head_dim, input_dim), dtype, device)

    partial_cache_read_buf = ValueHolder()
    partial_cache_read_buf.val = _tensor((max_num_kv, batch * n_head, head_dim), dtype, device)

    weight_home = ValueHolder()

    attn.forward(
        hidden, cache_read_buf, weight_read_buf, attention_mask, cache_write_buf,
        decode_step, 0, False, partial_weight_read_buf, partial_cache_read_buf,
        None, None, None, weight_home)
