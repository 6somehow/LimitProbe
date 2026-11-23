#!/usr/bin/env bash
# cs6223 adapter (template; cs6223 = project name) of the gateway Claude core (code-agent-gateway bin/claude_dispatch.sh).
# usage: tools/dispatch/claude.sh [--review] [--account auto|swl|yxy] TASK-ID MODEL EFFORT [PROMPT_FILE [WORKTREE]]
#   3 args: build the prompt from <WORKTREE>/development/tasks/<TASK-ID>.md
# Environment:
#   MEM=<size>   MemoryMax of the scope in the host memory slice prose.slice (shared by all projects of this host) around the run (default 3G; MEM=0: no scope)
# Start it detached: setsid nohup tools/dispatch/claude.sh ... > /dev/null 2>&1 < /dev/null &
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
main_root="$(cd -- "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
workspace="$(dirname -- "$main_root")"
core="${CODE_AGENT_GATEWAY:-/home/somehow6/code-agent-gateway}/bin/claude_dispatch.sh"
export CLAUDE_DISPATCH_WORKTREE_ROOT="${CLAUDE_DISPATCH_WORKTREE_ROOT:-/home/somehow6/lesson/cs6223-wt}"
export CLAUDE_DISPATCH_LOG_DIR="${CLAUDE_DISPATCH_LOG_DIR:-/home/somehow6/lesson/cs6223-wt/logs}"
export CLAUDE_DISPATCH_CONDA_ENV="${CLAUDE_DISPATCH_CONDA_ENV:-findlimit}"
MEM="${MEM:-3G}"
usage='usage: tools/dispatch/claude.sh [--review] [--account auto|swl|yxy] TASK-ID MODEL EFFORT [PROMPT_FILE [WORKTREE]]'
flags=(); mode=impl
while [[ ${1:-} == --* ]]; do
  case "$1" in
    --review) flags+=(--review); mode=review; shift ;;
    --account) [[ $# -ge 2 ]] || { echo "$usage" >&2; exit 2; }; flags+=(--account "$2"); shift 2 ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
done
[[ $# == 3 || $# == 4 || $# == 5 ]] || { echo "$usage" >&2; exit 2; }
T="$1"
[[ "$T" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || { echo 'Invalid task id' >&2; exit 2; }
WT="${5:-$CLAUDE_DISPATCH_WORKTREE_ROOT/$T}"
[[ -d "$WT" ]] || { echo "missing worktree $WT" >&2; exit 2; }
WT="$(cd -- "$WT" && pwd)"
mkdir -p "$CLAUDE_DISPATCH_LOG_DIR"

scope=()
if [[ "$MEM" != 0 ]]; then
  scope=(systemd-run --user --scope --quiet --slice=prose.slice -p "MemoryMax=$MEM" -p MemorySwapMax=0 --unit "claude-$T-$$")
fi

if [[ $# -ge 4 ]]; then
  exec "${scope[@]}" "$core" "${flags[@]}" "$1" "$2" "$3" "$4" "$WT"
fi

PACK="development/tasks/$T.md"
[[ -f "$WT/$PACK" ]] || { echo "missing task package: $WT/$PACK" >&2; exit 2; }
if [[ "$MEM" != 0 ]]; then
  mem_rule="This whole process already runs in a memory scope (MemoryMax $MEM). Run checks directly. Do not call systemd-run or mem_guard.sh."
else
  mem_rule="Run memory-heavy checks with /home/somehow6/code-agent-gateway/bin/mem_guard.sh run --max 3G -- <command>."
fi
shell_rule="Write one command per Bash call. Do not chain commands with 'cd ... &&'. Do not put 'VAR=value' before a command. The permission check rejects these forms."
prompt_file="$(mktemp "${TMPDIR:-/tmp}/cs6223-claude.XXXXXXXX.md")"
trap 'rm -f -- "$prompt_file"' EXIT
if [[ $mode == review ]]; then
  cat > "$prompt_file" <<EOF
You are an independent read-only reviewer for the cs6223 project. Your working directory is $WT (Git root).
1. Read AGENTS.md. Read the task package $PACK, including its return block, and only the files that it references.
2. Review the task branch against base_sha of the package: 'git diff <base_sha>' plus uncommitted changes. Check the scope against allowed_paths, the contracts and invariants, the failure paths, weakened tests or assertions, and claims without evidence. Check the documents against docs/harness/writing.md.
3. You can run the checks of the package with 'conda run -n findlimit ...'. Run a test that starts a child process once with an empty PYTHONPATH. Do not change any file.
4. $mem_rule
5. $shell_rule
6. Final message: VERDICT: ACCEPT | NEEDS_CHANGES | BLOCKED. Then FINDINGS by severity (high, medium, low) with file:line and a reproduction or the reasoning. Then CHECKS with PASS, FAIL, or NOT_RUN. Then RESIDUAL_RISKS.
EOF
else
  cat > "$prompt_file" <<EOF
You are a Claude code agent for the cs6223 project. Your working directory is your task worktree: $WT (Git root).
1. Read AGENTS.md and follow it. Read only the files that your task package names.
2. Your task package is $PACK. Do exactly that scope. Change only its allowed_paths.
3. Run Python only as 'conda run -n findlimit ...'. Do not install, upgrade, or remove packages in a shared environment. If a package is missing, report BLOCKED with its name.
4. $mem_rule
5. $shell_rule
6. A test that starts a child process must give it an explicit environment. Do not rely on the environment of your shell.
7. Do not run git add, git commit, merge, or rebase. The controller reviews and commits your working tree. Do not start other agents.
8. Before you finish: run 'git status' and 'git diff --check', run the checks of the package, and append the return block (docs/harness/workflow.md) to the package. This append is the only write that is allowed outside allowed_paths. Set COMMITS to 'pending controller commit'. Remove __pycache__ directories and other generated files outside ignored paths. Your final message repeats the return block.
EOF
fi
"${scope[@]}" "$core" "${flags[@]}" "$1" "$2" "$3" "$prompt_file" "$WT"
