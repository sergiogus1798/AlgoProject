#!/bin/bash
# nightly-fix — the fixer agent on Opus, unattended, from cron, last of the nightly chain.
#
#   03:00 audit  →  03:30 documenter  →  04:00 fixer
#
# Cron starts it at 04:00, but it first waits for the documenter's lock, which in turn waited for
# the audit's. It never works in the main checkout: it adds a git worktree on a new branch
# `fix/nocturno-YYYY-MM-DD` from whatever the main checkout has checked out (what the audit read),
# lets the agent commit one fix per finding there, and removes the worktree. The branch stays for
# the owner to review and merge; nothing is pushed. A night with no commit deletes its branch.
# The report is copied into the main checkout's audit/ so it is where the audit's is.
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
BRANCH="fix/nocturno-$TODAY"
WT="${TMPDIR:-/tmp}/algoproject-fix-$TODAY"

CLAUDE="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude \
             2>/dev/null | sort -V | tail -1)
fi

if [ "${1:-}" = "--dry-run" ]; then
  printf 'root   %s\nbranch %s from %s\nwt     %s\nlog    %s\nclaude %s\n' "$ROOT" "$BRANCH" \
    "$(git rev-parse --abbrev-ref HEAD)" "$WT" "$LOG" "${CLAUDE:-NOT FOUND}"
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
if git show-ref --quiet "refs/heads/$BRANCH"; then
  echo "--- branch $BRANCH already exists; not overwriting it"; exit 1
fi

BASE=$(git rev-parse --abbrev-ref HEAD)
BASE_SHA=$(git rev-parse HEAD)   # fixed now: another session may switch branch overnight
git worktree add -q -b "$BRANCH" "$WT" "$BASE_SHA" || { echo "--- worktree failed"; exit 1; }
echo "--- worktree $WT on $BRANCH from $BASE ${BASE_SHA:0:7}"

# What git does not carry: the machine's paths, the agent itself until it is committed, and
# today's audit reports, which may still be uncommitted in the main checkout.
cp config/machine.yaml "$WT/config/machine.yaml"
[ -f "$WT/.claude/agents/fixer.md" ] || cp .claude/agents/fixer.md "$WT/.claude/agents/fixer.md"
IN=$(mktemp -d)
cp "audit/$TODAY.md" "$IN/"
[ -f "audit/$TODAY-mechanical.md" ] && cp "audit/$TODAY-mechanical.md" "$IN/"

(cd "$WT" && timeout 3h "$CLAUDE" -p --agent fixer --model opus \
  --permission-mode acceptEdits --add-dir "$DATA" --add-dir "$IN" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Fix what today's audit found. The reports are in $IN. You are in a worktree on branch \
$BRANCH; commit there only. Unattended from cron: never ask. Write and commit \
audit/${TODAY}-fixes.md last.")
echo "--- agent exit $?"

n=$(git rev-list --count "$BASE_SHA..$BRANCH")
echo "--- $n commit(s) on $BRANCH:"
git log --oneline "$BASE_SHA..$BRANCH"
[ -f "$WT/audit/$TODAY-fixes.md" ] && cp "$WT/audit/$TODAY-fixes.md" "audit/$TODAY-fixes.md"

git worktree remove --force "$WT"
[ "$n" -eq 0 ] && { git branch -q -D "$BRANCH"; echo "--- nothing committed; branch removed"; }
rm -rf "$IN"
echo "=== $(date -Is) nightly fix end"
