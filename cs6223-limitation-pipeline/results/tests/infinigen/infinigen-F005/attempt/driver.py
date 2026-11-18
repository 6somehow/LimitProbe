import argparse
import sys
from pathlib import Path

import numpy as np
import torch

_REPO = Path(sys.path[0]).resolve()
for _sub in ("speedup/flexgen", "speedup/infinigen"):
    _path = str(_REPO / _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)

import infinigen.flex_opt as _flex_opt


def _namespace(inputs):
    attempt = Path(__file__).resolve().parent
    args = argparse.Namespace()
    args.model = inputs["model"]
    args.path = str(attempt / inputs["path"])
    args.offload_dir = str(attempt / inputs["offload_dir"])
    args.prompt_len = int(inputs["prompt_len"])
    args.gen_len = int(inputs["gen_len"])
    args.cut_gen_len = inputs["cut_gen_len"]
    args.debug_mode = inputs["debug_mode"]
    args.gpu_batch_size = int(inputs["gpu_batch_size"])
    args.num_gpu_batches = int(inputs["num_gpu_batches"])
    args.percent = list(inputs["percent"])
    args.sep_layer = bool(inputs["sep_layer"])
    args.pin_weight = bool(inputs["pin_weight"])
    args.cpu_cache_compute = bool(inputs["cpu_cache_compute"])
    args.attn_sparsity = float(inputs["args.attn_sparsity"])
    args.compress_weight = bool(inputs["compress_weight"])
    args.compress_cache = bool(inputs["args.compress_cache"])
    args.log_file = "auto"
    args.no_log = True
    args.verbose = int(inputs["verbose"])
    args.overlap = bool(inputs["overlap"])
    args.alpha = int(inputs["alpha"])
    args.partial_weight_ratio = float(inputs["partial_weight_ratio"])
    args.max_num_kv = int(inputs["max_num_kv"])
    args.warmup_input_path = str(_REPO / inputs["warmup_input_path"])
    args.test_input_path = str(_REPO / inputs["test_input_path"])
    return args


def run(inputs):
    torch.manual_seed(0)
    np.random.seed(0)
    torch.set_num_threads(1)
    return _flex_opt.run_flexgen(_namespace(inputs))
