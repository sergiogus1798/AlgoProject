#!/bin/bash
# sqx-worker — drive the SQX worker with bars that are never stale.
#
# The three H2 files hold the bars a backtest actually consumes. They cannot be
# shared (H2 takes an exclusive lock), so each install needs its own copy — and
# a copy can only be written while the worker is stopped.
#
# The trick: sync on START, not after a data update. The worker is stopped by
# definition at that moment, so the copy is always safe and always current.
# You never have to remember anything.
#
# Usage:
#   sqx-worker start          sync bars, then run the worker (HTTP API on 5060)
#   sqx-worker stop           shut the worker down cleanly
#   sqx-worker check          report bar freshness; changes nothing
#   sqx-worker sync           sync bars only
#   sqx-worker run <args>     sync, then one-shot sqcli command, e.g.
#                               sqx-worker run -project action=list
set -uo pipefail

MASTER="/home/sergioguslw/Desktop/SQX"
WORKER="/home/sergioguslw/Desktop/SQX_w1"
CLI_PORT=5060
LOG="$WORKER/user/log/worker-daemon.log"
BARS=(data.db data_futures.h2.db data_stock.h2.db)

running() { ss -ltn 2>/dev/null | grep -q ":${CLI_PORT} "; }
fingerprint() { md5sum "$MASTER"/user/data/*.db "$MASTER"/user/data/*.version 2>/dev/null | md5sum; }

check() {
  # Compare the .version markers, NOT the .db files. H2 rewrites a database's
  # header every time it is opened, so the worker's .db diverges byte-wise the
  # first time it runs even though the bars are identical. The .version files
  # are SQX's own data-version stamps (format: YYYYMMDDHHmm) and only change
  # when the data actually changes.
  local stale=0 m w name
  echo "data version: master -> worker"
  for vf in "$MASTER"/user/data/*.version; do
    name=$(basename "$vf")
    m=$(cat "$vf" 2>/dev/null)
    w=$(cat "$WORKER/user/data/$name" 2>/dev/null)
    if [ -z "$w" ]; then printf '  MISSING  %-26s\n' "$name"; stale=1
    elif [ "$m" = "$w" ]; then printf '  ok       %-26s %s\n' "$name" "$m"
    else printf '  STALE    %-26s worker %s < master %s\n' "$name" "$w" "$m"; stale=1
    fi
  done
  # data.db carries no .version stamp; size is the only cheap signal.
  m=$(stat -c%s "$MASTER/user/data/data.db" 2>/dev/null)
  w=$(stat -c%s "$WORKER/user/data/data.db" 2>/dev/null)
  [ "$m" = "$w" ] && printf '  ok       %-26s %s bytes\n' "data.db (size)" "$m" \
                  || { printf '  DIFFERS  %-26s worker %s vs master %s\n' "data.db (size)" "$w" "$m"; stale=1; }
  return $stale
}

sync_bars() {
  if running; then
    echo "worker is running on :$CLI_PORT — stop it first (sqx-worker stop)"; return 1
  fi
  # The master may be mid-import. Copy, then confirm the source didn't move
  # underneath us; a torn H2 file silently truncates the backtest window.
  local before after
  for attempt in 1 2 3; do
    before=$(fingerprint)
    rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"
    after=$(fingerprint)
    if [ "$before" = "$after" ]; then
      echo "bars synced (attempt $attempt)"; return 0
    fi
    echo "master data changed mid-copy — retrying"
    sleep 2
  done
  echo "master data kept changing; is a Data Manager import running? Not synced."; return 1
}

case "${1:-}" in
  check) check && echo "worker bars are current" ;;
  sync)  sync_bars ;;
  stop)
    running || { echo "worker not running"; exit 0; }
    curl -sg -m 30 "http://localhost:${CLI_PORT}/call?cmd=-exit" >/dev/null 2>&1
    for _ in $(seq 1 20); do running || break; sleep 1; done
    running && echo "worker did not stop" || echo "worker stopped"
    ;;
  start)
    running && { echo "worker already running on :$CLI_PORT"; exit 0; }
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    env -u ELECTRON_RUN_AS_NODE setsid nohup ./sqcli >"$LOG" 2>&1 </dev/null &
    echo -n "starting"
    for _ in $(seq 1 60); do
      running && break; echo -n "."; sleep 2
    done
    echo
    if running; then
      echo "worker up:  http://localhost:${CLI_PORT}/call?cmd=-h"
      echo "log:        $LOG"
    else
      echo "worker failed to start — see $LOG"; exit 1
    fi
    ;;
  run)
    shift
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    env -u ELECTRON_RUN_AS_NODE ./sqcli "$@" 2>&1 | grep -vE "DEBUG|oshi|ResponseProcessCookies|set-cookie"
    ;;
  *)
    sed -n '2,20p' "$0" | sed 's/^# \?//'
    exit 1
    ;;
esac
