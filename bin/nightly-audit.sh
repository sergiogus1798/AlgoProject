#!/bin/bash
# nightly-audit — the daily audit, unattended, from cron.
#
# Two halves, in order: the mechanical script (tools/daily_audit.py, no model) and then
# the `auditor` agent headless, which reads the mechanical report and spends its effort
# on what a script cannot see. Both write into audit/; the run's own log goes to the
# data root.
#
# Local cron, not a cloud routine: the auditor reads SQX's logs and ~/Desktop/AlgoData,
# which exist only on this machine. The auditor is read-only by its own definition — it
# never starts, stops or reconfigures SQX — so this never touches a worker.
#
# The only `claude` on this machine ships inside the VS Code extension, under a folder
# named by version that changes on every update. So the newest one is picked each run.
#
# Usage:
#   nightly-audit            run both halves
#   nightly-audit --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

# core/paths.py is the only place that knows where things live. Headless, the workspace's
# own additionalDirectories are ignored, so the data root and every install are passed
# to the agent with --add-dir, or it could not read the logs it audits.
_WHERE=$(python3 -c '
from core.paths import DATA, MASTER, WORKERS
print(DATA)
print(MASTER)
for w in WORKERS.values():
    print(w["path"])' 2>&1) || {
  printf 'cannot resolve the paths:\n  %s\n' "$_WHERE"; exit 1; }
mapfile -t _WHERE <<< "$_WHERE"
DATA="${_WHERE[0]}"
ADD_DIRS=()
for d in "${_WHERE[@]}"; do ADD_DIRS+=(--add-dir "$d"); done
LOG="$DATA/logs/nightly-audit.log"
LOCK="$DATA/logs/.nightly-audit.lock"

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nlog    %s\nclaude %s\nreads  %s\n' "$ROOT" "$LOG" "${CLAUDE:-NOT FOUND}" "${_WHERE[*]}"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another nightly audit is running; skipped"; exit 0; }

echo "=== $(date -Is) nightly audit start"

python3 tools/daily_audit.py
echo "--- mechanical half exit $?"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; agent half skipped"; exit 1
fi

TODAY=$(date +%F)
timeout 2h "$CLAUDE" -p --agent auditor --model sonnet \
  --permission-mode acceptEdits "${ADD_DIRS[@]}" \
  --allowedTools "Bash Read Grep Glob Write Edit" \
  "Run the full daily audit (all four areas). Read audit/${TODAY}-mechanical.md first, and the data root's size from the last \
perf.disk.report run in the data root's logs/disk-nightly.log. \
Write audit/${TODAY}.md. This run is unattended from cron: ask nothing, change nothing \
outside your report and OPEN.md."
echo "=== $(date -Is) nightly audit end, agent exit $?"
