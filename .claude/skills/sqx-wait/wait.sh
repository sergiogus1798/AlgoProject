#!/bin/bash
# wait — block until an SQX run on a worker ends, then print ONE line (rule 18).
#
# Usage:
#   wait.sh [--role ROLE] mark            print the log's current line count; take it BEFORE action=start
#   wait.sh [--role ROLE] [--from N]      wait; reads the log from line N (default: its end now)
#   ROLE is custodian (default) or conductor.
#
# Exit: 0 finished · 1 failed · 2 worker gone · 3 free RAM under 15 GB.
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
ROLE=custodian
FROM=""
while true; do
  case "${1:-}" in
    --role) ROLE="${2:?--role needs a role}"; shift 2 ;;
    --from) FROM="${2:?--from needs a line number}"; shift 2 ;;
    *) break ;;
  esac
done

WHERE=$(cd "$ROOT" && python3 -c '
import sys
from core.paths import WORKERS
w = WORKERS[sys.argv[1]]
print(w["path"]); print(w["port"])' "$ROLE" 2>&1) || { printf 'cannot resolve role "%s":\n  %s\n' "$ROLE" "$WHERE"; exit 1; }
mapfile -t WHERE <<< "$WHERE"
LOGS="${WHERE[0]}/user/log/StrategyQuant"
PORT="${WHERE[1]}"

newest() { ls -t "$LOGS"/*.log 2>/dev/null | head -1; }
LOG=$(newest)
[ -n "$LOG" ] || { echo "no log under $LOGS"; exit 1; }

if [ "${1:-}" = "mark" ]; then echo $(( $(wc -l < "$LOG") + 1 )); exit 0; fi
[ -n "$FROM" ] || FROM=$(( $(wc -l < "$LOG") + 1 ))

END='Project finished'
BAD='Project stopped|Exception in task|OutOfMemory'
# The run's lines: the marked log from FROM on, plus any log SQX opened after it (midnight).
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
  FREE=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
  if [ "$FREE" -lt 15 ]; then echo "low-ram: ${FREE} GB free, the run is still going"; exit 3; fi
  sleep 10
done
