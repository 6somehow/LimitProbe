# Code agents: executors, models, effort, accounts (template)

Copy to `<repo>/docs/harness/models.md`. This file owns the choice of executor, model, effort, and account. The controller chooses by risk, scope, and uncertainty of the cause. It does not choose by the number of lines. Check the model list again after a CLI upgrade.

## Executors

| Executor | Entry | Writes code | Use |
|---|---|---|---|
| `codex` | `tools/dispatch/codex.sh` | yes (the controller commits) | Most implementation; remote and SSH work; reviews of Claude work |
| `claude` | `tools/dispatch/claude.sh` (no `--account`) | yes (the controller commits) | Local code and documents; reviews of Codex work (`--review`) |
| `claude-sub` | `.claude/agents/` | no (read-only) | Search, log summaries, a first look at a diff. Not an independent review. |

- Remote or SSH work goes to `codex`. The Claude allowlist has no `ssh`, `scp`, or `rsync`.
- Code generation and its review use different sessions and different model families.
- Codex takes the larger share of implementation. Claude takes local documents, harness work, and reviews of Codex work.

## Executor principle (user order 2026-11-21; applies to every project)

1. Codex is the default. It takes simple and well-defined implementation, reading documents and code, local and bounded tasks, routine documents, harness scripts, and runs. Use no fixed share.
2. Claude takes innovative tasks and global tasks (architecture, interfaces, integration, cross-family review).
3. Choices: ordinary ones go to Opus (`claude-opus-5-5`, medium). Hard and critical ones go to Fable (`claude-fable-5-2`, high), with a reason in the package. Sonnet is optional.
4. Prefer remote Codex: run the task on the node with its own Codex login (`remote_codex.sh`). The controller only dispatches.
5. The controller does not execute tasks or watch them. It submits, then sleeps. A monitor script runs outside the session, and when the sub agent ends it wakes the controller with one terminal event. No polling loops, no SSH loops in a Claude session.
   - How to wait (2026-11-23 fix): start `tools/dispatch/wait_done.sh --pid PID` (or `--file DONE_MARKER`, or `--grep LOG 'exit='`) with `run_in_background`, one per job, then end your turn. Its exit is the wake event. Never wait with `pgrep -f <pattern>`: the pattern also matches the long-lived shell that launched the job (its command line holds the same text), so the wait never ends and the controller sleeps forever. Give every job a done marker (`.err` with `exit=`, or a manifest file) or a PID, and always set `--timeout`. After each wake, check state, do the next step, and wait again; if a job already ended, do not wait.
6. Quota is not a reason to choose an executor. The gateway allocates the account. With no usable Codex account, queue the job and let it wait.

Remote Codex is the default for remote or SSH work (UD-18 extension, 2026-11-14): `tools/dispatch/remote_codex.sh launch ALIAS TASK-ID --prompt-file FILE [--send DIR]`, then `status`, `logs`, `fetch`, `stop`. The task runs in `<root>/codex-tasks/<TASK-ID>/` on the node, detached, with a timeout (default 2 h), and returns evidence with `fetch` to `<workspace>/remote-codex/<alias>/<TASK-ID>/`. It uses the Codex account that is logged in on the node, so the gateway account rules do not apply. Put the scope, allowed paths, and the return block rule in the prompt. A remote agent does not write outside its task directory unless the prompt names the path. A node can have its own Codex CLI (paths in `config/platforms.json`, key `codex_path`). Update it before first use. It runs commands on the login node only; heavy work goes to jobs.

## Accounts

- The gateway chooses the account (`<gateway>/config/accounts.json`, `<gateway>/bin/select_account.py`). Do not keep a second account rule in the repository.
- Do not pass `--account` and do not pin an account. Pin one only when the user names it for one task, and write that in the package.
- Rule of the selector: an account is usable if every gating window has more than 2% left and it is not excluded. The usable account whose weekly window resets first wins. A tie goes to the configured order. No usable account gives `BLOCKED`: report it, and use no unlisted account.
- If a run reaches an account limit, the gateway switches the account and continues in the same worktree. Do not restart such a task by hand.
- Quota is live data. Read it when you need it (`codex.sh --probe`, `cswap list`). Never copy quota numbers into documents.
- The controller account is not fixed. The controller can switch accounts.

## Concurrency

> Project override (user, 2026-11-23): limit is 5 code agents; no review step (see workflow.md).

- Set one limit for the number of code agents that run at the same time (default 4). The limit follows the review capacity of the controller, not the number of accounts.
- Memory is the second limit. Every heavy check runs under `mem_guard.sh` ([local-host.md](local-host.md)).
- A dispatch scheduler (optional) waits for quota, keeps the agent limit, and continues a run after a usage limit. The controller acts only on its terminal events. See [workflow.md](workflow.md#dispatch).

## Profiles

Fill the tables at project setup with the newest models that the CLI offers. Use no older model unless the user names it.

| Level | Codex profile | Model | Effort | Use |
|---|---|---|---|---|
| 1 | `low` | `<model-a>` | low | Mechanical changes, small fixes with a known cause |
| 2 | `medium-low` | `<model-a>` | high | Small work with a clear contract |
| 3 | `medium` | `<model-b>` | low | Default: usual cross-file work |
| 4-5 | `high` | `<model-b>` | max | Costly. Code reviews, or other use with a written reason |

| Claude profile | Model | Effort | Use |
|---|---|---|---|
| `c-choice` | `claude-opus-5-5` | medium | Innovative or global task, ordinary choice and judgment, cross-family review of Codex work |
| `c-deep` | `claude-opus-5-5` | high | Core invariants, recovery, races (a reason in the package) |
| `c-critical` | `claude-fable-5-2` | high | Hard and critical choice or judgment; decisions that change the main line (a reason in the package) |
| `c-standard` | `claude-sonnet-5-5` | medium | Optional: documents that need Claude style or local context |
| Controller | `claude-opus-5-5` | medium | Dispatch, review, integration |

- Use the default level unless the package names another level. The controller names the level of each review in the review prompt.
- The dispatcher does not check model or effort. Example: `tools/dispatch/codex.sh TASK-001 <model-b> low`.

## Escalation

1. If two real fix attempts fail, write the smallest counterexample, the logs, and the excluded causes into the package. Then go up one profile. Reaching a costly level is the choice of the controller, with a written reason.
2. A missing dependency, a busy GPU, a network failure, a missing permission, or an empty quota is not a reasoning failure. Do not change the model for it.
3. After the cause is known, go back to a lower profile for mechanical work.

## Records and cost

- The package and the return block record the executor, the account, the requested model, the actual model ID, and the effort. Codex: the model ID is in the `.jsonl` log. Claude: it is `model_ids=` in `<TASK-ID>.err`.
- The controller gives the number of attempts. For a long task it also gives time and turn limits. An agent does not raise its own budget.
- An agent does not poll remote logs. Do not print credentials. Do not change global defaults of a node or an account.

## Executor limits (known)

- The Codex sandbox cannot write `.git`. The controller commits after the review.
- The Codex sandbox cannot write `/var/tmp`. Give a scratch directory under `/tmp/codex-<TASK-ID>-<n>`.
- In the Codex sandbox, use `ssh -F ~/.ssh/config <alias>`. Tests that open sockets need network access (`NET=1`).
- Codex runs pytest only with a memory cap. The adapters wrap the scope and tell the agent.
- Claude dispatch accepts one command per Bash call. It rejects `cd ... &&` chains and `VAR=value` prefixes. Write the package checks in that form.
- A Codex prompt over 128 KiB fails (exit 126). Send a header and the current ruling, and point to the package file.
- A Claude agent that has no scope is stopped by its process group, found with `/proc/<pid>/cwd`.
- Never use `kill $(pgrep -f "<text>")` in one call. The pattern also matches the shell that runs it. Use the `[x]yz` bracket form, and kill by explicit PID.
