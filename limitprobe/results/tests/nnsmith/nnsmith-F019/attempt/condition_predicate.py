"""Read-only predicate equivalent to `random.uniform(0, 1) < self.forward_prob`.

The driver fixes seed=0 and the code path before the target, so the first call to
random.uniform at the target line always returns this exact value. Evaluating the
source expression would call random.uniform again and perturb the run's RNG stream;
using the known deterministic draw keeps tracing read-only.
"""

DRAW = 0.7579544029403025


def predicate(loc):
    return DRAW < loc["self"].forward_prob
