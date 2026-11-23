#!/usr/bin/env bash
# cs6223 adapter (template; cs6223 = project name) of the gateway Codex core (code-agent-gateway bin/codex_dispatch.sh).
# usage: tools/dispatch/codex.sh TASK-ID MODEL EFFORT [PROMPT_FILE [WORKTREE]] | --probe | --select-account
#   3 args: build the prompt from <WORKTREE>/development/tasks/<TASK-ID>.md
# Environment:
#   MEM=<size>      MemoryMax of the scope in the host memory slice prose.slice (shared by all projects of this host) around the run (default 3G; MEM=0: no scope)
#   NET=1           network access in the Codex sandbox (sockets, SSH, internet)
#   CODEX_ACCOUNT   account preference (needs a reason in the task package)
# Start it detached: setsid nohup tools/dispatch/codex.sh ... > /dev/null 2>&1 < /dev/null &
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
main_root="$(cd -- "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
workspace="$(dirname -- "$main_root")"
core="${CODE_AGENT_GATEWAY:-/home/somehow6/code-agent-gateway}/bin/codex_dispatch.sh"
export CODEX_DISPATCH_WORKTREE_ROOT="${CODEX_DISPATCH_WORKTREE_ROOT:-/home/somehow6/lesson/cs6223-wt}"
export CODEX_DISPATCH_LOG_DIR="${CODEX_DISPATCH_LOG_DIR:-/home/somehow6/lesson/cs6223-wt/logs}"
export CODEX_DISPATCH_NETWORK="${CODEX_DISPATCH_NETWORK:-${NET:-0}}"
MEM="${MEM:-3G}"
[[ $# != 1 ]] || exec "$core" "$@"
usage='usage: tools/dispatch/codex.sh TASK-ID MODEL EFFORT [PROMPT_FILE [WORKTREE]]'
[[ $# == 3 || $# == 4 || $# == 5 ]] || { echo "$usage" >&2; exit 2; }
T="$1"; M="$2"; E="$3"
[[ "$T" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || { echo 'Invalid task id' >&2; exit 2; }
WT="${5:-$CODEX_DISPATCH_WORKTREE_ROOT/$T/cs6223-limitation-pipeline}"  # repo root is the parent dir; project is a subdir
[[ -d "$WT" ]] || { echo "missing worktree $WT" >&2; exit 2; }
WT="$(cd -- "$WT" && pwd)"
mkdir -p "$CODEX_DISPATCH_LOG_DIR"

scope=()
if [[ "$MEM" != 0 ]]; then
  scope=(systemd-run --user --scope --quiet --slice=prose.slice -p "MemoryMax=$MEM" -p MemorySwapMax=0 --unit "codex-$T-$$")
fi

if [[ $# -ge 4 ]]; then
  exec "${scope[@]}" "$core" "$T" "$M" "$E" "$4" "$WT"
fi

PACK="development/tasks/$T.md"
[[ -f "$WT/$PACK" ]] || { echo "missing task package: $WT/$PACK" >&2; exit 2; }
if [[ "$MEM" != 0 ]]; then
  mem_rule="This whole process already runs in a memory scope (MemoryMax $MEM). Run checks directly. Do not call systemd-run or mem_guard.sh."
else
  mem_rule="No memory scope is active. Run only small targeted tests. Report the full checks as NOT_RUN."
fi
prompt_file="$(mktemp "${TMPDIR:-/tmp}/cs6223-codex.XXXXXXXX.md")"
trap 'rm -f -- "$prompt_file"' EXIT
cat > "$prompt_file" <<EOF
You are a Codex code agent for the cs6223 project. Your working directory is your task worktree: $WT (Git root).
1. Read AGENTS.md and follow it. Read only the files that your task package names.
2. Your task package is $PACK. Do exactly that scope. Change only its allowed_paths.
3. Run Python on this host only as 'conda run -n findlimit ...'. Do not install, upgrade, or remove packages in a shared environment. If a package is missing, report BLOCKED with its name. This rule covers the controller host only: on a remote node, follow the node rule of your task package (the node Conda prefix, or system python3 for stdlib-only tools such as gpu_vacancy.py).
4. $mem_rule
5. Use a scratch directory under /tmp/codex-$T-<n> (for example pytest --basetemp). The sandbox cannot write /var/tmp.
6. A test that starts a child process must give it an explicit environment. Do not rely on the environment of your shell.
7. Do not run git add, git commit, git checkout <sha>, merge, or rebase. The controller reviews and commits your working tree. Do not start other agents.
8. Before you finish: run 'git status' and 'git diff --check', run the checks of the package, and append the return block (docs/harness/workflow.md) to the package. This append is the only write that is allowed outside allowed_paths. Your final message repeats the return block.
EOF
if [[ "$CODEX_DISPATCH_NETWORK" == 1 ]]; then
  printf '%s\n' "9. Network access is on. For SSH, use 'ssh -F <HOME>/.ssh/config <alias>'. Do not install or upgrade shared packages." >> "$prompt_file"
fi
"${scope[@]}" "$core" "$T" "$M" "$E" "$prompt_file" "$WT"
