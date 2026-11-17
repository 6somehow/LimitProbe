"""Driver for qoserve-F001: call DeadlineScheduler._schedule on a decoder sequence.

The positive input marks the sequence as not paused (RUNNING); _schedule reaches
`assert seq.is_paused()` and rejects it. The negative input marks the same sequence
PAUSED, so the assertion passes. Everything is built from the inputs dict; the real
repository code runs for the whole call up to (and, on the negative, past) the target.
"""

import random
import types

from sarathi.config import (
    CacheConfig,
    DeadlineSchedulerConfig,
    MetricsConfig,
    ParallelConfig,
    ReplicaConfig,
)
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.datatypes.sequence_status import SequenceStatus
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore


def run(inputs):
    random.seed(int(inputs["seed"]))

    model_config = types.SimpleNamespace(max_model_len=int(inputs["max_model_len"]))
    MetricsStore.get_or_create_instance(
        ReplicaConfig(), model_config, MetricsConfig(write_metrics=False)
    )
    scheduler_config = DeadlineSchedulerConfig(
        chunk_size=int(inputs["chunk_size"]),
        scheduler_type="deadline",
    )
    cache_config = CacheConfig(
        block_size=int(inputs["block_size"]),
        num_gpu_blocks=int(inputs["num_gpu_blocks"]),
    )
    parallel_config = ParallelConfig(
        pipeline_parallel_size=1,
        tensor_parallel_size=1,
    )
    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    prompt_len = int(inputs["prompt_len"])
    seq = Sequence(
        seq_id="0",
        prompt="hello",
        prompt_token_ids=list(range(1, prompt_len + 1)),
        block_size=int(inputs["block_size"]),
        eos_token_id=int(inputs["eos_token_id"]),
        arrival_time=float(inputs["arrival_time"]),
        sampling_params=SamplingParams(),
    )
    seq.set_status(SequenceStatus.RUNNING)
    if bool(inputs["paused"]):
        seq.set_status(SequenceStatus.PAUSED)
    seq.update_prompt_tokens_processed(prompt_len)
    scheduler.block_manager.allocate(seq)
    scheduler.running = [seq]

    return scheduler._schedule()
