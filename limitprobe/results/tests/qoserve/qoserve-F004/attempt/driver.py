"""Driver: call DeadlineScheduler._schedule with a single running decode sequence.

The Region is the ``if self.tier > 0:`` branch in Sequence._get_TBT_deadline.  _schedule
reaches it unconditionally at line 200 through _sorting_key for every running sequence
whose prompt processing has finished; ``chunk_size`` is set to 0 so that the rest of
_schedule (decode/prefill bookkeeping that would need a GPU block manager) is skipped
after the branch decision.  The scheduler state is assembled directly because building a
real ModelConfig would download model metadata, which is impossible offline and plays no
part in the branch.
"""

import random

from sarathi.core.scheduler.deadline_scheduler import DeadlineScheduler
from sarathi.core.datatypes.sequence import Sequence
from sarathi.core.datatypes.sampling_params import SamplingParams


def _make_sequence(inputs):
    prompt_len = int(inputs["prompt_len"])
    seq = Sequence(
        seq_id="0",
        prompt="x" * prompt_len,
        prompt_token_ids=list(range(prompt_len)),
        block_size=int(inputs["block_size"]),
        eos_token_id=0,
        arrival_time=float(inputs["arrival_time"]),
        sampling_params=SamplingParams(temperature=0.0),
    )
    seq.tier = int(inputs["tier"])
    seq.tier_deadline = float(inputs["ttft_deadline"])
    seq.ttft_deadline = float(inputs["ttft_deadline"])
    seq.prompt_processing_finished = True
    seq.state._prompt_processing_completed_at = (
        float(inputs["arrival_time"]) + float(inputs["e2e_prefill_time"])
    )
    return seq


def run(inputs):
    random.seed(int(inputs["seed"]))
    seq = _make_sequence(inputs)

    scheduler = object.__new__(DeadlineScheduler)
    scheduler.execution_threshold = float(inputs["execution_threshold"])
    scheduler.execution_threshold_batched = float(inputs["execution_threshold_batched"])
    scheduler.hybrid_prioritization_param = 0.008
    scheduler.scheduler_type = "deadline"
    scheduler.chunk_size = int(inputs["chunk_size"])
    scheduler._prefill_queue = []
    scheduler._iteration_id = 0
    scheduler.last_prefill_size = 0
    scheduler.prev_call_time = -1
    scheduler.expected_prefill_throughput = 8500.0
    scheduler.prefill_throughput_weight_decay = 0.995
    scheduler.min_time = 1e18
    scheduler.max_time = 0
    scheduler.waiting = []
    scheduler.running = [seq]

    return scheduler._schedule()
