#!/bin/bash
# nightly-fix — the fixer agent on Opus, unattended, from cron, last of the nightly chain.
#
#   03:00 audit  →  03:30 documenter  →  04:00 fixer
#
# Cron starts it at 04:00, but it first waits for the documenter's lock, which in turn waited for
# the audit's. It works in the one checkout, on the branch it has, like the documenter, and
# commits nothing: the owner reads `git diff` and audit/YYYY-MM-DD-fixes.md in the morning and
# commits what he wants (owner, 2026-09-26: one folder, no worktrees, no agent commits unasked).
#
# Usage:
#   nightly-fix            run it
#   nightly-fix --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/nightly-fix.log"
LOCK="$DATA/logs/.nightly-fix.lock"
DOCS_LOCK="$DATA/logs/.nightly-docs.lock"
TODAY=$(date +%F)

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nbranch %s\nlog    %s\nclaude %s\n' "$ROOT" \
    "$(git rev-parse --abbrev-ref HEAD)" "$LOG" "${CLAUDE:-NOT FOUND}"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another nightly fix is running; skipped"; exit 0; }

echo "=== $(date -Is) nightly fix start"
exec 8>"$DOCS_LOCK"
flock -w 14400 8 || { echo "--- documenter still running after 4 h; skipped"; exit 1; }
flock -u 8

if [ ! -f "audit/$TODAY.md" ]; then
  echo "--- no audit/$TODAY.md: the audit did not finish; nothing to fix"; exit 1
fi
if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi
echo "--- already modified before the fixer, not its to touch:"
git status --short

IN=$(mktemp -d)
cp "audit/$TODAY.md" "$IN/"
[ -f "audit/$TODAY-mechanical.md" ] && cp "audit/$TODAY-mechanical.md" "$IN/"

timeout 3h "$CLAUDE" -p --agent fixer --model opus \
  --permission-mode acceptEdits --add-dir "$DATA" --add-dir "$IN" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Fix what today's audit found. The reports are in $IN. Work in this checkout on the branch it \
has; never commit, stash, switch branch or create a worktree — leave every change uncommitted. \
Unattended from cron: never ask. Write audit/${TODAY}-fixes.md last."
echo "--- agent exit $?"
git status --short
rm -rf "$IN"
echo "=== $(date -Is) nightly fix end"
