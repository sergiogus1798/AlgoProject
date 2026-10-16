#!/bin/bash
# weekly-reconcile — the weeklyReconciler, unattended from cron: the ISO week that just ended,
# the live accounts against the SQX backtest of the same strategies (OPEN.md #78).
#
# Crontab line (proposed): 10 2 * * 6 — Saturday 02:10, after bin/weekly-data-update.sh (02:00),
# whose lock this script waits for because the backtest needs the week's bars.
#
# What it does: python3 -m mt5.reconcile.run --week <this ISO week>. That command
#   - reads the live accounts through the MT5 terminal, READ-ONLY (it logs the terminal into
#     each account of `live.accounts`; nothing is ever sent);
#   - builds, runs and retires a Test_Reconcile_<asset>_<tf>_<week> project on the conductor,
#     started and stopped through core.worker (bin/sqx-worker.sh), and refuses if another
#     session has the conductor up;
#   - refuses, in Spanish, while an owner's key of mt5/reconcile/config.yaml is empty or the
#     register of live EAs is missing. Nothing is guessed.
# It writes AlgoData/mt5/reconcile/<week>/result.json. No model involved.
#
# Usage:
#   weekly-reconcile                 run it for the week today sits in
#   weekly-reconcile 2026-W38        run it for that week
#   weekly-reconcile --dry-run       resolve paths and the week, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
. "$ROOT/bin/lib-agent-alert.sh"

resolve_data
LOG="$DATA/logs/weekly-reconcile.log"
LOCK="$DATA/logs/.weekly-reconcile.lock"
WEEK="$(date +%G-W%V)"
case "${1:-}" in
  --dry-run) printf 'root %s\nweek %s\nlog  %s\n' "$ROOT" "$WEEK" "$LOG"; exit 0 ;;
  ????-W??)  WEEK="$1" ;;
esac

exec >>"$LOG" 2>&1
take_lock "$LOCK" "another reconciliation is running"
echo "=== $(date -Is) weekly reconcile start, week $WEEK"

# The data update of the same night must have finished: the backtest reads the week's bars.
exec 8>"$DATA/logs/.weekly-data-update.lock"
flock -w 10800 8 || { echo "--- data update still running after 3 h; skipped"; exit 1; }
flock -u 8

python3 -m mt5.reconcile.run --week "$WEEK"
rc=$?
echo "=== $(date -Is) weekly reconcile end, exit $rc"
exit $rc
