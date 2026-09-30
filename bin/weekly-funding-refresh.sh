#!/bin/bash
# weekly-funding-refresh — the fundingWatcher agent, unattended from cron, Sunday 06:30.
#
# Re-reads the prop firms' sites into AlgoData/funding/funding.sqlite (prices, plans, add-ons),
# then researches the curated rules in AlgoData/funding/rules/*.yaml that are unknown,
# unconfirmed, in conflict or older than four weeks (owner, 2026-09-29). Reads public pages only.
# Writes AlgoData/audit/YYYY-MM-DD-fondeo.md. See .claude/agents/fundingWatcher.md and
# portfolio/funded/catalog/README.md.
#
# Usage:
#   weekly-funding-refresh            run it
#   weekly-funding-refresh --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/weekly-funding-refresh.log"
LOCK="$DATA/logs/.weekly-funding-refresh.lock"

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
flock -n 9 || { echo "$(date -Is) another funding refresh is going; skipped"; exit 0; }

echo "=== $(date -Is) weekly funding refresh start"
# The scrape runs first on its own, so prices are updated even if the agent cannot start.
python3 -m portfolio.funded.catalog.refresh
echo "--- scrape above"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; rules not researched"; exit 1
fi

TODAY=$(date +%F)
timeout 1h "$CLAUDE" -p --agent fundingWatcher --model sonnet \
  --permission-mode acceptEdits --add-dir "$DATA" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit,WebFetch,WebSearch \
  "Weekly prop-firm catalogue check, unattended from cron: nobody can answer, so never ask. \
Follow .claude/agents/fundingWatcher.md step by step: run the refresh, research the rules that are \
unknown, unconfirmed, in conflict or older than 28 days on the firms' own pages, edit \
AlgoData/funding/rules/*.yaml, refresh again, and write $DATA/audit/${TODAY}-fondeo.md in Spanish. Read \
public pages only — never log in, buy or submit anything — and never touch git or Python."
echo "=== $(date -Is) weekly funding refresh end, exit $?"
