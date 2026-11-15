# check_limits: instructions for the code agent

You verify ONE claim about a research code base ("a finding") by designing and running a small test on a
CPU-only machine. A deterministic harness runs your test, records what happened, and decides the verdict
and a confidence level. **You never decide the verdict.** You make the evidence strong; the harness
audits everything you declare and recomputes it.

## What the harness gives you

Run everything through the wrapper `CL` (its absolute path is in your task message):

| command | what it does |
|---|---|
| `CL task <finding>` | prints the claim, the target statement, its condition, the call chain, the source around it |
| `CL init <finding> --out attempt` | creates `attempt/{manifest.json, form.json, driver.py}` |
| `CL lint --attempt attempt` | static check against the design rules below. Run it before every harness run |
| `CL run --attempt attempt --out out --fast` | main pair only (~5 s). Use while developing |
| `CL run --attempt attempt --out out` | full run (~40 s): repeats, untraced run, mutation, boundary probes, clean-checkout replay. Prints the verdict, the level and a list of `next_steps` |

Work only inside your workspace directory. The repository under `third_party/` is read-only evidence:
never edit it (the harness diffs it against the pinned commit and a change makes the result invalid).
Do not edit anything under `checklimits/` except your own attempt directory.

## What you produce: an attempt package

* `driver.py`: `def run(inputs): ...` calls the OFFICIAL entry point (first function of the call chain) with
  values built from `inputs`. Import the code under test at module level. Set seeds. CPU only. No asserts of
  your own, and never catch the exception you are looking for.
* `form.json`: your declarations (below). `manifest.json` is pre-filled.
* optional `sim.py`: CPU implementations for GPU-only calls that run AFTER the target statement.
* optional `condition.py`: `def predicate(locals) -> bool`, only if the Region condition cannot be evaluated.

## What counts as "the effect" depends on the Region's outcome

| outcome in the task | effect the harness looks for | oracle you declare | observed text |
|---|---|---|---|
| `reject` | an exception raised AT the target line | `type: exception`, `spec: "<ExceptionClass> raised at <file>:<line>"` | `AssertionError at <file>:<line>` / `no exception at <file>:<line>` |
| `fallback`, `mechanism_variant` | the branch decision at the target line is TAKEN (the `if`/`while` body runs) | `type: path_hook`, `spec: "branch taken at <file>:<line>"`, `signal_location` = the line, tier O4 | `branch taken at <file>:<line>` / `branch not taken at <file>:<line>` |
| `state_dependent` | the same branch decision, in the LAST driver call, after earlier calls changed the program state | same as above, plus preludes (below) | same as above |
| anything else | not judged yet: the harness answers `not_run` | | |

A branch effect needs the target to be an `if` or `while` statement. The Region condition says when the branch
is taken; at the target line it must be TRUE on the positive input and FALSE on the negative one, exactly as for
`reject`. What happens after the decision does not matter for the verdict (the harness stops at the decision in
its probe runs), but your negative run may need stand-ins below the target as before.

**state_dependent.** The driver is called once per input. To put the program in a state, list the earlier calls in
`design.positive_prelude` / `design.negative_prelude` (each entry is a full input dict, run in order, in the same
process, before the checked call). Positive and negative then use the SAME final input and differ only in the
prelude; set `boundary_variable` to `"prelude"`. State findings usually have the state in a module-level variable,
so the positive case is a fresh process (no prelude) and the negative case makes one earlier call. Positive and
negative must still differ in exactly one thing. The harness cannot probe the neighbours of a state, so D5 stays
"residual" and the level is at most L2; guards such as `x is None` have only one or two mutants, so D3 is at most
"residual" (fewer than 4 mutants) and the level is at most L1. Say so in your summary instead of trying to hide it.

## The test you must design (T1 to T9) and the doubt each rule removes

The harness lists 14 ways its verdict could be wrong ("defeaters", D1 to D14). A level is only as high as
the defeaters you let the harness eliminate. Your design decides this:

1. **Reach (D1).** The positive input must execute the target line. Check the path prefix in the task: all
   earlier guards must hold, or the run stops before the target.
2. **Condition (D2).** At the target line the Region condition must be TRUE on the positive input and FALSE on
   the negative one. Pick inputs from the witness_hint; the condition is evaluated on the real local variables.
3. **Oracle, registered first (D4, T1).** Declare the oracle before you run anything: for a `reject` outcome,
   `type: exception`, `spec` naming the exception class and the location, `signal_location` = exactly the
   Region's `file:line`, `tier: O4`. If you change the oracle or the expected results later, the harness
   counts it and the level drops. Changing inputs or mocks later is fine.
4. **A minimal pair at the boundary (D5, T2).** Positive and negative input differ in exactly ONE factor
   (`boundary_variable`), and the negative is the neighbouring point on the other side of the boundary. The
   harness probes the neighbours of your negative input at full scale and checks this itself.
5. **An oracle that can see the effect (D3).** The harness mutates the target statement (negate, swap
   comparison, delete, constant +/-1) in a temporary copy; your test must flip for most mutants (Wilson lower
   bound >= 0.5, at least 4 mutants). If some mutants survive, no input of yours separates them from the
   original. For a set-membership guard such as `x in {a, b, c}`, add one input per member to
   `design.extra_negatives` (inputs that must show no effect); each fires under the mutant that changes its member.
6. **No stand-ins before the target (D6).** The verdict rests on what happened up to the target line. Anything
   you replace that is touched BEFORE the target makes the evidence "simulated" and caps the level. Put every
   mock behind the target, and keep the target's own function and its callers real.
7. **Stand-ins after the target, declared (D6, T5).** If the negative run would otherwise crash below the
   target for lack of a GPU, declare mocks with `kind: patch`, `behavior: sim`, `impl: "sim.py::func"` and say
   what the stand-in is: `sim_class: repo_reference` (it calls a reference implementation that ships in the
   repository, best), `independent_native` (plain torch you wrote), or `stub` (canned value, worst). Prefer
   running the repository's real code and replacing only the GPU kernel launchers. Never edit the repository.
8. **Small scale is allowed, silently wrong is not (D10, T3).** If you shrink a size to keep it fast, declare it
   in `design.scale` with the factor and an invariance argument (why the target decision cannot depend on the
   size). The harness re-runs both inputs at the full witness size up to the target and compares.
9. **Free parameters (T3).** Every value your driver chooses that is not in the witness_hint (head count, dtype,
   seed, defaults) goes into `design.free_parameters` with a reason. `lint` finds the ones you forgot.
10. **Official entry (D14, T4).** Call `call_chain[0]`. A deeper function needs `execution.entry_reason`.
11. **Offline, deterministic, pinned (T6, D8, D9).** No network, fixed seeds, single thread. The harness repeats
    the run in fresh processes and replays it in a fresh checkout of the pinned commit.
12. **Scope (T9, D13).** If the task says `out_of_scope`, only record it.

## The form (`form.json`): fill it honestly

`claims` are your predictions of what the harness will measure (target reached, decision outcomes seen,
condition true on positive / false on negative, what was observed on each input). The harness recomputes every
one; a wrong claim lowers `form_integrity`, which is reported next to the level. Fill `claims` from a real run
(`--fast` report), never from hope. `positive_observed` looks like `AssertionError at <file>:<line>`;
`negative_observed` looks like `no exception at <file>:<line>`.

## Loop

1. `CL task <finding>`; read the target and the code that leads to it in the repository.
2. `CL init`, write `driver.py`, fill `form.json` (oracle first). `CL lint` until no errors.
3. `CL run ... --fast`, read `out/*.report.json` (`positive`, `negative`, `target_hits`), fix the claims.
4. `CL run ...` (full). Read `next_steps`: each line names a defeater that is not yet eliminated and what
   would remove it. Fix the cause, never the report. Repeat from step 3 while it is worth it.
5. Stop when the level is L3, or when the remaining `next_steps` cannot be fixed by you, or after 6 full runs.
   Then print a short summary: verdict, level, open defeaters and why.

## Forbidden

Editing `third_party/`, the harness, the data, or other attempts; reading or printing any credential; network
access; using a stand-in to make the target line "work"; claiming something you did not observe.
