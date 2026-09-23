#!/bin/bash
# sqx-worker — drive a headless SQX worker with bars that are never stale.
#
# Which install it drives comes from config/machine.yaml, asked to core/paths.py.
# Nothing here knows where anything lives; --role picks one of the headless
# installs and defaults to the conductor, so every existing call is unchanged.
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
#   sqx-worker [--role ROLE] [--force-sync] start   sync bars if the master moved, then run
#   sqx-worker [--role ROLE] stop     shut the worker down cleanly
#   sqx-worker [--role ROLE] check    report bar freshness; changes nothing
#   sqx-worker [--role ROLE] sync     sync bars only
#   sqx-worker [--role ROLE] run <args>   sync, then one-shot sqcli command, e.g.
#                                           sqx-worker run -project action=list
#   ROLE is conductor (default) or custodian.
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ROLE=conductor
FORCE_SYNC=0
if [ "${1:-}" = "--role" ]; then ROLE="${2:?--role needs a role}"; shift 2; fi
# The data copy is skipped when the master has not moved, so a worker keeps the
# instruments it was given. --force-sync copies anyway.
if [ "${1:-}" = "--force-sync" ]; then FORCE_SYNC=1; shift; fi

# core/paths.py is the only place that knows where an install lives, so ask it
# instead of parsing YAML in bash. One line each, so a path with a space survives.
_WHERE=$(cd "$ROOT" && python3 -c '
import sys
from core.paths import MASTER, WORKERS
role = sys.argv[1]
if role not in WORKERS:
    sys.exit(f"machine.yaml defines no worker role {role!r}; it has: " + ", ".join(WORKERS))
print(MASTER); print(WORKERS[role]["path"]); print(WORKERS[role]["port"])' "$ROLE" 2>&1) || {
  printf 'cannot resolve worker role "%s":\n  %s\n' "$ROLE" "$_WHERE"; exit 1; }
mapfile -t _WHERE <<< "$_WHERE"
MASTER="${_WHERE[0]}"
WORKER="${_WHERE[1]}"
CLI_PORT="${_WHERE[2]}"
LOG="$WORKER/user/log/worker-daemon.log"
BARS=(data.db data_futures.h2.db data_stock.h2.db)

running() { ss -ltn 2>/dev/null | grep -q ":${CLI_PORT} "; }

# Does any sqcli already have this install open? `running` only watches the port, and a
# worker whose AppSettings drifted listens somewhere else -- so the port alone says "free"
# while the H2 database is locked, and the second launch is the one that does the damage.
holds_install() {
  local p
  for p in $(pgrep -x sqcli 2>/dev/null); do
    [ "$(readlink -f "/proc/$p/cwd" 2>/dev/null)" = "$(readlink -f "$WORKER")" ] && return 0
  done
  return 1
}

configured_port() {
  grep -oE '<AppWebServerPortSQUANT>[0-9]+' "$WORKER/internal/AppSettings.txt" 2>/dev/null \
    | grep -oE '[0-9]+'
}

# 🔬 2026-09-23: two sqcli started on SQX_w2 200 ms apart. The second could not take the H2
# lock, logged "Cannot load settings", fell back to the DEFAULTS -- 5050, the master's own
# port, with no SQEDITOR entry -- and ON EXIT wrote those defaults into AppSettings.txt.
# A transient collision permanently reconfigured the worker to impersonate the master.
# Both halves are guarded here because either one alone lets it happen again.
guard_launch() {
  local have
  have=$(configured_port)
  if [ "$have" != "$CLI_PORT" ]; then
    printf 'REFUSING: %s declares AppWebServerPortSQUANT=%s, but role %s must be %s.\n' \
      "$(basename "$WORKER")" "${have:-<missing>}" "$ROLE" "$CLI_PORT"
    printf 'Its port config drifted -- launching now would bind the wrong port.\n'
    printf 'Fix internal/AppSettings.txt to %s / %s, install stopped, then retry.\n' \
      "$CLI_PORT" "$((CLI_PORT + 1))"
    exit 1
  fi
  if holds_install; then
    printf 'REFUSING: another sqcli already holds %s.\n' "$WORKER"
    printf 'A second one cannot take the H2 lock and rewrites AppSettings.txt on the way out.\n'
    printf 'Stop it first, by PID, never by pattern.\n'
    exit 1
  fi
}
fingerprint() { md5sum "$MASTER"/user/data/*.db "$MASTER"/user/data/*.version 2>/dev/null | md5sum; }

check() {
  # Compare the .version markers, NOT the .db files. H2 rewrites a database's
  # header every time it is opened, so the worker's .db diverges byte-wise the
  # first time it runs even though the bars are identical. The .version files
  # are SQX's own data-version stamps (format: YYYYMMDDHHmm) and only change
  # when the data actually changes.
  local stale=0 m w name
  # sqcli restamps these two on every launch, with a value of its own that is newer than
  # the master's. They differ on a perfectly current worker, so they are reported and not
  # counted -- otherwise the exit code is 1 forever and stops meaning anything.
  # ⚠️ The price: a real futures/stock import on the master is not flagged here. It does
  # not matter, because `start` syncs unconditionally before every run.
  local restamped=" data_futures.version data_stock.version "
  echo "data version: master -> $ROLE"
  for vf in "$MASTER"/user/data/*.version; do
    name=$(basename "$vf")
    m=$(cat "$vf" 2>/dev/null)
    w=$(cat "$WORKER/user/data/$name" 2>/dev/null)
    if [ -z "$w" ]; then printf '  MISSING  %-26s\n' "$name"; stale=1
    elif [ "$m" = "$w" ]; then printf '  ok       %-26s %s\n' "$name" "$m"
    # Never write "worker < master": the restamped value is the NEWER of the two.
    elif [[ "$restamped" == *" $name "* ]]
    then printf '  restamp  %-26s worker %s vs master %s (sqcli stamps this one)\n' \
                "$name" "$w" "$m"
    else printf '  DIFFERS  %-26s worker %s vs master %s\n' "$name" "$w" "$m"; stale=1
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
  # rsync CREATES its destination, so without this a role whose install was never
  # cloned leaves a half-built folder behind — and clone-sqx-worker.sh then refuses
  # to clone, because "the worker already exists".
  if [ ! -x "$WORKER/sqcli" ]; then
    echo "no SQX install at $WORKER — clone it first: bin/clone-sqx-worker.sh $ROLE"; return 1
  fi
  if running; then
    echo "$ROLE is running on :$CLI_PORT — stop it first (sqx-worker --role $ROLE stop)"; return 1
  fi
  # The master may be mid-import. Copy, then confirm the source didn't move
  # underneath us; a torn H2 file silently truncates the backtest window.
  # 🔬 2026-09-23: this rsync copies the whole of user/data/, and SQX's INSTRUMENT
  # REGISTRY lives in data.db alongside the bars. So an unconditional sync silently
  # reverts every -instrument edit on every start -- an instrument added on the worker
  # was gone after one restart, and XAUUSD_Infinox was back to the master's spread.
  # Skipping the copy when the master has not moved is what lets a worker hold its own
  # costs; the marker records which master state the worker was last given.
  local before after marker
  marker="$WORKER/user/data/.synced-from-master"
  before=$(fingerprint)
  if [ "$FORCE_SYNC" != "1" ] && [ "$(cat "$marker" 2>/dev/null)" = "$before" ]; then
    echo "bars already current (master unchanged) — not copying, worker keeps its instruments"
    return 0
  fi
  for attempt in 1 2 3; do
    before=$(fingerprint)
    rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"
    after=$(fingerprint)
    if [ "$before" = "$after" ]; then
      printf '%s' "$after" >"$marker"
      echo "bars synced (attempt $attempt)"; return 0
    fi
    echo "master data changed mid-copy — retrying"
    sleep 2
  done
  echo "master data kept changing; is a Data Manager import running? Not synced."; return 1
}

case "${1:-}" in
  check) check && echo "$ROLE bars are current" ;;
  sync)  sync_bars ;;
  stop)
    running || { echo "$ROLE not running"; exit 0; }
    curl -sg -m 30 "http://localhost:${CLI_PORT}/call?cmd=-exit" >/dev/null 2>&1
    for _ in $(seq 1 20); do running || break; sleep 1; done
    running && echo "$ROLE did not stop" || echo "$ROLE stopped"
    # The worker just released its log. Quiescent install = safe moment to prune.
    "$ROOT/bin/sqx-log-prune.sh" --auto || true
    ;;
  start)
    running && { echo "$ROLE already running on :$CLI_PORT"; exit 0; }
    guard_launch
    # Nothing holds a log right now, and a start is about to write more of them.
    # --auto is rate-limited, so calling it on every start costs nothing.
    "$ROOT/bin/sqx-log-prune.sh" --auto || true
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    env -u ELECTRON_RUN_AS_NODE setsid nohup ./sqcli >"$LOG" 2>&1 </dev/null &
    echo -n "starting $ROLE"
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
    guard_launch
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    env -u ELECTRON_RUN_AS_NODE ./sqcli "$@" 2>&1 | grep -vE "DEBUG|oshi|ResponseProcessCookies|set-cookie"
    ;;
  *)
    sed -n '2,23p' "$0" | sed 's/^# \?//'
    exit 1
    ;;
esac
