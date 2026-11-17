"""Driver for qoserve-F010: call DeadlineScheduler._schedule (the official entry) on a
CPU-constructed scheduler whose prefill queue already holds one request.

The only factor that differs between the positive and the negative input is the scheduler
type, encoded as an integer index so the harness can probe the neighbouring categories.
"""

import heapq
import random
import time

from sarathi.config import (
    CacheConfig,
    DeadlineSchedulerConfig,
    MetricsConfig,
    ParallelConfig,
    ReplicaConfig,
)
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore

# 0 and 1 are the two scheduler types the target condition accepts; 2..4 are the
# categories on the other side of the boundary. The order lets the harness probe the
# negative input (index 2) at index 1 (in-group) and index 3 (out-group).
SCHEDULER_TYPES = {
    0: "deadline",
    1: "deadline_no_dynamic_chunking",
    2: "srpf",
    3: "edf",
    4: "fcfs",
}


class _ModelConfig:
    """Only max_model_len is read by the scheduler constructor / block manager."""

    def __init__(self, max_model_len):
        self.max_model_len = max_model_len


# Disable the metrics store (the real repository class) once, before any scheduling.
MetricsStore.get_or_create_instance(
    ReplicaConfig(replica_id=0, output_dir="."),
    _ModelConfig(4096),
    MetricsConfig(write_metrics=False),
)


def run(inputs):
    seed = int(inputs["seed"])
    random.seed(seed)

    scheduler_type = SCHEDULER_TYPES[int(inputs["scheduler_type_index"])]
    model_config = _ModelConfig(int(inputs["max_model_len"]))
    scheduler_config = DeadlineSchedulerConfig(
        scheduler_type=scheduler_type,
        chunk_size=int(inputs["chunk_size"]),
    )
    cache_config = CacheConfig(
        block_size=int(inputs["block_size"]),
        num_gpu_blocks=int(inputs["num_gpu_blocks"]),
    )
    parallel_config = ParallelConfig(pipeline_parallel_size=1, tensor_parallel_size=1)

    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    prompt_len = int(inputs["prompt_len"])
    seq = Sequence(
        seq_id="seq-0",
        prompt="x" * prompt_len,
        prompt_token_ids=list(range(prompt_len)),
        block_size=int(inputs["block_size"]),
        eos_token_id=0,
        arrival_time=time.monotonic(),
        sampling_params=SamplingParams(temperature=0.0, max_tokens=int(inputs["max_tokens"])),
    )
    # Far-future TTFT deadline: the eager-relegation check inside the target body never
    # fires, so the prefill loop visits the target decision exactly once in both runs.
    seq.ttft_deadline = float(inputs["ttft_deadline"])
    heapq.heappush(scheduler._prefill_queue, seq)

    return scheduler._schedule()
