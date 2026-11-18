"""Driver: build a real DeadlineScheduler and call its _schedule entry point.

The target is the branch at sarathi/core/scheduler/deadline_scheduler.py:231,
`if seq.tier >= 1:`.  The only factor that differs between the positive and the
negative input is the tier of the single waiting sequence.

No repository code is replaced: the scheduler, the block-space manager, the
Sequence object and the queue logic all come from the pinned checkout.  ModelConfig
is instantiated with object.__new__ only to skip its network/HF __post_init__; the
scheduler reads just max_model_len from it.
"""

import random

from sarathi.config import (
    CacheConfig,
    DeadlineSchedulerConfig,
    MetricsConfig,
    ModelConfig,
    ParallelConfig,
    ReplicaConfig,
)
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence, TIER_DEADLINES
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore

random.seed(0)


def _model_config(max_model_len):
    cfg = object.__new__(ModelConfig)
    cfg.max_model_len = max_model_len
    cfg.model = "offline-cpu-dummy"
    cfg.seed = 0
    return cfg


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)

    model_config = _model_config(int(inputs["max_model_len"]))
    MetricsStore.get_or_create_instance(
        ReplicaConfig(), model_config, MetricsConfig(write_metrics=False)
    )

    scheduler_config = DeadlineSchedulerConfig(
        chunk_size=int(inputs["chunk_size"]),
        execution_threshold=float(inputs["execution_threshold"]),
        execution_threshold_batched=float(inputs["execution_threshold_batched"]),
        scheduler_type="deadline",
        output_len_pred=int(inputs["output_len_pred"]),
    )
    cache_config = CacheConfig(
        block_size=int(inputs["block_size"]),
        num_gpu_blocks=int(inputs["num_gpu_blocks"]),
    )
    parallel_config = ParallelConfig(
        pipeline_parallel_size=1, tensor_parallel_size=1
    )

    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    prompt_len = int(inputs["prompt_len"])
    block_size = int(inputs["block_size"])
    seq = Sequence(
        seq_id="seq-0",
        prompt="x" * prompt_len,
        prompt_token_ids=list(range(prompt_len)),
        block_size=block_size,
        eos_token_id=-1,
        arrival_time=float(inputs["now"]),
        sampling_params=SamplingParams(temperature=0.0, max_tokens=1),
    )
    tier = int(inputs["tier"])
    seq.tier = tier
    seq.tier_deadline = TIER_DEADLINES[tier % len(TIER_DEADLINES)]

    scheduler.add_seq(seq)
    return scheduler._schedule()
