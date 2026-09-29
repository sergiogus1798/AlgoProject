#!/bin/bash
# daily-funding-deals — prop-firm offers, every day at 10:00, unattended from cron.
#
# Three stages (owner, 2026-09-29): the scan reads every place a firm shows offers and re-checks the
# known codes; the dealHunter agent looks for codes on the web and records them only through
# `deals.add`, which asks the firm itself; the notifier sends a desktop notification for each deal in
# the owner's universe (10k USD accounts where EAs are allowed) he has not heard of. The scan and the
# notifier run even when the agent cannot. See portfolio/funded/deals/README.md.
#
# Usage:
#   daily-funding-deals            run it
#   daily-funding-deals --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/daily-funding-deals.log"
LOCK="$DATA/logs/.daily-funding-deals.lock"
# cron has no session environment: notify-send needs the owner's session bus.
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nlog    %s\nclaude %s\nbus    %s\n' "$ROOT" "$LOG" "${CLAUDE:-NOT FOUND}" \
    "$DBUS_SESSION_BUS_ADDRESS"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another deals run is going; skipped"; exit 0; }

echo "=== $(date -Is) daily funding deals start"
python3 -m portfolio.funded.deals.scan
echo "--- scan above"

if [ -n "$CLAUDE" ] && [ -x "$CLAUDE" ]; then
  timeout 30m "$CLAUDE" -p --agent dealHunter --model sonnet --add-dir "$DATA" \
    --allowedTools=Bash,Read,Grep,Glob,WebFetch,WebSearch \
    "Daily prop-firm deal hunt, unattended from cron: nobody can answer, so never ask. Follow \
.claude/agents/dealHunter.md: search the web for current discount codes and sales of every active or \
candidate firm of AlgoData/funding/firms.yaml, record each candidate only through python3 -m portfolio.funded.deals.add, and end with a \
summary of at most ten lines. Never log in, buy or submit anything, never edit files, never touch git."
  echo "--- agent above, exit $?"
else
  echo "--- no claude binary found; web search skipped"
fi

python3 -m portfolio.funded.deals.notify
echo "=== $(date -Is) daily funding deals end"
