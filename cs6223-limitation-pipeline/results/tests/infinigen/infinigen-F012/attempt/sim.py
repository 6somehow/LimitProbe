"""CPU port of TorchDevice.mha_gen for the dense decoding path.

The repository kernel runs on CUDA only (it calls .cuda() on its CPU branch), so the
harness runs this plain-torch implementation instead.  Only its causal position
before the target line matters for F012; it must return the same tuple shape the
caller stores into its caches.
"""

import torch
import torch.nn.functional as F


def mha_gen(inputs, attention_mask, w_q, b_q, w_k, b_k, w_v, b_v,
            w_out, b_out, w_ln, b_ln, n_head, k_cache, v_cache, donate,
            attn_sparsity, compress_cache, comp_config, p_w_q,
            partial_k_cache, speculation_stream, alpha, max_num_kv):
    from flexgen.pytorch_backend import TorchTensor

    x = inputs.data if hasattr(inputs, "data") else inputs
    b, tgt_s, h = x.shape
    src_s = min(attention_mask.shape[1], k_cache.shape[0] + 1)
    head_dim = h // n_head

    hidden = F.layer_norm(x, (h,), weight=w_ln.data, bias=b_ln.data)
    new_h = torch.cat((hidden, torch.ones_like(hidden)[:, :, :1]), dim=-1)

    q = F.linear(new_h, w_q.data, bias=None)
    k = F.linear(new_h, w_k.data, bias=None)
    v = F.linear(hidden, w_v.data, bias=b_v.data)

    q = q.view(b, tgt_s, n_head, head_dim)
    k = k.view(b, tgt_s, n_head, head_dim)
    v = v.view(b, tgt_s, n_head, head_dim)

    q = q.permute(0, 2, 1, 3).reshape(b * n_head, tgt_s, head_dim)
    k_new = k.permute(1, 0, 2, 3).reshape(tgt_s, b * n_head, head_dim)
    v_new = v.permute(1, 0, 2, 3).reshape(tgt_s, b * n_head, head_dim)

    k_hist = k_cache.data[:src_s - 1].to(k_new.dtype)
    v_hist = v_cache.data[:src_s - 1].to(v_new.dtype)
    k_all = torch.cat((k_hist, k_new), dim=0)
    v_all = torch.cat((v_hist, v_new), dim=0)

    k_mat = k_all.permute(1, 2, 0).reshape(b * n_head, head_dim, -1)
    v_mat = v_all.permute(1, 0, 2).reshape(b * n_head, -1, head_dim)

    attn = torch.softmax(torch.bmm(q, k_mat), dim=2)
    value = torch.bmm(attn, v_mat).view(b, n_head, tgt_s, head_dim)
    value = value.transpose(1, 2).reshape(b, tgt_s, h)
    value = F.linear(value, w_out.data, bias=b_out.data)
    value = value + x

    dev = k_cache.device
    return (TorchTensor.create_from_torch(value, dev),
            TorchTensor.create_from_torch(k_new, dev),
            TorchTensor.create_from_torch(v_new, dev),
            None)
