"""Driver: reach DeadlineScheduler._get_prefill_size_by_slack through the official
entry DeadlineScheduler._schedule with the memory_budget the harness passes in.

memory_budget is not an argument of the entry; it is a local derived inside the target
function as (free_blocks * block_size) // 32.  With block_size=16 and
num_gpu_blocks = 2 * memory_budget the product is exactly 32 * memory_budget, so the
local memory_budget seen at the target line equals the input value.
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
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.metrics.metrics_store import MetricsStore

BLOCK_SIZE = 16
PROMPT_TOKENS = 64
CHUNK_SIZE = 512
MAX_TOKENS = 8


def _model_config():
    # ModelConfig.__post_init__ downloads a HuggingFace config; the scheduler only reads
    # max_model_len, so build the value object without the network-bound constructor.
    cfg = ModelConfig.__new__(ModelConfig)
    cfg.model = "dummy"
    cfg.trust_remote_code = True
    cfg.download_dir = None
    cfg.load_format = "dummy"
    cfg.dtype = "float16"
    cfg.seed = 0
    cfg.revision = None
    cfg.max_model_len = 8192
    cfg.hf_config = None
    return cfg


def _make_scheduler(memory_budget):
    num_gpu_blocks = 2 * int(memory_budget)
    model_config = _model_config()
    scheduler_config = DeadlineSchedulerConfig(
        chunk_size=CHUNK_SIZE,
        scheduler_type="deadline",
    )
    cache_config = CacheConfig(block_size=BLOCK_SIZE, num_gpu_blocks=num_gpu_blocks)
    parallel_config = ParallelConfig(pipeline_parallel_size=1, tensor_parallel_size=1)
    MetricsStore.get_or_create_instance(
        ReplicaConfig(replica_id=0, output_dir="/tmp"),
        model_config,
        MetricsConfig(write_metrics=False),
    )
    return DeadlineScheduler(
        model_config, scheduler_config, cache_config, parallel_config
    )


def run(inputs):
    random.seed(0)
    scheduler = _make_scheduler(inputs["memory_budget"])

    prompt_token_ids = list(range(PROMPT_TOKENS))
    seq = Sequence(
        seq_id="0",
        prompt="",
        prompt_token_ids=prompt_token_ids,
        block_size=BLOCK_SIZE,
        eos_token_id=-1,
        arrival_time=0.0,
        sampling_params=SamplingParams(max_tokens=MAX_TOKENS),
    )
    # Keep the below-target eager-relegation branch off the wall-clock boundary.
    seq.tier = 0
    seq.ttft_deadline = 1e18
    scheduler.add_seq(seq)

    return scheduler._schedule()
