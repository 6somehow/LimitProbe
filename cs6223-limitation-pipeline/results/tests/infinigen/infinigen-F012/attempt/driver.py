"""Driver for F012: decoding branch of SelfAttention.forward.

A prefill pass (i=0) runs the real repository mha on CPU to create the partial
key index exactly as the model would; a decoding pass (i=1) then reaches the
target line with a non-empty prev_partial_cache_read_buf holder.  The only input
that changes between the positive and negative run is layer_id.
"""

import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

import _clpaths

_clpaths.ensure()

from flexgen.pytorch_backend import TorchDevice, TorchTensor  # noqa: E402
from flexgen.utils import ExecutionEnv, ValueHolder  # noqa: E402
from infinigen.flex_opt import SelfAttention  # noqa: E402

N_HEAD = 2
HEAD_DIM = 4
H = N_HEAD * HEAD_DIM
BATCH = 1
PROMPT_LEN = 4
GEN_LEN = 2
PARTIAL_RATIO = 0.5

torch.set_num_threads(1)
random.seed(0)
np.random.seed(0)
torch.manual_seed(0)


def _tensor(*shape, gen, dtype=torch.float32):
    return torch.randn(*shape, generator=gen, dtype=dtype)


def _weights(gen, dev):
    w_q = torch.cat((_tensor(H, H, gen=gen), _tensor(H, 1, gen=gen)), dim=1)
    w_k = torch.cat((_tensor(H, H, gen=gen), _tensor(H, 1, gen=gen)), dim=1)
    w_v = _tensor(H, H, gen=gen)
    b_v = _tensor(H, gen=gen)
    w_out = _tensor(H, H, gen=gen)
    b_out = _tensor(H, gen=gen)
    w_ln = torch.ones(H)
    b_ln = torch.zeros(H)
    b_q = torch.zeros(H)
    b_k = torch.zeros(H)

    def pair(x):
        return (TorchTensor.create_from_torch(x, dev), False)

    return (pair(w_q), pair(b_q), pair(w_k), pair(b_k), pair(w_v), pair(b_v),
            pair(w_out), pair(b_out), pair(w_ln), pair(b_ln))


def run(inputs):
    dev = TorchDevice("cpu")
    config = SimpleNamespace(n_head=N_HEAD, input_dim=H, dtype=np.float32)
    policy = SimpleNamespace(
        gpu_batch_size=1,
        num_gpu_batches=1,
        compress_weight=False,
        compress_cache=False,
        comp_cache_config=None,
        cpu_cache_compute=False,
        attn_sparsity=1.0,
    )
    env = ExecutionEnv(gpu=dev, cpu=dev)
    attn = SelfAttention(config, env, policy, layer_id=int(inputs["layer_id"]),
                         enable_prefetching=False, partial_weight_ratio=PARTIAL_RATIO)
    attn.task = SimpleNamespace(prompt_len=PROMPT_LEN, gen_len=GEN_LEN, cut_gen_len=None)

    gen = torch.Generator().manual_seed(11)

    def tt(x):
        return TorchTensor.create_from_torch(x, dev)

    # prefill: fills self.partial_index from the query distribution
    pref_hidden = ValueHolder()
    pref_hidden.val = tt(_tensor(BATCH, PROMPT_LEN, H, gen=gen))
    pref_mask = ValueHolder()
    pref_mask.val = tt(torch.ones((BATCH, PROMPT_LEN), dtype=torch.bool))
    pref_in = ValueHolder()
    pref_in.store(_weights(gen, dev))
    pref_out = ValueHolder()
    weight_home = ValueHolder()
    attn.forward(pref_hidden, ValueHolder(), pref_in, pref_mask, pref_out, 0, 0,
                 False, None, None, None, None, None, weight_home)

    # decoding: the holder is non-empty and layer_id decides whether it grows
    dprime = int(HEAD_DIM * PARTIAL_RATIO)
    k_cache = tt(_tensor(PROMPT_LEN + GEN_LEN - 1, BATCH * N_HEAD, HEAD_DIM, gen=gen))
    v_cache = tt(_tensor(PROMPT_LEN + GEN_LEN - 1, BATCH * N_HEAD, HEAD_DIM, gen=gen))
    cache_read = ValueHolder()
    cache_read.store(((k_cache, False), (v_cache, False)))
    dec_weights = ValueHolder()
    dec_weights.store(_weights(gen, dev))
    dec_hidden = ValueHolder()
    dec_hidden.val = tt(_tensor(BATCH, 1, H, gen=gen))
    dec_mask = ValueHolder()
    dec_mask.val = tt(torch.ones((BATCH, PROMPT_LEN + GEN_LEN - 1), dtype=torch.bool))
    dec_out = ValueHolder()
    prev = ValueHolder()
    prev.val = torch.zeros((0, BATCH * N_HEAD, dprime), dtype=torch.float32)

    attn.forward(dec_hidden, cache_read, dec_weights, dec_mask, dec_out, 1, 0,
                 False, None, None, None, prev, None, weight_home)

    return {"layer_id": int(inputs["layer_id"]),
            "partial_len": int(prev.val.shape[0]),
            "returned_shape": list(dec_hidden.val.shape)}
