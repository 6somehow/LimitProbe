import sys, os
sys.dont_write_bytecode = True
repo = '<project-root>/third_party/InfiniGen'
sys.path.insert(0, os.path.join(repo, 'speedup', 'flexgen'))
sys.path.insert(1, os.path.join(repo, 'speedup', 'infinigen'))
sys.path.insert(2, repo)
import numpy as np
from types import SimpleNamespace
from flexgen.utils import Task, ExecutionEnv, ValueHolder
from flexgen.compression import CompressionConfig
from flexgen.pytorch_backend import TorchDevice, TorchMixedDevice
from infinigen.flex_opt import Policy, SelfAttention


def build(sparsity):
    gpu_batch_size = 2
    n_head = 2
    head_dim = 4
    input_dim = n_head * head_dim
    config = SimpleNamespace(n_head=n_head, input_dim=input_dim, dtype=np.float16)
    task = Task(inputs=None, prompt_len=4, gen_len=2, cut_gen_len=None,
                do_sample=False, temperature=1.0, stop=None)
    comp = None
    policy = Policy(gpu_batch_size=gpu_batch_size, num_gpu_batches=1,
                    w_gpu_percent=0, w_cpu_percent=100,
                    cache_gpu_percent=50, cache_cpu_percent=50,
                    act_gpu_percent=0, act_cpu_percent=100,
                    overlap=False, sep_layer=True, pin_weight=False,
                    cpu_cache_compute=True, attn_sparsity=float(sparsity),
                    compress_weight=False, comp_weight_config=comp,
                    compress_cache=False, comp_cache_config=comp)
    cpu = TorchDevice('cpu')
    cpu2 = TorchDevice('cpu')
    mixed = TorchMixedDevice([cpu, cpu2, TorchDevice('cpu')])
    env = ExecutionEnv(gpu=cpu, cpu=cpu, disk=None, mixed=mixed)
    cpu.init_attention_compute_workspace(config, task, policy)
    att = SelfAttention(config, env, policy, layer_id=0, enable_prefetching=False)
    att.set_task(task)
    k_home, v_home = mixed.init_cache_one_gpu_batch(config, task, policy)
    print('k_home dtype', k_home.dtype, 'shape', k_home.shape,
          'seg', k_home.data[1], 'gpu0', k_home.data[0][0] is not None)
    cache_home = ValueHolder()
    cache_home.store((k_home, v_home))
    cache_read_buf = ValueHolder()
    try:
        att.load_cache(cache_home, cache_read_buf, 1)
        print('sparsity', sparsity, '-> no exception')
    except BaseException as e:
        tb = e.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        print('sparsity', sparsity, '->', type(e).__name__,
              'at', os.path.basename(tb.tb_frame.f_code.co_filename), tb.tb_lineno)


for s in (1.0, 0.999, 0.5, 1.001):
    build(s)
