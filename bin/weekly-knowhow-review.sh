#!/bin/bash
# weekly-knowhow-review — the documenter agent, unattended from cron, auditing knowhow/ itself.
#
# The nightly documenter repairs drift the daily audit found; it does not read knowhow/ end to
# end looking for cards that are individually correct but collectively redundant, stale or
# contradictory. tools/checks.py already enforces the mechanical shape of every card (size,
# header, links, index freshness) — this pass is for what only reading the prose catches:
# two cards answering the same q:, a 🔬 claim a later card quietly overturned without bumping
# the older one's date:, a tag that undersells or oversells its evidence, a card that has grown
# into two facts and should split. Sundays, after the Saturday data update and clear of the daily
# audit/docs/fix chain. Writes documentation only — no code, no SQX, no data root, no git — and
# leaves its changes uncommitted, so `git diff` on Monday shows exactly what it did.
#
# Usage:
#   weekly-knowhow-review            run it
#   weekly-knowhow-review --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/weekly-knowhow-review.log"
LOCK="$DATA/logs/.weekly-knowhow-review.lock"

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
flock -n 9 || { echo "$(date -Is) another weekly knowhow review is going; skipped"; exit 0; }

echo "=== $(date -Is) weekly knowhow review start"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

timeout 2h "$CLAUDE" -p --agent documenter --model sonnet \
  --permission-mode acceptEdits --add-dir "$DATA" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Weekly knowhow quality pass, unattended from cron: nobody can answer, so never ask — decide, \
and leave in OPEN.md what you could not resolve. tools/checks.py already enforces the mechanical \
shape of every card (size, header, links, index freshness): run it first and do not re-litigate \
what it already passes. Your job is what only reading the prose catches. Read every card under \
knowhow/ domain by domain, against its own domain's INDEX.md, and for each domain: (1) two or more \
cards answering the same or overlapping q: — merge them into the one that survives, edit it in \
place, delete the other, never leave both; (2) a card whose tag oversells its evidence (🔬 \
claimed but the Evidence section only reads logs — that is 📓) or undersells it (🤔 called out as \
unconfirmed when the Evidence section already reproduces it directly — promote to 🔬); (3) a card \
a later one contradicts without saying so — rewrite the older card's rule to match what is true \
now and bump its date:, per CLAUDE.md's rule that a card is edited in place, never appended to; \
(4) a card that has drifted into answering two unrelated questions — split it, one q: each; (5) a \
'see:' cross-reference that points at a slug that no longer carries what it once did. Do not touch \
knowhow/INDEX.md's domain table or the CLAUDE.md router — those are the owner's structure, not \
yours to reorganise; only the per-domain INDEX.md files and the cards themselves. After any change \
run python3 tools/knowhowmap.py, then python3 tools/checks.py, and fix anything you broke. \
Documentation only: never edit code, never write under the data root, never run git add, commit, \
checkout, stash or reset — leave your changes uncommitted. Finish with the list of cards you \
merged, retagged, rewrote or split, and why, in Spanish."
echo "=== $(date -Is) weekly knowhow review end, exit $?"
