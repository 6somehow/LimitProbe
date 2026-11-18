"""Driver: call OptLM.__init__ with a minimal config for the selected layer count.

The nominal official entry (TorchDevice.mha) has no static path to OptLM.__init__, so this
driver calls OptLM.__init__ directly and records that in execution.entry_reason.
"""

from types import SimpleNamespace

from flexgen.infinigen.flex_opt import OptLM


def run(inputs):
    num_hidden_layers = int(inputs["num_hidden_layers"])
    config = SimpleNamespace(num_hidden_layers=num_hidden_layers)
    env = SimpleNamespace(gpu=object(), cpu=object(), disk=object())
    policy = SimpleNamespace(
        sep_layer=True,
        compress_weight=False,
        cpu_cache_compute=False,
        num_gpu_batches=1,
        act_gpu_percent=100,
        act_cpu_percent=0,
        act_disk_percent=0,
    )
    OptLM(
        config=config,
        env=env,
        path="",
        policy=policy,
        partial_weight_ratio=0.2,
        alpha=4,
        max_num_kv=400,
    )
