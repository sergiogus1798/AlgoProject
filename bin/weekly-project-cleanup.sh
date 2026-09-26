#!/bin/bash
# weekly-project-cleanup — the projectJanitor agent, unattended from cron, Monday 03:00.
#
# Other sessions create custom SQX projects for one question and leave them on the workers
# (owner, 2026-09-26). This pass retires what the rule in sqx/projects/sweep.py names — Test_
# projects, projects of fewer than 10 tasks, and whatever the owner queued in
# AlgoData/projects/retire-queue.txt — archiving each project.cfx in AlgoData first. It never
# starts, stops or queries an install: a running one keeps its projects another week. Writes
# audit/YYYY-MM-DD-proyectos.md, uncommitted. See .claude/agents/projectJanitor.md and
# docs/manual/04-sqx-plantillas-y-proyectos.pdf (cap. 55-retirar-proyectos).
#
# Usage:
#   weekly-project-cleanup            run it
#   weekly-project-cleanup --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
mapfile -t INSTALLS < <(python3 -c '
from sqx.projects.retire import installs
for p in installs().values(): print(p)')
ADD_DIRS=(--add-dir "$DATA")
for d in "${INSTALLS[@]}"; do ADD_DIRS+=(--add-dir "$d"); done
LOG="$DATA/logs/weekly-project-cleanup.log"
LOCK="$DATA/logs/.weekly-project-cleanup.lock"

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nlog    %s\nclaude %s\ndirs   %s\n' "$ROOT" "$LOG" "${CLAUDE:-NOT FOUND}" \
    "${INSTALLS[*]}"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another project cleanup is going; skipped"; exit 0; }

echo "=== $(date -Is) weekly project cleanup start"
python3 -m sqx.projects.retire --sweep
echo "--- dry run above"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

TODAY=$(date +%F)
timeout 1h "$CLAUDE" -p --agent projectJanitor --model sonnet \
  --permission-mode acceptEdits "${ADD_DIRS[@]}" \
  --allowedTools=Bash,Read,Grep,Glob,Write \
  "Weekly SQX project cleanup, unattended from cron: nobody can answer, so never ask — when in \
doubt keep the project and say why. Follow .claude/agents/projectJanitor.md step by step: dry-run the \
sweep, hold back any candidate with a sign of life, retire the rest with sqx.projects.retire, \
dequeue what you retired from the queue, and write audit/${TODAY}-proyectos.md in Spanish. Never \
send any command to an SQX install and never touch git."
echo "=== $(date -Is) weekly project cleanup end, exit $?"
