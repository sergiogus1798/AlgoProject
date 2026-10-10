#!/bin/bash
# mirror-data — copy the master's market data (user/data: History, data.db, the H2 files) to the
# master of every other server named under `mirrors:` in machine.yaml, so a workflow run there
# reads the same bars, instruments and sessions as here (owner, 2026-10-10: one dataset, kept
# updated from this machine; the other server never downloads data of its own).
#
# Refuses, copying nothing, when SQX is running at either end: H2 takes exclusive locks and a
# copy made under it is torn, and a workflow over there must not have its bars change mid-run.
# The remote workers pick the new data up by themselves: bin/sqx-worker.sh syncs on every start.
#
# Called by bin/weekly-data-update.sh after a successful update; by hand after adding a feed.
#
# Usage:
#   mirror-data            copy to every mirror
#   mirror-data --dry-run  say what would be copied, copy nothing
# Exit 0: every mirror holds this machine's data. Non-zero: at least one does not; the reason is
# printed and, from cron, raised as an alert by the caller.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
DRY=(); [ "${1:-}" = "--dry-run" ] && DRY=(--dry-run --itemize-changes)

# one line per mirror: <name> <ssh host> <master folder on it>, then this machine's master
_CFG=$(python3 -c '
from core.paths import MASTER, MIRRORS
from core.worker import holding
print(MASTER)
print(*holding(MASTER))
for name, m in MIRRORS.items():
    print(name, m["ssh"], m["master"])') || { echo "mirror-data: cannot read the paths"; exit 1; }
mapfile -t _CFG <<< "$_CFG"
MASTER="${_CFG[0]}"; HELD="${_CFG[1]}"
[ "${#_CFG[@]}" -gt 2 ] || { echo "mirror-data: no mirrors in machine.yaml; nothing to do"; exit 0; }
[ -z "$HELD" ] || { echo "mirror-data: the master here is running (PID $HELD); nothing copied"; exit 1; }

exec 8>"/tmp/.mirror-data-$(id -u).lock"
flock -n 8 || { echo "mirror-data: another copy is running; nothing done"; exit 1; }

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30)
rc=0
for line in "${_CFG[@]:2}"; do
  read -r name host dest <<< "$line"
  # -x matches the process name itself, so this never sees its own command line (hard rule 2)
  busy=$("${SSH[@]}" "$host" 'pgrep -u "$USER" -x "sqcli|StrategyQuantX" | tr "\n" " "') \
    || { echo "mirror-data: $name ($host) does not answer; not copied"; rc=1; continue; }
  [ -z "$busy" ] || { echo "mirror-data: SQX is running on $name (PID $busy); not copied"; rc=1; continue; }
  echo "--- $(date -Is) $name: $MASTER/user/data/ -> $host:$dest/user/data/"
  rsync -a --delete --partial --info=stats1 "${DRY[@]}" -e "${SSH[*]}" \
    "$MASTER/user/data/" "$host:$dest/user/data/" \
    || { echo "mirror-data: the copy to $name failed"; rc=1; continue; }
  echo "--- $(date -Is) $name: done"
done
exit $rc
