#!/bin/bash
# nightly-sync — the /sync skill, unattended, from cron.
#
# Runs after the nightly audit, so the OPEN.md it touched goes up with everything else. The skill
# already refuses data, machine.yaml and secrets, runs the checks before committing and
# never force-pushes, merges or deletes. Unattended adds one rule: anything the skill
# would ask the owner about is left uncommitted and written to the log instead.
#
# Usage:
#   nightly-sync            run it
#   nightly-sync --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/nightly-sync.log"
LOCK="$DATA/logs/.nightly-sync.lock"

# gh lives in ~/.local/bin, which cron's PATH does not carry.
export PATH="$HOME/.local/bin:$PATH"

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nlog    %s\nclaude %s\n' "$ROOT" "$LOG" "${CLAUDE:-NOT FOUND}"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another nightly sync is running; skipped"; exit 0; }

echo "=== $(date -Is) nightly sync start"
if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

timeout 1h "$CLAUDE" -p --model sonnet \
  --permission-mode acceptEdits \
  --allowedTools "Bash Read Grep Glob Skill" \
  "Run the /sync skill. This run is unattended from cron and nobody can answer: wherever the \
skill says to ask or stop, do not commit that part, leave it as it is and name it in your final \
report. Never commit a half-finished change from another session. Report in Spanish."
echo "=== $(date -Is) nightly sync end, exit $?"
