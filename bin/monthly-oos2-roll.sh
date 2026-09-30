#!/bin/bash
# monthly-oos2-roll — on the month's first Saturday, move every decided oos2 in
# assets/_policy.yaml to end on the last day of the previous month (owner, 2026-09-30).
#
# Cron fires it every Saturday; it does nothing past the 7th. It waits for the Saturday data
# update (bin/weekly-data-update.sh) to finish, since that is what refreshes each asset's
# `data:` line, and then python3 -m sqx.data.roll_oos2 --apply moves only the assets whose
# data already reaches the new end — the rest are named in the log and the exit is 1.
# No model involved. Leaves _policy.yaml uncommitted.
#
# Usage:
#   monthly-oos2-roll          run it (still a no-op past the 7th)
#   monthly-oos2-roll --now    skip the first-Saturday check, for a run by hand
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
[ "${1:-}" = "--now" ] || [ "$(date +%-d)" -le 7 ] || exit 0

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)') || exit 1
exec >>"$DATA/logs/monthly-oos2-roll.log" 2>&1
echo "=== $(date -Is) oos2 roll start"

exec 8>"$DATA/logs/.weekly-data-update.lock"
flock -w 10800 8 || { echo "--- data update still running after 3 h; skipped"; exit 1; }
flock -u 8

python3 -m sqx.data.roll_oos2 --apply
rc=$?
echo "=== $(date -Is) oos2 roll end, exit $rc"
exit $rc
