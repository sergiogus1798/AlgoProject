#!/bin/bash
# wait — block until an SQX run on a worker ends, then print ONE line (rule 18).
#
# Usage:
#   wait.sh [--role ROLE] mark            print FILE:LINE, where the log ends now; take it BEFORE action=start
#   wait.sh [--role ROLE] [--from MARK] [--max-hours N]
#                                         wait; reads MARK's file from its line on and every newer
#                                         log whole (default: the newest log's end now). A bare
#                                         line number, the old mark, means the newest log at wait time.
#   ROLE is custodian (default) or conductor. N is whole hours, 72 by default.
#   SQX_WAIT_LOGS and SQX_WAIT_PORT replace the role's log folder and port: for tests/test_sqx_wait.py only.
#
# Exit: 0 finished · 1 failed · 2 worker gone · 3 free RAM under 15 GB · 4 still running after N hours.
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
ROLE=custodian
FROM=""
MAX_HOURS=72
while true; do
  case "${1:-}" in
    --role) ROLE="${2:?--role needs a role}"; shift 2 ;;
    --from) FROM="${2:?--from needs a mark}"; shift 2 ;;
    --max-hours) MAX_HOURS="${2:?--max-hours needs a number of hours}"; shift 2 ;;
    *) break ;;
  esac
done
case "$MAX_HOURS" in ''|*[!0-9]*) echo "--max-hours takes whole hours, not '$MAX_HOURS'"; exit 1 ;; esac

if [ -n "${SQX_WAIT_LOGS:-}" ]; then
  LOGS="$SQX_WAIT_LOGS"; PORT="${SQX_WAIT_PORT:?SQX_WAIT_LOGS needs SQX_WAIT_PORT}"
else
  WHERE=$(cd "$ROOT" && python3 -c '
import sys
from core.paths import WORKERS
w = WORKERS[sys.argv[1]]
print(w["path"]); print(w["port"])' "$ROLE" 2>&1) || { printf 'cannot resolve role "%s":\n  %s\n' "$ROLE" "$WHERE"; exit 1; }
  mapfile -t WHERE <<< "$WHERE"
  LOGS="${WHERE[0]}/user/log/StrategyQuant"
  PORT="${WHERE[1]}"
fi

newest() { ls -t "$LOGS"/*.log 2>/dev/null | head -1; }
ends() { echo $(( $(wc -l < "$1") + 1 )); }

case "$FROM" in
  *:*) LOG="${FROM%:*}"; FROM="${FROM##*:}"                     # a mark: that file, from that line
       [ -f "$LOG" ] || { echo "the marked log is gone: $LOG"; exit 1; } ;;
  *)   LOG=$(newest)
       [ -n "$LOG" ] || { echo "no log under $LOGS"; exit 1; } ;;
esac
if [ "${1:-}" = "mark" ]; then echo "$LOG:$(ends "$LOG")"; exit 0; fi
[ -n "$FROM" ] || FROM=$(ends "$LOG")
case "$FROM" in *[!0-9]*) echo "--from takes FILE:LINE or a line number, not '$FROM'"; exit 1 ;; esac

END='Project finished'
# «Error while running project»: SQX aborted the run and will never write END (🔬 2026-09-29).
BAD='Project stopped|Exception in task|OutOfMemory|Error while running project'
# The run's lines: the marked log from FROM on, plus any log SQX opened after it (midnight, a later start).
lines() { tail -n +"$FROM" "$LOG"; find "$LOGS" -name '*.log' -newer "$LOG" -exec cat {} + 2>/dev/null; }

while true; do
  HIT=$(lines | grep -m1 -E "$END|$BAD")
  if [ -n "$HIT" ]; then
    if grep -qE "$END" <<< "$HIT"; then echo "finished: ${HIT:0:200}"; exit 0; fi
    echo "failed: ${HIT:0:200}"; exit 1
  fi
  if ! ss -ltn 2>/dev/null | grep -q ":${PORT} "; then
    echo "gone: nothing listens on :$PORT and the log never said '$END'"; exit 2
  fi
  if [ "$SECONDS" -ge $(( MAX_HOURS * 3600 )) ]; then
    echo "timeout: no '$END' after ${MAX_HOURS} h, the worker still listens on :$PORT"; exit 4
  fi
  FREE=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
  if [ "$FREE" -lt 15 ]; then echo "low-ram: ${FREE} GB free, the run is still going"; exit 3; fi
  sleep 10
done
