"""Driver: call DeadlineScheduler._schedule (the official entry and the Region target).

The scheduler object is built directly from real repository classes: the real
DeadlineBlockSpaceManager (so can_append_slot() is the repository's own
`num_free_gpu_blocks > 0`) and a real Sequence that has finished its prompt and
sits in the PAUSED state, which is what the Region's path prefix requires. The
only free variable in the pair is how many physical GPU blocks the block
allocator owns: the positive run allocates the single block the sequence needs
and leaves 0 free (can_append_slot() -> False), the negative run has one block
left over (can_append_slot() -> True).
"""

import random

import numpy as np

from sarathi.core.block_space_manager.deadline_block_space_manager import (
    DeadlineBlockSpaceManager,
)
from sarathi.core.datatypes.sampling_params import SamplingParams
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.datatypes.sequence_status import SequenceStatus
from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler


def _build_scheduler(inputs):
    random.seed(int(inputs["seed"]))
    np.random.seed(int(inputs["seed"]))

    block_size = int(inputs["block_size"])
    prompt_len = int(inputs["prompt_len"])

    block_manager = DeadlineBlockSpaceManager(
        block_size=block_size,
        num_gpu_blocks=int(inputs["num_gpu_blocks"]),
        max_model_len=int(inputs["max_model_len"]),
    )

    seq = Sequence(
        seq_id="seq-0",
        prompt="a short prompt",
        prompt_token_ids=list(range(prompt_len)),
        block_size=block_size,
        eos_token_id=int(inputs["eos_token_id"]),
        arrival_time=0.0,
        sampling_params=SamplingParams(max_tokens=int(inputs["max_tokens"])),
    )
    seq.set_status(SequenceStatus.RUNNING)
    seq.set_status(SequenceStatus.PAUSED)
    seq.update_prompt_tokens_processed(prompt_len)
    block_manager.allocate(seq)

    scheduler = object.__new__(DeadlineScheduler)
    scheduler.block_manager = block_manager
    scheduler.running = [seq]
    scheduler.waiting = []
    scheduler.chunk_size = int(inputs["chunk_size"])
    scheduler.execution_threshold = float(inputs["execution_threshold"])
    scheduler.execution_threshold_batched = float(inputs["execution_threshold_batched"])
    scheduler.scheduler_type = inputs["scheduler_type"]
    scheduler.hybrid_prioritization_param = float(inputs["hybrid_prioritization_param"])
    scheduler.output_len_pred = int(inputs["output_len_pred"])
    scheduler._prefill_queue = []
    scheduler.count = 0
    scheduler.max_time = 0
    scheduler.min_time = 1e18
    scheduler.pred_thres = 1.2
    scheduler.prev_call_time = -1
    scheduler.last_prefill_size = 0
    scheduler.prefill_token_limit = int(inputs["chunk_size"])
    scheduler.expected_prefill_throughput = 8500.0
    scheduler.prefill_throughput_weight_decay = 0.995
    scheduler._iteration_id = 0
    return scheduler


def run(inputs):
    scheduler = _build_scheduler(inputs)
    return scheduler._schedule()
