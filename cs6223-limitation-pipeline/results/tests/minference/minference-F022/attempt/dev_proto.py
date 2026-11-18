import sys, types, importlib.util, pathlib, time, os, json, math
sys.dont_write_bytecode = True
REPO = pathlib.Path('<project-root>/third_party/MInference/minference').resolve()
for name, path in [('minference', REPO), ('minference.modules', REPO/'modules'), ('minference.ops', REPO/'ops')]:
    m = types.ModuleType(name); m.__path__ = [str(path)]; sys.modules[name] = m
for name, attrs in [('minference.ops.block_sparse_flash_attention', ['block_sparse_attention']),
                    ('minference.ops.pit_sparse_flash_attention_v2', ['vertical_slash_sparse_attention'])]:
    m = types.ModuleType(name)
    for a in attrs:
        setattr(m, a, lambda *x, **k: None)
    sys.modules[name] = m
import torch
_real_arange, _real_full = torch.arange, torch.full
def arange(*a, **k):
    if k.get('device') == 'cuda': k['device'] = 'cpu'
    return _real_arange(*a, **k)
def full(*a, **k):
    if k.get('device') == 'cuda': k['device'] = 'cpu'
    return _real_full(*a, **k)
torch.arange, torch.full = arange, full
spec = importlib.util.spec_from_file_location('minference.modules.minference_forward', REPO/'modules'/'minference_forward.py')
MF = importlib.util.module_from_spec(spec); sys.modules[spec.name] = MF
spec.loader.exec_module(MF)


def make_mask(q_len, dtype=torch.float32):
    attention_mask = torch.full((q_len, q_len), torch.finfo(dtype).min)
    mask_cond = torch.arange(attention_mask.size(-1))
    attention_mask.masked_fill_(mask_cond < (mask_cond + 1).view(attention_mask.size(-1), 1), 0)
    return attention_mask[None, None, :]


def scores(q, k):
    q_len = q.shape[2]; head_dim = q.shape[-1]
    attention_mask = make_mask(q_len).to(q.dtype)
    attn_weights = torch.matmul(q, k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask
    attn_weights = torch.nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(q.dtype)

    def vertical_and_slash(vertical_size, slash_size):
        last_q = 64
        qk_idxs = [ii + q_len for ii in list(range(-last_q, 0, 1))]
        qk = torch.matmul(q[:, :, qk_idxs, :], k.transpose(2, 3)) / math.sqrt(head_dim) + attention_mask[:, :, qk_idxs]
        qk = torch.nn.functional.softmax(qk, dim=-1, dtype=torch.float32)
        vertical = qk.sum(-2, keepdim=True)
        vertical[..., :30] = torch.inf
        vertical_topk = torch.topk(-vertical, q_len - vertical_size, -1).indices
        slash = MF.sum_all_diagonal_matrix(qk)[..., :-last_q + 1]
        slash[..., -30:] = torch.inf
        slash = torch.topk(slash, slash_size, -1).indices - (q_len - 1)
        slash = torch.stack([torch.sparse.spdiags(torch.ones(slash_size, q_len), slash.cpu()[0][_], (q_len, q_len)).to_dense() for _ in range(1)]).to(q.device)
        est_attn = torch.ones_like(attn_weights)
        dim = 3
        est_attn = est_attn.scatter(3, vertical_topk.expand(*est_attn.shape[:dim], vertical_topk.shape[dim], *est_attn.shape[dim + 1:]), 0)
        est_attn = est_attn + slash
        est_attn = (est_attn > 0).float()
        est_attn = torch.tril(est_attn)
        attn_weights_x = attn_weights * est_attn
        res3 = attn_weights_x[:, :, 2500:].sum(-1).mean(-1).squeeze().float().detach().cpu().numpy()
        if vertical_size == 3500:
            print('DBG v3500 rowsum3000', float(attn_weights[0,0,3000].sum()), 'slice3000', float(attn_weights[0,0,3000,2500:].sum()), 'mask3000nz', int((attention_mask[0,0,3000] > -1e30).sum()), 'slice_mean', float(attn_weights[:, :, 2500:].sum(-1).mean()), 'aw_sum', float(attn_weights[:, :, 2500:].sum(-1).mean(-1)), 'x_sum', float(attn_weights_x[:, :, 2500:].sum(-1).mean(-1)), 'same', bool(torch.equal(attn_weights_x, est_attn)), 'shapes', attn_weights.shape, est_attn.shape)
        return res3, est_attn

    def stream_llm(vertical_size, slash_size):
        mask = torch.triu(torch.tril(torch.ones(q_len, q_len), 0), -slash_size).to(q)
        mask[:, :vertical_size] = 1
        mask = mask.unsqueeze(0).unsqueeze(1)
        est_attn = torch.tril(mask)
        attn_weights_x = attn_weights * est_attn
        res3 = attn_weights_x[:, :, 2500:].sum(-1).mean(-1).squeeze().float().detach().cpu().numpy()
        return res3, est_attn

    def block_sparse(topk_ratio, slash_size=None):
        block_num = (q_len - 1) // 32 + 1
        block_q = torch.zeros(1, 1, block_num * 32, head_dim).to(q)
        block_q[:, :, :q_len] = q
        block_q = block_q.reshape(1, 1, block_num, 32, -1).mean(-2)
        block_k = torch.zeros(1, 1, block_num * 32, head_dim).to(k)
        block_k[:, :, :q_len] = k
        block_k = block_k.reshape(1, 1, block_num, 32, -1).mean(-2)
        qk = torch.matmul(block_q, block_k.transpose(2, 3)) + attention_mask[:, :, :block_num, :block_num]
        est_attn = torch.ones_like(qk)
        block_topk = torch.topk(-qk, block_num - block_num // topk_ratio, -1).indices
        dim = 3
        est_attn = est_attn.scatter(3, block_topk.expand(*est_attn.shape[:dim], block_topk.shape[dim], *est_attn.shape[dim + 1:]), 0)
        est_attn = est_attn.unsqueeze(3).unsqueeze(-1).repeat(1, 1, 1, 32, 1, 32).reshape(1, 1, block_num * 32, block_num * 32)[..., :q_len, :q_len]
        est_attn = torch.tril(est_attn)
        attn_weights_x = attn_weights * est_attn
        res2 = attn_weights_x[:, :, 2500:].sum(-1).mean(-1).squeeze().float().detach().cpu().numpy()
        return res2, est_attn

    out = {}
    out['stream'] = stream_llm(100, 800)
    for vs, ss in [(30, 800), (100, 750), (500, 700), (3500, 100)]:
        out[f'v{vs}'] = vertical_and_slash(vs, ss)
    out['block'] = block_sparse(100)
    return out
