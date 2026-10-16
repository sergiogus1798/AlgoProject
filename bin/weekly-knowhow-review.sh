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
. "$ROOT/bin/lib-agent-alert.sh"

resolve_data
LOG="$DATA/logs/weekly-knowhow-review.log"
LOCK="$DATA/logs/.weekly-knowhow-review.lock"

resolve_claude

dry_run "${1:-}" 'root   %s\nlog    %s\nclaude %s\n' "$ROOT" "$LOG" "${CLAUDE:-NOT FOUND}"

exec >>"$LOG" 2>&1
take_lock "$LOCK" "another weekly knowhow review is going"

echo "=== $(date -Is) weekly knowhow review start"

if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

agent_run weekly-knowhow-review sonnet "" timeout 2h "$CLAUDE" -p --output-format json --agent documenter --model sonnet \
  --permission-mode acceptEdits --add-dir "$DATA" \
  --allowedTools=Bash,Read,Grep,Glob,Write,Edit \
  "Weekly knowhow quality pass, unattended from cron: nobody can answer, so never ask — decide, \
and leave in OPEN.md what you could not resolve. knowhow/ is ~300 cards in 16 domain folders: one \
pass cannot read them all, so work ONE DOMAIN AT A TIME. Step 0, before any reading: run \
python3 tools/checks.py and fix what its knowhow sections report (cards, links, header paths, \
indexes) — that is mechanical and a script already finds it; spend your reading only on judgment. \
Then loop over every folder under knowhow/ (ls knowhow; finish one before starting the next, and \
say which domain you are on). For each domain: (a) grep -h '^q:' knowhow/<domain>/ — that is the \
whole map of the domain (kw: lines hold the symptom keywords, grep them only to look a card up); (b) from the q: lines alone, list the suspected problems: two cards whose \
q: overlap, a card whose q: names two unrelated questions, a pair that sound contradictory; \
(c) read the HEADER only (sed '/^## Evidence/q' <card>) of the suspected cards, and the Evidence \
only of one whose tag you doubt. Never read a whole domain's cards. Judge: (1) two or more cards \
answering the same or overlapping q: — merge them into the one that survives, edit it in place, \
delete the other, never leave both; (2) a card whose tag oversells its evidence (🔬 claimed but \
the Evidence only reads logs — that is 📓) or undersells it (🤔 when the Evidence already \
reproduces it directly — promote to 🔬); (3) a card a later one contradicts without saying so — \
rewrite the older card's rule to match what is true now and bump its date:, per CLAUDE.md's rule \
that a card is edited in place, never appended to; (4) a card that has drifted into answering two \
unrelated questions — split it, one q: each; (5) a 'see:' that points at a slug that no longer \
carries what it once did; (6) a card filed in the wrong domain (a Qt fact in eng, an MT5 fact in \
sqx-drive) — say so in OPEN.md, do not move it. Do not touch knowhow/INDEX.md's domain table or \
the CLAUDE.md router — those are the owner's structure; only the per-domain INDEX.md files and the \
cards themselves. After each domain you changed run python3 tools/knowhowmap.py; at the end \
python3 tools/checks.py, and fix anything you broke. Documentation only: never edit code, never \
write under the data root, never run git add, commit, checkout, stash or reset — leave your \
changes uncommitted. Finish with one line per domain (cards read, cards changed) and the list of \
cards you merged, retagged, rewrote or split, and why, in Spanish."
echo "=== $(date -Is) weekly knowhow review end, exit $?"
