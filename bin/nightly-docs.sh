#!/bin/bash
# nightly-docs — the documenter agent, unattended, from cron, after the nightly audit.
#
# Cron starts it at 03:30, but it first waits for the audit's lock: both agents write OPEN.md,
# and an audit can outlast half an hour. So it starts at 03:30 or when the audit ends, whichever
# is later. It repairs documentation that drifted from the code, starting from what today's
# audit found. It writes documentation only — no code, no SQX, no data root, no git — and leaves
# its changes uncommitted, so `git diff` in the morning shows exactly what it did.
#
# Usage:
#   nightly-docs            run it
#   nightly-docs --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/nightly-docs.log"
LOCK="$DATA/logs/.nightly-docs.lock"
AUDIT_LOCK="$DATA/logs/.nightly-audit.lock"

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
flock -n 9 || { echo "$(date -Is) another nightly docs run is going; skipped"; exit 0; }

echo "=== $(date -Is) nightly docs start"
exec 8>"$AUDIT_LOCK"
flock -w 10800 8 || { echo "--- audit still running after 3 h; skipped"; exit 1; }
flock -u 8
echo "--- audit lock free at $(date -Is)"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

TODAY=$(date +%F)
timeout 2h "$CLAUDE" -p --agent documenter --model sonnet \
  --permission-mode acceptEdits --add-dir "$DATA" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Documentation drift pass, unattended from cron: nobody can answer, so never ask — decide, and \
leave in OPEN.md what you could not resolve. Start from today's audit ($DATA/audit/${TODAY}.md and \
$DATA/audit/${TODAY}-mechanical.md): repair every documentation finding in it, then check paths, \
commands and claims in CLAUDE.md files, READMEs, knowhow/ and the manual chapters in AlgoData/manual-fuentes/ against what is on disk. \
Documentation only: never edit code, never write under the data root, never run git add, commit, \
checkout, stash or reset — leave your changes uncommitted. When done run python3 tools/checks.py. \
Finish with the list of files you changed, in Spanish."
echo "=== $(date -Is) nightly docs end, exit $?"
