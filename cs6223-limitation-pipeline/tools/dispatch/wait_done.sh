#!/usr/bin/env bash
# Wait for a job to end, then exit once. Start it with run_in_background: its exit wakes the controller.
# usage: tools/dispatch/wait_done.sh [--timeout SEC] (--pid PID | --file PATH | --grep PATH PATTERN)
#   --pid PID           wait until /proc/PID is gone (explicit PID, never a pgrep -f pattern)
#   --file PATH         wait until PATH exists (a done marker, e.g. run_manifest.json)
#   --grep PATH PAT     wait until PATH exists and contains the fixed string PAT (e.g. logs/LS-01.err "exit=")
# Exit: 0 done, 124 timeout. Prints one line with the reason.
set -u
timeout=10800; mode=""; a=""; b=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout) timeout="$2"; shift 2;;
    --pid) mode=pid; a="$2"; shift 2;;
    --file) mode=file; a="$2"; shift 2;;
    --grep) mode=grep; a="$2"; b="$3"; shift 3;;
    *) echo "bad arg $1" >&2; exit 2;;
  esac
done
[[ -n "$mode" ]] || { echo "need --pid, --file or --grep" >&2; exit 2; }
end=$((SECONDS+timeout))
while (( SECONDS < end )); do
  case "$mode" in
    pid)  [[ -d /proc/$a ]] || { echo "done: pid $a ended"; exit 0; };;
    file) [[ -e "$a" ]] || true; [[ -e "$a" ]] && { echo "done: $a exists"; exit 0; };;
    grep) [[ -f "$a" ]] && grep -qF -- "$b" "$a" && { echo "done: $a has '$b'"; exit 0; };;
  esac
  sleep 10
done
echo "timeout after ${timeout}s"; exit 124
