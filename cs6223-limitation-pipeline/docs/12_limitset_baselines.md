# Limitset baselines

The baseline command currently supports planning only. Actual B1 and B2 execution,
output adaptation, and cost recording are not implemented. A non-dry run exits
with an error instead of producing baseline results.

The scorer and baseline runner must not run simultaneously: their shared relay
is stopped when its starter exits.
