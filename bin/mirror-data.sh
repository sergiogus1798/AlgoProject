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
# After the copy the mirror gets the manual's sources, refreshes its own M1 bar library
# (sqx.export.sync_bars through bin/remote.sh: it decodes the .dat the copy just brought) and rescans its feeds' quality, so its studies
# read what its SQX reads and step 4 finds every feed scanned.
#
# Refuses too when the source holds more than 5 % fewer files than at the last good copy: an
# `rsync --delete` from a half-emptied data folder would empty the mirror the same way. Each mirror
# gets `logs/MIRROR_OK.<name>` here: «copying <date>» while its copy runs, «ok <date>» once it is
# whole; bin/remote.sh refuses a workflow on a mirror whose last copy did not end (encargo 76 E).
# A shrink that is meant (feeds removed on purpose) passes with --accept-shrink, once: the count
# of that good copy becomes the new reference.
#
# Called by bin/weekly-data-update.sh after a successful update; by hand after adding a feed.
#
# Usage:
#   mirror-data            copy to every mirror
#   mirror-data --dry-run  say what would be copied, copy nothing
#   mirror-data --accept-shrink   copy even if the source holds over 5 % fewer files than last time
# Exit 0: every mirror holds this machine's data. Non-zero: at least one does not; the reason is
# printed and, from cron, raised as an alert by the caller.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
DRY=(); SHRINK=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=(--dry-run --itemize-changes) ;;
    --accept-shrink) SHRINK=1 ;;
    *) sed -n '2,30p' "$0"; exit 2 ;;
  esac
done

# one line per mirror: <name> <ssh host> <master folder on it>, then this machine's master
_CFG=$(python3 -c '
from core.paths import DATA, MANUAL_SRC, MASTER, MIRRORS
from core.worker import holding
print(MASTER)
print(*holding(MASTER))
print(MANUAL_SRC)
print(DATA)
for name, m in MIRRORS.items():
    print(name, m["ssh"], m["master"])') || { echo "mirror-data: cannot read the paths"; exit 1; }
mapfile -t _CFG <<< "$_CFG"
MASTER="${_CFG[0]}"; HELD="${_CFG[1]}"; MANUAL="${_CFG[2]}"; DATA="${_CFG[3]}"
[ "${#_CFG[@]}" -gt 4 ] || { echo "mirror-data: no mirrors in machine.yaml; nothing to do"; exit 0; }
[ -z "$HELD" ] || { echo "mirror-data: the master here is running (PID $HELD); nothing copied"; exit 1; }

exec 8>"/tmp/.mirror-data-$(id -u).lock"
flock -n 8 || { echo "mirror-data: another copy is running; nothing done"; exit 1; }

COUNT=$(find "$MASTER/user/data" -type f | wc -l)
LAST=$(cat "$DATA/logs/mirror-data.count" 2>/dev/null || echo 0)
[ "$SHRINK" = 1 ] || [ $((COUNT * 100)) -ge $((LAST * 95)) ] || {
  echo "mirror-data: the source holds $COUNT files, the last good copy $LAST (over 5 % fewer); nothing copied — rerun with --accept-shrink if the files were removed on purpose"; exit 1; }

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30)
rc=0
for line in "${_CFG[@]:4}"; do
  read -r name host dest <<< "$line"
  # -x matches the process name itself, so this never sees its own command line (hard rule 2)
  busy=$("${SSH[@]}" "$host" 'pgrep -u "$USER" -x "sqcli|StrategyQuantX" | tr "\n" " "') \
    || { echo "mirror-data: $name ($host) does not answer; not copied"; rc=1; continue; }
  [ -z "$busy" ] || { echo "mirror-data: SQX is running on $name (PID $busy); not copied"; rc=1; continue; }
  echo "--- $(date -Is) $name: $MASTER/user/data/ -> $host:$dest/user/data/"
  OK="$DATA/logs/MIRROR_OK.$name"
  [ "${#DRY[@]}" -gt 0 ] || echo "copying $(date -Is)" > "$OK"
  rsync -a --delete --partial --info=stats1 "${DRY[@]}" -e "${SSH[*]}" \
    "$MASTER/user/data/" "$host:$dest/user/data/" \
    || { echo "mirror-data: the copy to $name failed"; rc=1; continue; }
  # The data is only half of it: the studies read the M1 bar library, exported from that data,
  # and checks.py reads the manual's sources. A mirror with fresh data and last week's library
  # refused its first workflow at step 4 (📓 gorilla, 2026-10-11: 27 feeds behind).
  if [ "${#DRY[@]}" -eq 0 ]; then
    rsync -a --delete -e "${SSH[*]}" "$MANUAL/" "$host:Desktop/AlgoData/manual-fuentes/" \
      || { echo "mirror-data: the manual's sources did not reach $name"; rc=1; }
    bin/remote.sh "$name" python3 -m sqx.export.sync_bars \
      || { echo "mirror-data: the bar library on $name is behind its data"; rc=1; continue; }
    # And the scan step 4 asks for: a feed never scanned there is refused by the plan.
    bin/remote.sh "$name" python3 -m studies.data.feedQuality.scan >/dev/null \
      || { echo "mirror-data: the feed-quality scan failed on $name"; rc=1; continue; }
  fi
  [ "${#DRY[@]}" -gt 0 ] || echo "ok $(date -Is)" > "$OK"
  echo "--- $(date -Is) $name: done"
done
[ "$rc" -ne 0 ] || [ "${#DRY[@]}" -gt 0 ] || echo "$COUNT" > "$DATA/logs/mirror-data.count"
exit $rc
