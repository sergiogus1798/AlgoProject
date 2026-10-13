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
#   sqx-worker [--role ROLE] [--owner NAME] [--force-sync] start   sync bars, then run
#   sqx-worker [--role ROLE] [--force] stop     shut the worker down cleanly
#   sqx-worker [--role ROLE] check    report bar freshness and who holds the lock; changes nothing
#   sqx-worker [--role ROLE] sync     sync bars only
#   sqx-worker [--role ROLE] run <args>   sync, then one-shot sqcli command, e.g.
#                                           sqx-worker run -project action=list
#   ROLE is conductor (default) or custodian.
#   --gui (start only): run ./StrategyQuantX under a private Xvfb instead of sqcli, so the
#   GUI's own JSON servlets (/project/start runTask, /project/updateTaskXML) answer on the
#   port SQX writes to settings.xml (WebServerPortUsed), with the BrowserToken beside it.
#
# Every install carries an owner lock (OPEN.md #32): `start` writes user/log/OWNER
# (holder, sqcli PID, start time) the moment it launches; `stop` from a different holder
# refuses unless --force. The holder is $CLAUDE_CODE_SESSION_ID when set, else
# --owner/$SQX_OWNER, else "owner".
#
# Exit codes: 0 only when the command did what it says. `start` exits 1 when another start
# or run of the same install is in progress, or when the port never opened (the sqcli it
# launched is then killed, by PID). `stop` exits 1 when the worker is still alive at the end.
# "Alive" is the port OR a sqcli/StrategyQuantX process whose working directory is the
# install -- never the port alone. → knowhow/sqx-drive/worker-process-lifecycle.md
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ROLE=conductor
FORCE_SYNC=0
OWNER_ARG=""
FORCE_STOP=0
GUI=0
while true; do
  case "${1:-}" in
    --role) ROLE="${2:?--role needs a role}"; shift 2 ;;
    # The data copy is skipped when the master has not moved, so a worker keeps the
    # instruments it was given. --force-sync copies anyway.
    --force-sync) FORCE_SYNC=1; shift ;;
    --owner) OWNER_ARG="${2:?--owner needs a name}"; shift 2 ;;
    # stop only: override a different holder's lock.
    --force) FORCE_STOP=1; shift ;;
    --gui) GUI=1; shift ;;
    *) break ;;
  esac
done

# core/paths.py is the only place that knows where an install lives, so ask it
# instead of parsing YAML in bash. One line each, so a path with a space survives.
_WHERE=$(cd "$ROOT" && python3 -c '
import sys
from core.paths import MASTER, WORKERS
role = sys.argv[1]
if role not in WORKERS:
    sys.exit(f"machine.yaml defines no worker role {role!r}; it has: " + ", ".join(WORKERS))
print(MASTER); print(WORKERS[role]["path"]); print(WORKERS[role]["port"])' "$ROLE") || {
  printf 'cannot resolve worker role "%s" (python said why, above)\n' "$ROLE"; exit 1; }
# stdout only: with stderr folded in, a Python warning became line 1 and was read as MASTER.
mapfile -t _WHERE <<< "$_WHERE"
MASTER="${_WHERE[0]}"
WORKER="${_WHERE[1]}"
CLI_PORT="${_WHERE[2]}"
LOG="$WORKER/user/log/worker-daemon.log"
BARS=(data.db data_futures.h2.db data_stock.h2.db)

running() { ss -ltn 2>/dev/null | grep -q ":${CLI_PORT} "; }
source "$ROOT/bin/sqx-lock.sh"

# Does any sqcli already have this install open? `running` only watches the port, and a
# worker whose AppSettings drifted listens somewhere else -- so the port alone says "free"
# while the H2 database is locked, and the second launch is the one that does the damage.
# Matched by exact process name and working directory, never by a command-line pattern: a
# shell or a `claude -p` whose arguments merely name sqcli is not a worker (rule 2).
install_pids() {
  local p here
  here=$(readlink -f "$WORKER")
  for p in $(pgrep -x 'sqcli|StrategyQuantX|strategyquantx_ui' 2>/dev/null); do   # the GUI's Electron too
    [ "$(readlink -f "/proc/$p/cwd" 2>/dev/null)" = "$here" ] && printf '%s\n' "$p"
  done
  return 0
}
holds_install() { [ -n "$(install_pids)" ]; }

# The worker is alive while its port answers OR its process exists. The port alone lies at
# both ends: a booting worker has a process and no port yet, and one shutting down may drop
# the port while the JVM is still writing its databanks to disk.
alive() { running || holds_install; }
# Wait for the install's process to go, for at most $1 s (default 15), polling every second:
# returns 0 the moment it is gone, 1 (saying what it waited for) when it is still there.
settle_wait() {
  for _ in $(seq 1 "${1:-15}"); do alive || return 0; sleep 1; done
  echo "   still waiting for the $ROLE process to exit after ${1:-15} s" >&2
  return 1
}

# Wait for process $1 to be gone, for at most $2 s, polling every second; 1 (saying so) when it is still there.
pid_wait() {
  for _ in $(seq 1 "$2"); do kill -0 "$1" 2>/dev/null || return 0; sleep 1; done
  echo "   PID $1 still there after $2 s" >&2
  return 1
}
# Wait for the X socket of display $1 (":N") for at most $2 s, polling every second, while the
# Xvfb just launched (PID $3) is alive: a socket left by a killed one proves nothing, and a dead
# Xvfb is no reason to keep waiting.
XSOCK_DIR="${SQX_X_SOCKET_DIR:-/tmp/.X11-unix}"
xvfb_wait() {
  for _ in $(seq 1 "$2"); do
    kill -0 "$3" 2>/dev/null || { echo "   Xvfb (PID $3) died before opening display $1" >&2; return 1; }
    [ -S "$XSOCK_DIR/X${1#:}" ] && return 0
    sleep 1
  done
  echo "   Xvfb display $1 has no socket after $2 s" >&2
  return 1
}

# Seconds `start` waits for the port and `stop` waits for the process. 🔬 2026-10-03, 1,679
# launches in both workers' launcher_*.log against "Server started on port" in SQX's log:
# the port opens 1-7 s after launch (median 2), the 80 GB custodian included -- so 120 s
# without a port is a failed start, not a slow one. The env overrides exist for the tests.
START_WAIT="${SQX_START_WAIT:-120}"
STOP_WAIT="${SQX_STOP_WAIT:-300}"

# One start (or one-shot run) per install at a time. `guard_launch` alone is check-then-act:
# the log prune and `sync_bars` (an md5 of the master's data, then an rsync) sit between the
# check and the launch, and two sessions both passed it -- the 2026-09-23 incident below.
# The flock is held on fd 9 until this script exits; every daemon it launches closes fd 9
# (`9>&-`), or the worker itself would hold the lock for as long as it lives.
take_start_lock() {
  if [ ! -x "$WORKER/sqcli" ]; then
    echo "no SQX install at $WORKER — clone it first: bin/clone-sqx-worker.sh $ROLE"; exit 1
  fi
  mkdir -p "$WORKER/user/log"
  exec 9>"$WORKER/user/log/.start.lock" || {
    echo "cannot open $WORKER/user/log/.start.lock"; exit 1; }
  if ! flock -n 9; then
    printf 'REFUSING: another start or run of %s is in progress (%s is locked).\n' \
      "$ROLE" "$WORKER/user/log/.start.lock"
    printf 'Two launches on one install is how a worker got the port of the master.\n'
    printf 'Wait for it to finish, then look at who holds the install before retrying.\n'
    exit 1
  fi
}

xvfb_file() { printf '%s/user/log/XVFB' "$WORKER"; }
# One display per install, derived from its port, so two workers never share a screen.
xvfb_display() { printf ':%s' "$((CLI_PORT / 10))"; }

# The PID in user/log/XVFB, but only while that process really is this install's Xvfb. The
# file outlives a GUI crash or a reboot, and a bare `kill $(cat XVFB)` then hits whatever
# owns the number now.
xvfb_pid() {
  local pid
  pid=$(cat "$(xvfb_file)" 2>/dev/null) || return 1
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  [ "$(cat "/proc/$pid/comm" 2>/dev/null)" = "Xvfb" ] || return 1
  tr '\0' '\n' <"/proc/$pid/cmdline" 2>/dev/null | grep -qx -- "$(xvfb_display)" || return 1
  printf '%s' "$pid"
}

# Kill this install's Xvfb if the file still names it, and remove the file either way.
drop_xvfb() {
  local pid
  if [ -f "$(xvfb_file)" ]; then
    pid=$(xvfb_pid) && kill "$pid" 2>/dev/null
    rm -f "$(xvfb_file)"
  fi
  rm -f "$XSOCK_DIR/X$(xvfb_display | tr -d :)"     # a killed Xvfb leaves its socket: stale for the next wait
}

# A start whose port never opened used to report the failure and leave its sqcli alive: it
# could come up later with no OWNER lock, invisible to every other session. Kill the one
# this start launched -- by PID, checked to still be a sqcli/StrategyQuantX of this install.
kill_launched() {
  local pid="$1"
  if install_pids | grep -qx -- "$pid"; then
    echo "killing the process this start launched (PID $pid)"
    kill "$pid" 2>/dev/null
    for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
    if kill -0 "$pid" 2>/dev/null; then
      echo "PID $pid ignored SIGTERM for 30 s — sending SIGKILL"
      kill -9 "$pid" 2>/dev/null; pid_wait "$pid" 5 || true
    fi
  fi
  if kill -0 "$pid" 2>/dev/null && install_pids | grep -qx -- "$pid"; then
    echo "⚠️ PID $pid is STILL ALIVE — its owner lock is kept; kill it by PID before retrying"
  else
    rm -f "$(owner_file)"
  fi
  if [ "$(configured_port)" != "$CLI_PORT" ]; then
    echo "⚠️ internal/AppSettings.txt now declares port $(configured_port), not $CLI_PORT — fix it before the next start"
  fi
}
gui_setting() {
  grep -oE "<$1>[^<]*" "$WORKER/user/settings/settings.xml" 2>/dev/null | head -1 | sed "s/<$1>//"
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
  if alive; then
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
  check)
    clear_stale_lock
    check && echo "$ROLE bars are current"
    if [ -f "$(owner_file)" ]; then
      printf 'owner: %s (sqcli PID %s) since %s\n' \
        "$(owner_field holder)" "$(owner_field pid)" "$(owner_field since)"
    else
      echo "owner: none"
    fi
    ;;
  sync)  sync_bars ;;
  stop)
    clear_stale_lock
    # The lock this stop came to remove. Every removal below compares against it: a `start`
    # of another session can write its own while this stop waits, kills or exports.
    LOCK0=$(lock_id)
    # "Running" is the process, not the port: a worker still booting has no port yet, and
    # calling it "not running" removed the lock of a live install.
    if ! alive; then
      echo "$ROLE not running"; drop_xvfb; drop_lock_if_same "$LOCK0"; exit 0
    fi
    refuse_stop_if_held || exit 1
    # GUI mode only while the XVFB file names a live Xvfb of this install. A file left by a
    # GUI crash or a reboot used to send this down the GUI branch: no -exit, a 5 min wait.
    GUI_UP=0
    if [ -f "$(xvfb_file)" ]; then
      if xvfb_pid >/dev/null; then
        GUI_UP=1
      else
        echo "stale $(xvfb_file): its PID is not this install's Xvfb — removed, stopping as a CLI worker"
        rm -f "$(xvfb_file)"
      fi
    fi
    # A stop sent in the ~20 s after `start` returns (port answering, CLI still booting) is
    # silently swallowed, and the old code then waited the full 5 min before saying STILL
    # RUNNING (OPEN.md #75, 2026-09-27, conductor). SQX itself logs the line below the moment
    # its CLI can take a command; wait for it, bounded, before sending -exit. A worker that
    # has been up for a while already has the line, so this costs nothing on a normal stop.
    if [ "$GUI_UP" = "0" ] && ! grep -q 'CLI is now ready' "$LOG" 2>/dev/null; then
      echo -n "waiting for the CLI to finish booting"
      for _ in $(seq 1 30); do
        grep -q 'CLI is now ready' "$LOG" 2>/dev/null && break
        echo -n "."; sleep 1
      done
      echo
    fi
    if [ "$GUI_UP" = "1" ]; then
      # GUI mode never readies the sqcli API («CLI not ready»); its own servlet exits it.
      curl -s -m 30 -H "browserToken: $(gui_setting BrowserToken)" \
        "http://localhost:$(gui_setting WebServerPortUsed)/main/exitapp" >/dev/null 2>&1
    else
      curl -sg -m 30 "http://localhost:${CLI_PORT}/call?cmd=-exit" >/dev/null 2>&1
    fi
    SENT=$?
    # The shutdown sync is what writes the databanks to disk, and it is NOT quick: a
    # 500-strategy databank took over 20 s on its own, and with three of them the JVM was
    # still writing when the old 20-second wait gave up. It did not kill anything — it
    # returned "did not stop" and the next command read a half-written databank: 211 of 500
    # .sqx, no error anywhere (measured 2026-09-24). So wait for the process to actually go
    # — the process, not the port.
    if [ "$SENT" = "7" ]; then
      # curl 7 = connection refused: the exit never reached SQX, so there is no shutdown
      # to wait 5 minutes for. Give a process that was already leaving a few seconds.
      echo "could not reach $ROLE to send it the exit (nothing answers on its port)"
      STOP_WAIT=10
    fi
    echo -n "stopping $ROLE"
    for _ in $(seq 1 "$STOP_WAIT"); do alive || break; echo -n "."; sleep 1; done
    echo
    if alive; then
      # Owner, 2026-10-06: an SQX that does not leave is killed, never left for him to kill from the
      # system monitor. Not while it is still saving: its log moves while the shutdown sync writes
      # databanks (minutes with many projects), so wait while it or its projects' files move, up to
      # 15 min; 60 s of silence with the process still here is the hang. Then SIGTERM by PID, SIGKILL what remains.
      LOGF="$WORKER/user/log/StrategyQuant/log_$(date +%Y_%m_%d).log"
      echo "$ROLE still here after $STOP_WAIT s: waiting while its log or its files move (it may be saving)"
      for _ in $(seq 1 60); do
        alive || break
        # The log alone is not the sign: a 10,000-strategy databank is written for over two minutes
        # without a line, and the kill landed in the middle of it and left a truncated .sqx that
        # blocked the next start (2026-10-09). A file written under user/projects counts as moving.
        if { [ -f "$LOGF" ] && [ $(( $(date +%s) - $(stat -c %Y "$LOGF") )) -lt 60 ]; } \
           || [ -n "$(find "$WORKER/user/projects" -type f -mmin -1 -print -quit 2>/dev/null)" ]; then
          settle_wait 15 || true
        else
          break
        fi
      done
      if alive; then
        echo "   $ROLE silent for 60 s and not leaving: killing by PID $(install_pids | tr '\n' ' ')(never by pattern)"
        for p in $(install_pids); do kill -TERM "$p" 2>/dev/null; done
        for _ in $(seq 1 30); do alive || break; sleep 1; done
        for p in $(install_pids); do kill -KILL "$p" 2>/dev/null; done
        settle_wait 5 || true
      fi
    fi
    if alive; then
      STOPPED=0
      echo "⚠️ $ROLE STILL RUNNING even after the kill — PID(s) $(install_pids | tr '\n' ' ')"
    else
      STOPPED=1
      echo "$ROLE stopped"
      drop_xvfb
      rm -rf "/dev/shm/algobank/$ROLE"    # an .abk is a picture of the session's memory: stale once it ends
    fi
    # The worker just released its log. Quiescent install = safe moment to prune.
    "$ROOT/bin/sqx-log-prune.sh" --auto || true
    # A stop that did not stop is a failure the caller must see: core.worker.stop runs this
    # with check=True, and exit 0 here let it go on to read databanks still being written.
    # The owner lock stays, because the install is still held.
    [ "$STOPPED" = "1" ] || exit 1
    # Before the export, not after it: the install is free from here on, and the export
    # takes minutes in which another session may start it and write its own lock.
    drop_lock_if_same "$LOCK0"
    # Owner, 2026-09-28: every SQX run is exported the moment it ends — metrics, trades and
    # the cosecha of each new or stale databank of the install's Test_/Trade_ projects.
    # ALGO_NO_EXPORT=1 skips it. A failed export never fails the stop (nine callers run it with
    # check=True and the worker is already down), but it is never silent: stderr, and a FALLO
    # line in THIS install's user/log/FALLO-export.txt. A run folder records no role, so writing
    # into the newest estado.txt could hit another worker's run; the window does not read this file yet.
    if ! (cd "$ROOT" && python3 -m ui.daemon.loader.afterrun --role "$ROLE"); then
      MSG="FALLO en el export final tras parar el $ROLE (afterrun salió con error): las exportaciones de sus databanks pueden estar viejas"
      echo "$MSG" >&2
      printf '%s %s\n' "$(date +%F\ %H:%M:%S)" "$MSG" >>"$WORKER/user/log/FALLO-export.txt" || true
    fi
    ;;
  start)
    clear_stale_lock
    running && { echo "$ROLE already running on :$CLI_PORT"; exit 0; }
    take_start_lock
    # Again under the lock: the start that held it a moment ago may have finished.
    running && { echo "$ROLE already running on :$CLI_PORT"; exit 0; }
    guard_launch
    # Nothing holds a log right now, and a start is about to write more of them.
    # --auto is rate-limited, so calling it on every start costs nothing.
    "$ROOT/bin/sqx-log-prune.sh" --auto || true
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    # The prune and the sync can take long; check once more right before launching.
    guard_launch
    # Nothing holds the install, so an XVFB file here is a leftover of a GUI run that
    # crashed: without this a later `stop` of a CLI worker took the GUI branch.
    drop_xvfb
    if [ "$GUI" = "1" ]; then
      DISP=$(xvfb_display)
      OLD_TOKEN=$(gui_setting BrowserToken)
      setsid nohup "$HOME/.local/bin/Xvfb" "$DISP" -screen 0 1920x1080x24 -nolisten tcp \
        >"$WORKER/user/log/xvfb.log" 2>&1 </dev/null 9>&- &
      XVFB_PID=$!
      echo "$XVFB_PID" >"$(xvfb_file)"
      xvfb_wait "$DISP" 10 "$XVFB_PID" || { drop_xvfb; exit 1; }
      env -u ELECTRON_RUN_AS_NODE DISPLAY="$DISP" setsid nohup ./StrategyQuantX >"$LOG" 2>&1 </dev/null 9>&- &
    else
      env -u ELECTRON_RUN_AS_NODE setsid nohup ./sqcli >"$LOG" 2>&1 </dev/null 9>&- &
    fi
    SQCLI_PID=$!
    # The lock is written at launch, not once the port answers: a worker that is booting is
    # already held, and one that comes up late must never come up unowned.
    write_lock "$SQCLI_PID"
    echo -n "starting $ROLE"
    for _ in $(seq 1 "$START_WAIT"); do
      running && break; echo -n "."; sleep 1
    done
    echo
    if running && [ "$GUI" = "1" ]; then
      # SQX writes a fresh BrowserToken to settings.xml once its GUI web server is up.
      echo -n "waiting for the GUI web server"
      for _ in $(seq 1 180); do
        [ "$(gui_setting BrowserToken)" != "$OLD_TOKEN" ] && break; echo -n "."; sleep 1
      done
      echo
      [ "$(gui_setting BrowserToken)" != "$OLD_TOKEN" ] || echo "⚠️ GUI web server did not report a new token"
      echo "gui:        http://localhost:$(gui_setting WebServerPortUsed)  (header browserToken from settings.xml)"
    fi
    if running; then
      echo "worker up:  http://localhost:${CLI_PORT}/call?cmd=-h"
      echo "log:        $LOG"
      echo "owner:      $(resolve_holder)"
    else
      echo "worker failed to start — see $LOG"
      kill_launched "$SQCLI_PID"
      drop_xvfb
      exit 1
    fi
    ;;
  run)
    shift
    # Held until this one-shot ends: a `start` or a second `run` of the same install is
    # refused instead of racing it between the check and the launch.
    take_start_lock
    guard_launch
    sync_bars || exit 1
    cd "$WORKER" || exit 1
    env -u ELECTRON_RUN_AS_NODE ./sqcli "$@" 2>&1 9>&- | grep -vE "DEBUG|oshi|ResponseProcessCookies|set-cookie"
    exit "${PIPESTATUS[0]}"   # sqcli's own code: grep's is 1 whenever it filtered every line
    ;;
  *)
    sed -n '2,23p' "$0" | sed 's/^# \?//'
    exit 1
    ;;
esac
