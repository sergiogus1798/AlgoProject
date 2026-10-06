#!/bin/bash
# fleet-collect — pull the VPS's FleetBeacon files into AlgoData/fleet/, every minute from cron.
#
# python3 -m mt5.fleet.collect: scp the beacons' JSON, append a row to each account's minute history,
# fold the open positions into excursions.json, and every 5 minutes ask the VPS for its health
# (vps.json). Read-only on the VPS. A VPS that does not answer is NOT an error: the files stop
# changing and MetaTracker reads the silence.
#
# The one cron entry that shares a minute with others (owner, 2026-10-03: «cron cada minuto»): it takes
# no lock any other job waits on, and flock -n skips a run while the previous one is still going.
# Crontab line: * * * * * /home/sergioguslw/Desktop/AlgoProject/bin/fleet-collect.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
  printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
LOG="$DATA/logs/fleet-collect.log"
LOCK="$DATA/logs/.fleet-collect.lock"

exec >>"$LOG" 2>&1
exec 9>"$LOCK"
flock -n 9 || exit 0
python3 -m mt5.fleet.collect || {
  rc=$?; echo "$(date '+%Y-%m-%d %H:%M:%S') FAIL collect exit $rc"
  # A silent VPS exits 0: this is the collector itself crashing. One alert a day, not one a minute.
  if [ ! -e "$DATA/audit/ERROR-fleet-collect-$(date +%F).txt" ]; then
    . "$ROOT/bin/lib-agent-alert.sh"; agent_alert fleet-collect "mt5.fleet.collect exited $rc"
  fi
}
