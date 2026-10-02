#!/bin/bash
# preflight — who holds each SQX install right now. Reads only; changes nothing.
#
# Usage:
#   preflight.sh
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
# core/paths.py is the only place that knows where an install lives.
WHERE=$(cd "$ROOT" && python3 -c '
from core.paths import MASTER, WORKERS
print("master", MASTER, "-")
for role, w in WORKERS.items():
    print(role, w["path"], w["port"])' 2>&1) || { printf 'cannot resolve the installs:\n  %s\n' "$WHERE"; exit 1; }

echo "== sqcli / StrategyQuantX processes"
pgrep -af 'sqcli|StrategyQuantX' | grep -v pgrep | cut -c1-160 || echo "none"
echo "== listening"
ss -ltnp 2>/dev/null | grep -E 'java|sqcli|Strategy' | awk '{print $4, $6}' || echo "none"

while read -r ROLE DIR PORT; do
  echo "== $ROLE  $DIR  port $PORT"
  if [ "$PORT" != "-" ]; then
    ss -ltn 2>/dev/null | grep -q ":${PORT} " && echo "port: UP" || echo "port: down"
  fi
  if [ -f "$DIR/user/log/OWNER" ]; then echo "lock: $(tr '\n' ' ' < "$DIR/user/log/OWNER")"; else echo "lock: none"; fi
  ls -lt "$DIR/user/projects" 2>/dev/null | sed -n 2,6p | awk '{print "  " $6, $7, $8, $9}'
done <<< "$WHERE"
