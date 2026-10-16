#!/bin/bash
# lib-agent-alert — sourced by every bin/ script that calls `claude -p` unattended (owner review,
# 2026-10-03). Two jobs that no script did before:
#   1. a failed agent run is no longer silent: when claude exits non-zero, says is_error, or the
#      report the agent had to write is missing or empty, write $DATA/audit/ERROR-<job>-<date>.txt
#      (reason + the last 20 log lines) and send a critical desktop notification — the same
#      mechanism as portfolio/funded/deals/notify.py (notify-send on the owner's session bus).
#   2. what the run spent is recorded: one row per call in $DATA/logs/agent-spend.csv,
#      date,job,model,input_tokens,output_tokens,duration_s,exit
#      (input_tokens = fresh + cache-creation + cache-read tokens; the plan is flat, tokens are the unit).
# Usage, after the script has set DATA, LOG and redirected its output to the log:
#   . "$ROOT/bin/lib-agent-alert.sh"
#   agent_run <job> <model> <report file or ""> timeout 2h "$CLAUDE" -p ... --output-format json "prompt"
# The command must carry `--output-format json` (its stdout is parsed, so only use it where the
# report is a file the agent writes, not claude's stdout). Returns claude's exit status; never exits.
# No `set -e` here on purpose: the calling scripts check exit codes by hand.

# cron has no session environment: notify-send needs the owner's session bus (as in daily-funding-deals).
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

agent_alert() {  # agent_alert <job> <reason>
  local job="$1" reason="$2" day file
  day=$(date +%F); file="$DATA/audit/ERROR-$job-$day.txt"
  mkdir -p "$DATA/audit"
  { printf '%s  %s  FAILED: %s\n\n--- last 20 lines of %s\n' "$(date -Is)" "$job" "$reason" "$LOG"
    tail -n 20 "$LOG" 2>/dev/null; } > "$file"
  echo "--- ALERT $job: $reason ($file)"
  notify-send --app-name=AlgoProject --urgency=critical "AlgoProject: $job failed" \
    "$reason
$file" 2>/dev/null || true
}

agent_run() {  # agent_run <job> <model> <report or ""> <command...>
  local job="$1" model="$2" report="$3" out start rc dur parsed reason=""
  shift 3
  out=$(mktemp); start=$(date +%s)
  "$@" > "$out"; rc=$?
  dur=$(( $(date +%s) - start ))
  parsed=$(python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print("0 0 1"); sys.exit()
u = d.get("usage") or {}
i = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
print(i, int(u.get("output_tokens") or 0), 1 if d.get("is_error") else 0)
print(str(d.get("result") or "").strip())
' "$out" 2>/dev/null)
  local itok otok iserr result
  read -r itok otok iserr <<< "$(head -n1 <<< "$parsed")"
  result=$(tail -n +2 <<< "$parsed")
  [ -s "$out" ] && { [ -n "$result" ] && printf '%s\n' "$result" || head -c 2000 "$out"; }
  rm -f "$out"
  local csv="$DATA/logs/agent-spend.csv"
  [ -s "$csv" ] || echo "date,job,model,input_tokens,output_tokens,duration_s,exit" > "$csv"
  echo "$(date -Is),$job,$model,${itok:-0},${otok:-0},$dur,$rc" >> "$csv"
  echo "--- agent exit $rc"
  [ "$rc" -ne 0 ] && reason="claude exited $rc after ${dur}s"
  [ -z "$reason" ] && [ "${iserr:-0}" = 1 ] && reason="claude reported is_error: ${result:0:200}"
  [ -z "$reason" ] && [ -n "$report" ] && [ ! -s "$report" ] && reason="report missing or empty: $report"
  [ -n "$reason" ] && agent_alert "$job" "$reason"
  return "$rc"
}

# --- boilerplate shared by the cron scripts (encargo 78, part D). Call them after `cd "$ROOT"`.
resolve_data() {  # sets DATA from core.paths, or prints why and exits 1
  DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
    printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
}

resolve_claude() {  # sets CLAUDE: $CLAUDE_BIN, else PATH, else the newest VS Code extension binary
  CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
  if [ -z "$CLAUDE" ]; then
    CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
               2>/dev/null | sort -V | tail -1)
  fi
}

dry_run() {  # dry_run "${1:-}" <printf format> [args...] — on --dry-run print and exit 0
  [ "$1" = "--dry-run" ] || return 0
  shift; printf "$@"; exit 0
}

take_lock() {  # take_lock <lockfile> <what is already running> — exit 0 when another run holds it
  exec 9>"$1"
  flock -n 9 || { echo "$(date -Is) $2; skipped"; exit 0; }
}
