#!/bin/bash
# weekly-data-update — the GUI's "Update all" on the master, unattended, from cron.
#
# Order, and each step stops the next when it fails:
#   1. full copy of the master's user/projects into the data root (hard rule 1: the sqcli run
#      ends in a sync that deletes on-disk .sqx not held in memory; the command's own photo is
#      an inventory, not a copy). Only the last KEEP copies made by this script are kept.
#   2. python3 -m sqx.data.update --apply — refuses by itself, killing nothing, if the master's
#      GUI is up (hard rule 2), and refreshes assets/_policy.yaml when done.
#   3. names any day a feed refused with HTTP 429; the next run fetches it.
#   4. python3 -m core.commission --refresh — every confirmed broker's `pct_now` from the
#      close the update just brought in (owner, 2026-09-29). Runs even if step 2 found nothing
#      new; does not stop the script on failure, since it only affects step 26/weeklyReconciler.
#
# Cron: Saturday 02:00 (it was 03:00, the audit's minute). bin/monthly-oos2-roll.sh starts five
# minutes later and waits on this script's lock, so that order must hold.
#
# No model involved: nothing here needs judgement. First real run and its numbers: OPEN.md 30.
#
# Usage:
#   weekly-data-update            run it
#   weekly-data-update --dry-run  resolve paths, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
KEEP="${KEEP:-3}"

_WHERE=$(python3 -c '
from core.paths import DATA, MASTER
print(DATA)
print(MASTER)' 2>&1) || {
  printf 'cannot resolve the paths:\n  %s\n' "$_WHERE"; exit 1; }
mapfile -t _WHERE <<< "$_WHERE"
DATA="${_WHERE[0]}"
MASTER="${_WHERE[1]}"
LOG="$DATA/logs/weekly-data-update.log"
LOCK="$DATA/logs/.weekly-data-update.lock"
SNAPS="$DATA/snapshots"
PREFIX="weekly-data-update-"
SNAP="$SNAPS/$PREFIX$(date +%F)"

if [ "${1:-}" = "--dry-run" ]; then
  printf 'master %s\nsnap   %s (keeps %s)\nlog    %s\n' "$MASTER" "$SNAP" "$KEEP" "$LOG"
  exit 0
fi

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "$(date -Is) another data update is running; skipped"; exit 0; }
echo "=== $(date -Is) weekly data update start"

# The update refuses on its own with the GUI up, but checking first spares a 4 GB copy.
if pgrep -f "$MASTER/" >/dev/null; then
  echo "--- master SQX is running; nothing done"; exit 1
fi

mkdir -p "$SNAP"
rsync -a "$MASTER/user/projects/" "$SNAP/projects/" || { echo "--- snapshot failed; update not run"; exit 1; }
n_src=$(find "$MASTER/user/projects" -name '*.sqx' | wc -l)
n_dst=$(find "$SNAP/projects" -name '*.sqx' | wc -l)
echo "--- snapshot $SNAP: $n_dst of $n_src .sqx"
[ "$n_src" -eq "$n_dst" ] || { echo "--- snapshot incomplete; update not run"; exit 1; }

# Rotation touches only this script's own copies, never another snapshot.
ls -1d "$SNAPS/$PREFIX"* 2>/dev/null | sort | head -n -"$KEEP" | while read -r old; do
  echo "--- removing old snapshot $old"; rm -rf "$old"
done

OUT=$(mktemp)
python3 -m sqx.data.update --apply > "$OUT" 2>&1
rc=$?
# sqcli's DEBUG chatter is thousands of lines; keep what a reader needs.
grep -vE ' DEBUG |^WARNING: Invalid cookie|ResponseProcessCookies' "$OUT" \
  | grep -vE ', (Downloading|Writing) .*[0-9]+%$'
echo "--- update exit $rc"
fails=$(grep -c 'ERROR: download failed' "$OUT")
[ "$fails" -gt 0 ] && { echo "--- $fails day(s) refused by the feed:"; grep 'ERROR: download failed' "$OUT"; }
rm -f "$OUT"

echo "--- refreshing broker commission percentages"
python3 -m core.commission --refresh || echo "--- core.commission --refresh failed, continuing"

echo "=== $(date -Is) weekly data update end"
exit $rc
