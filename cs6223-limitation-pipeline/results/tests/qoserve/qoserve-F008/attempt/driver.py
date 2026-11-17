"""Driver: build one Sequence and call DeadlineScheduler._schedule (the official entry = target)."""

import random
from types import SimpleNamespace

from sarathi.config import CacheConfig, DeadlineSchedulerConfig, ParallelConfig
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import TIER_DEADLINES, Sequence
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore

MetricsStore._instance = None


def run(inputs):
    random.seed(inputs["seed"])

    model_config = SimpleNamespace(max_model_len=inputs["max_model_len"])
    scheduler_config = DeadlineSchedulerConfig(
        max_num_seqs=inputs["max_num_seqs"],
        chunk_size=inputs["chunk_size"],
        execution_threshold=inputs["execution_threshold"],
        execution_threshold_batched=inputs["execution_threshold_batched"],
        scheduler_type=inputs["scheduler_type"],
        output_len_pred=inputs["output_len_pred"],
        hybrid_prioritization_param=inputs["hybrid_prioritization_param"],
    )
    cache_config = CacheConfig(
        block_size=inputs["block_size"],
        num_gpu_blocks=inputs["num_gpu_blocks"],
    )
    parallel_config = ParallelConfig(
        pipeline_parallel_size=inputs["pipeline_parallel_size"],
        tensor_parallel_size=inputs["tensor_parallel_size"],
    )

    scheduler = DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )

    seq = Sequence(
        seq_id="seq-0",
        prompt="x" * inputs["prompt_len"],
        prompt_token_ids=list(range(inputs["prompt_len"])),
        block_size=inputs["block_size"],
        eos_token_id=-1,
        arrival_time=float(inputs["arrival_time"]),
        sampling_params=SamplingParams(),
    )
    seq.tier = inputs["tier"]
    seq.tier_deadline = TIER_DEADLINES[seq.tier]
    seq.ttft_deadline = seq.tier_deadline
    seq.num_decode_tokens = inputs["num_decode_tokens"]

    scheduler.add_seq(seq)
    return scheduler._schedule()
