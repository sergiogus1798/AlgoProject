#!/bin/bash
# weekly-docs-health — the documenter agent, unattended from cron, on everything in docs/ and
# OPEN.md that ages the way knowhow/ does but that bin/weekly-knowhow-review.sh does not cover.
#
# Four things, in one pass because they are all the documenter's own territory and often touch
# the same files:
#   - OPEN.md: an issue marked closed (✅/🟢) whose body no longer matches what is on disk, or
#     the top status table drifted from the issues below it.
#   - docs/SKILLS.md (tools/skillmap.py's own output): skills nobody has used in a long time, or
#     that overlap another skill enough to be a retirement candidate — reported, never deleted.
#   - docs/encargos/: this folder's own rule is "un encargo cumplido se borra" (README.md) — an
#     encargo whose described work is already verifiably in the repo gets deleted, one by one,
#     the way encargos 1-4, 7 and 19 already were; one still open is left alone.
#   - a general pass for a doc whose command, path or claim no longer matches the code, beyond
#     what nightly-docs.sh already repairs from the daily audit.
#
# Starts at the same time as the knowhow review but waits for its lock, so the two never fight
# over OPEN.md at once. Writes documentation only — no code, no SQX, no data root, no git — and
# leaves its changes uncommitted, so `git diff` on Monday shows exactly what it did.
#
# Usage:
#   weekly-docs-health            run it
#   weekly-docs-health --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/weekly-docs-health.log"
LOCK="$DATA/logs/.weekly-docs-health.lock"
KNOWHOW_LOCK="$DATA/logs/.weekly-knowhow-review.lock"

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
flock -n 9 || { echo "$(date -Is) another weekly docs health run is going; skipped"; exit 0; }

echo "=== $(date -Is) weekly docs health start"
exec 8>"$KNOWHOW_LOCK"
flock -w 7200 8 || { echo "--- knowhow review still running after 2 h; skipped"; exit 1; }
flock -u 8
echo "--- knowhow review lock free at $(date -Is)"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

timeout 2h "$CLAUDE" -p --agent documenter --model sonnet \
  --permission-mode acceptEdits --add-dir "$DATA" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Weekly docs-health pass, unattended from cron: nobody can answer, so never ask — decide, and \
leave in OPEN.md what you could not resolve. Four checks, in this order: \
(1) OPEN.md — read the status table near the top against every issue's own heading below it; fix \
any mismatch. For each issue marked closed (✅ or 🟢), spot-check its central claim still holds \
(a file it names still exists with the shape it describes, a schedule it claims still runs). Do \
not invent a new archiving scheme for closed issues — OPEN.md's own convention is to keep them \
inline with their status emoji; only fix what is actually wrong. \
(2) docs/SKILLS.md — run python3 tools/skillmap.py to refresh it, then read it for a skill nobody \
has used in a long time or that duplicates another closely enough to be a retirement candidate. \
Never delete a skill yourself: list the candidates and your reasoning as a new OPEN.md issue, \
owner decides. \
(3) docs/encargos/ — read docs/encargos/README.md for the rule ('un encargo cumplido se borra') \
and check every remaining file against the actual repository: code, knowhow/, the manual. Delete \
only an encargo whose described work you can point at, already done, in the repo — the way \
encargos 1, 2, 3, 4, 7 and 19 were already removed (see README.md's own log of that). Leave alone \
anything genuinely still open, and anything you are not sure is done. \
(4) a general pass: pick up where nightly-docs.sh's daily runs leave off — a path, command or \
claim in a README, a CLAUDE.md or a manual chapter in AlgoData/manual-fuentes/ that no longer matches the code, that a whole \
week of daily passes has not yet caught because nobody's audit finding pointed at it. \
When done run python3 tools/checks.py and fix anything you broke. Documentation only: never edit \
code, never write under the data root, never run git add, commit, checkout, stash or reset — \
leave your changes uncommitted. Finish with the list of files you changed or encargos you deleted, \
and why, in Spanish."
echo "=== $(date -Is) weekly docs health end, exit $?"
