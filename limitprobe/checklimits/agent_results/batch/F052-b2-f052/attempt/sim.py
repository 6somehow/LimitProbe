"""CPU stand-in for the GPU flash-attention call reached only AFTER the batch-size assert."""

import torch


def flash_attn(q, k, v, softmax_scale=None, **kwargs):
    return torch.zeros_like(q)
