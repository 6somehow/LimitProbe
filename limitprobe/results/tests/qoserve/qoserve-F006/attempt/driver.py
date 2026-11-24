"""Driver: put the deadline scheduler in the state _schedule needs and call it.

The finding is about the slack value that _schedule passes to
DeadlineScheduler._get_prefill_size_by_slack.  The decoded sequence carries the
prescribed slack; its deadline object returns that slack when the scheduler
subtracts the current time, so the value handed to the target is exactly the
one in the input (0 or 1) on every run.
"""
import random
from types import SimpleNamespace

from sarathi.config import CacheConfig, DeadlineSchedulerConfig, ParallelConfig
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.datatypes.sequence_status import SequenceStatus
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore


class _PrescribedSlack:
    __slots__ = ("slack",)

    def __init__(self, slack):
        self.slack = slack

    def __sub__(self, other):
        return self.slack

    def __rsub__(self, other):
        return self.slack


class _SlackSequence(Sequence):
    def __init__(self, *args, slack=0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.prescribed_slack = slack

    def _get_TBT_deadline(self, execution_threshold, execution_threshold_batched):
        return _PrescribedSlack(self.prescribed_slack)


def run(inputs):
    random.seed(inputs["seed"])
    MetricsStore.get_or_create_instance(None, None, None)

    model_config = SimpleNamespace(max_model_len=inputs["max_model_len"])
    cache_config = CacheConfig(
        block_size=inputs["block_size"],
        num_gpu_blocks=inputs["num_gpu_blocks"],
    )
    parallel_config = ParallelConfig(
        pipeline_parallel_size=1, tensor_parallel_size=1
    )
    scheduler_config = DeadlineSchedulerConfig(
        chunk_size=inputs["chunk_size"],
        execution_threshold=inputs["execution_threshold"],
        execution_threshold_batched=inputs["execution_threshold_batched"],
        scheduler_type=inputs["scheduler_type"],
    )
    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    sampling_params = SamplingParams()

    decode = _SlackSequence(
        "decode",
        "",
        list(range(inputs["decode_prompt_tokens"])),
        inputs["block_size"],
        0,
        0.0,
        sampling_params,
        slack=float(inputs["min_slack"]),
    )
    decode.set_status(SequenceStatus.RUNNING)
    decode.set_status(SequenceStatus.PAUSED)
    decode.prompt_tokens_processed = inputs["decode_processed_tokens"]
    decode.prompt_processing_finished = True
    decode.state._prompt_processing_completed_at = 0.0
    decode.tier = 0
    decode.tier_deadline = inputs["tier_deadline"]
    decode.ttft_deadline = inputs["tier_deadline"]
    scheduler._allocate(decode)
    decode.mem_allocated = True

    prefill = Sequence(
        "prefill",
        "",
        list(range(inputs["prefill_prompt_tokens"])),
        inputs["block_size"],
        0,
        0.0,
        sampling_params,
    )
    prefill.prompt_tokens_processed = inputs["prefill_context_tokens"]
    prefill.tier = 1
    prefill.tier_deadline = inputs["tier_deadline"]
    prefill.ttft_deadline = inputs["tier_deadline"]

    scheduler.running.append(decode)
    scheduler.waiting.append(prefill)

    return scheduler.schedule()
