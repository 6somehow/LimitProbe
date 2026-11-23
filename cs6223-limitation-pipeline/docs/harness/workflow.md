# Development workflow (template)

Copy to `<repo>/docs/harness/workflow.md`. This file owns the task package, the return block, dispatch, review, integration, branches and worktrees, the DAG, decisions, and logs. Executor and model choice is in [models.md](models.md).

`W` is the workspace. `R` is the main checkout `W/<repo>` (branch `dev`). Task worktrees are in `W/<repo>-wt/<TASK-ID>/`. Dispatch logs are in `W/<repo>-wt/logs/`.

## Roles

- **Controller.** Claude Code on the controller host. It writes task packages, keeps the DAG, dispatches, reviews, integrates into `dev`, and records decisions.
- **Code agent.** A Codex or Claude process for one task. It works only in its task worktree. It does not commit, merge, or start other agents.
- **Read-only subagent.** A Claude subagent in the controller session. It reads and reports. It is not an independent review.
- **User.** Owns the goal documents, the scope, and each decision that lowers a guarantee or uses new resources.

## Task package

The controller writes one package per task in `development/tasks/<TASK-ID>.md`.

```yaml
task_id: TASK-001
dag_node: REQUIRED           # the DAG node that this task implements
serves: REQUIRED             # harness, a scenario, or a result of the goal documents
base_sha: REQUIRED           # dev SHA of the worktree
branch: agent/TASK-001/short-name
worktree: REQUIRED           # absolute path
goal: REQUIRED
allowed_paths: []            # repository-relative; an empty list grants no write access
non_goals: []
references: []               # sections, not whole documents
executor: codex              # codex | claude
model_profile: medium        # models.md
reason: REQUIRED             # why this executor and profile
limits:
  attempts: 2
  max_runtime_seconds: null  # required for a remote run or a long run
  gpu: none                  # none, or a capability class (platforms.md)
  network: 0                 # 1: sockets, SSH, internet
checks: []                   # real commands and the expected result
```

- If a limit is missing for a long or remote task, the agent reports it first. It does not start an unbounded task.
- If a task replaces a placeholder (for example a `NotImplementedError`), the controller searches the tests for that placeholder and adds those test files to `allowed_paths`.
- Verify each path of a package with `ls` before dispatch.

## Return block

The code agent appends this block to its package and repeats it as its final message. This append is the only write outside `allowed_paths`.

```text
STATUS: DONE | PARTIAL | BLOCKED
COMMITS: pending controller commit
EXECUTOR: <executor; requested model -> actual model id; effort>
SUMMARY: <behavior change and failure behavior>
CHECKS: <command; PASS | FAIL | NOT_RUN | BLOCKED | INVALID_RUN; evidence path>
GPU: <node, UUIDs, vacancy result, monitor verdict or SCHEDULER_ALLOCATED; "none" if not used>
SELF-REVIEW: <each item of the review checklist: the probe or test that covers it, or why it does not apply>
RISKS: <conflicts, assumptions, follow-up work>
```

## Dispatch

1. Check the DAG (`ready` nodes only). Do not dispatch a task that has no DAG node.
2. Create the worktree: `git -C R worktree add -b agent/TASK-001/short-name W/<repo>-wt/TASK-001 <dev-sha>`.
3. Commit the package on that branch, or copy it into the worktree.
4. Write the prompt with a script (not `sed`). The prompt has a header and the current ruling, and points to the package file. Keep it under 128 KiB.
5. Submit the job to the dispatch scheduler, or start the adapter detached: `setsid nohup tools/dispatch/codex.sh TASK-001 <model> <effort> > /dev/null 2>&1 < /dev/null &`.
6. Set the DAG node to `running`.

- Adapters run the gateway core in a memory scope. `MEM=<size>` sets MemoryMax (default `3G`). `NET=1` gives Codex network access.
- `claude.sh --review` starts a read-only reviewer. It returns `VERDICT: ACCEPT | NEEDS_CHANGES | BLOCKED`.
- A retry uses a new task ID (`TASK-001b`) in the same worktree. The gateway never overwrites a log.
- End signal: the last non-empty line of `<TASK-ID>.err` is `exit=<n> end=<time>`. Also check the scope state: an OOM kill writes no `exit=` line. A failed Codex run can end with no `.last.md`.
- To stop a run, stop its scope unit. Never use `kill $(pgrep -f "<text>")` in one call.

Dispatch scheduler (optional, recommended once more than one agent runs). It waits for quota, keeps the agent limit, and continues a run after a usage limit. Submit through it and wait on its events. Do not write hand watcher loops or manual continuations.

## Long runs and the controller

- After every job submit or agent dispatch, start a background wait in the same turn. Never end a turn with work running and no wait. (An 8-hour idle gap in robodb followed a turn that ended without a wait.)
- When a job fails, read its logs first (the step log, the engine log, the guard output). Bound retries. Do not resubmit blindly.
- Run drivers as stateful scripts with a state file and a log, not as one long command. Details and pitfalls: [remote-runs.md](remote-runs.md).
- If a run was cut by a user order, write down in the state file what is done, what is todo, and how to resume. Mark the entry "not counted" for failure limits.
- Write a new design version as a decision record before the run (for example a changed init-state range). A run that deviates without a record is not comparable.

## Review and integration

- One complete review pass per round. The review checks the package requirements and compares with `dev`.
- Only two kinds of finding block a merge: a regression against `dev`, and an unmet requirement of the package. Other findings go into the backlog.
- A fix round fixes every blocking finding of that review.
- Review crosses the model family. A review of Codex work uses Claude, and the reverse.
- The controller runs the per-task checks, including tests that import the changed modules. It never checks a worktree that an agent is still editing.
- Merge into `dev` with a normal merge. Capture the exit code of the check before the commit: never `check | tail && git commit`.
- After a revert of a merge, never merge `dev` into the branch (a fast-forward drops the work). A re-merge needs a revert of the revert.
- The controller commits agent work (agents do not commit).

## Branches, worktrees, and cleanup

- Branch `agent/<TASK-ID>/<name>` from `base_sha`. One owner per writable workspace. On a remote node, use a node-local clone and exchange commits through a bundle.
- A worktree is complete if its HEAD is an ancestor of `dev`, `git status --porcelain` is empty, the record and logs are saved, cited evidence is copied to `<data>/`, and no process uses it. Then `git worktree remove <path>` (no `--force`) and `git worktree prune`. Keep the branch.
- The controller resolves conflicts. No whole-side `ours` or `theirs`.

## Work graph and decisions

- `development/dag.yaml` is the work graph. The controller keeps it current at each package, dispatch, merge, block, and decision. Run the DAG `check` and `ready` commands before each dispatch round.
- Record each user decision with an ID and a date in `development/decisions.md`. A new decision names the one that it replaces. Remove the replaced rule from the owner files in the same commit.
- Current facts only in `development/state.md`. History goes into `development/log/`.

## Evidence

- A run record is the evidence. Do not build stage gates, seals, or byte-pinned manifests unless the user asks.
- Write the counting rules of an experiment and commit them before the first run. Use a fresh output directory for each run.
- Report PASS, FAIL, NOT_RUN, BLOCKED, and INVALID_RUN separately. A tool that exits 0 is not a PASS: check the artifacts.
