"""Driver for qoserve-F009: call DeadlineScheduler._schedule with a non-empty prefill queue.

The Region is the `if self.scheduler_type == 'deadline':` branch inside `_schedule`; the entry in the
call chain is `_schedule` itself.  A scheduler is built, one real Sequence is placed in its prefill
queue (the path prefix the task names), and `_schedule` is called.  Everything touched before the
target line is the repository's own code.
"""

import heapq
import random
from types import SimpleNamespace

from sarathi.config import CacheConfig, DeadlineSchedulerConfig, ParallelConfig
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore


def run(inputs):
    random.seed(0)
    MetricsStore.get_or_create_instance(
        SimpleNamespace(), SimpleNamespace(), SimpleNamespace(write_metrics=False)
    )

    scheduler_type = inputs["scheduler_type"]
    model_config = SimpleNamespace(max_model_len=inputs["max_model_len"])
    scheduler_config = DeadlineSchedulerConfig(
        chunk_size=inputs["chunk_size"],
        execution_threshold=0.1,
        execution_threshold_batched=0.4,
        scheduler_type=scheduler_type,
        output_len_pred=15,
        hybrid_prioritization_param=0.008,
    )
    cache_config = CacheConfig(
        block_size=inputs["block_size"], num_gpu_blocks=inputs["num_gpu_blocks"]
    )
    parallel_config = ParallelConfig(pipeline_parallel_size=1, tensor_parallel_size=1)

    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    seq = Sequence(
        seq_id="f009-0",
        prompt="prompt",
        prompt_token_ids=list(range(inputs["prompt_len"])),
        block_size=inputs["block_size"],
        eos_token_id=1,
        arrival_time=1.0,
        sampling_params=SamplingParams(),
    )
    seq.arrival_time = 1.0
    seq.ttft_deadline = 1e18
    seq.scheduler_type = scheduler_type
    heapq.heappush(scheduler._prefill_queue, seq)

    return scheduler._schedule()
