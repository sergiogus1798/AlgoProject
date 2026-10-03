#!/bin/bash
# monthly-oos2-roll — move every decided oos2 in assets/_policy.yaml to end on the last day of
# the previous month (owner, 2026-09-30): on the month's first Saturday, and again on each later
# Saturday for the assets that Saturday left behind.
#
# Cron fires it every Saturday at 02:05, five minutes after the update takes its lock (02:00).
# It waits for the Saturday data update (bin/weekly-data-update.sh) to finish, since that is what
# refreshes each asset's `data:` line, and then python3 -m sqx.data.roll_oos2 --apply moves only
# the assets whose data already reaches the new end — the rest are named in the log, the exit is
# 1 and the owner is alerted. The unit is the asset: one stale feed never holds the others.
#
# Past the 7th it is the catch-up: the same command, the same end date (still the last day of
# the previous month), so it moves only what is still short of it, and three log lines when nothing is.
# Until 2026-10-03 it was a no-op past the 7th, and an asset whose feed was stale on the first
# Saturday (UKOIL: the update was refused, master up) waited a whole month for its window.
# No model involved. Leaves _policy.yaml uncommitted.
#
# Usage:
#   monthly-oos2-roll          run it
#   monthly-oos2-roll --now    the same; kept for the runs by hand that used to need it
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)') || exit 1
LOG="$DATA/logs/monthly-oos2-roll.log"
exec >>"$LOG" 2>&1
echo "=== $(date -Is) oos2 roll start"

exec 8>"$DATA/logs/.weekly-data-update.lock"
flock -w 10800 8 || { echo "--- data update still running after 3 h; skipped"; exit 1; }
flock -u 8

python3 -m sqx.data.roll_oos2 --apply
rc=$?
echo "=== $(date -Is) oos2 roll end, exit $rc"
# a failed roll (e.g. a feed whose data ends before the window) was silent for weeks: tell the owner
. "$ROOT/bin/lib-agent-alert.sh"
[ "$rc" -eq 0 ] || agent_alert monthly-oos2-roll "roll_oos2 exited $rc (see the last lines: a symbol's data does not reach the window?)"
exit $rc
