#!/bin/bash
# Clone the SQX master into a headless worker of a given role.
# Requires: SQX and sqcli both CLOSED. Idempotent-ish: refuses if the worker exists.
#
# Usage: clone-sqx-worker.sh [ROLE]      ROLE is conductor (default) or custodian.
#
# Where each install lives and which port it owns comes from config/machine.yaml
# through core/paths.py — nothing is hard-coded here.
set -euo pipefail

ROLE="${1:-conductor}"
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

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

# The port convention of knowhow/03-driving-sqx.md: each install owns a triple
# <cli> / <cli+1> / <web>, with the master at 5050 / 5051 / 8080 and every worker
# ten above the previous one. Derived, so a new role only sets its cli port.
EDITOR_PORT=$((CLI_PORT + 1))
WEB_PORT=$((8080 + (CLI_PORT - 5050) / 10))

# Heaps and cores from the same table. The conductor stays small because it must
# only ever answer; the custodian holds one large databank for hours.
# ⚠️ These are the PC-A (96c / 125 GB) numbers. PC-B is 16c and wants 2 / 8 cores.
case "$ROLE" in
  custodian) SQCLI_XMX=48g; CORES=48 ;;
  *)         SQCLI_XMX=16g; CORES=8  ;;
esac

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- preflight
say "Preflight — role $ROLE: $WORKER (ports $CLI_PORT / $EDITOR_PORT / $WEB_PORT)"
[ -d "$MASTER" ] || { echo "master not found: $MASTER"; exit 1; }
[ -e "$WORKER" ] && { echo "worker already exists: $WORKER — remove it first"; exit 1; }

if pgrep -f "StrategyQuantX|strategyquantx_ui|sqcli" >/dev/null 2>&1; then
  echo "SQX or sqcli is running. Close it first — H2 takes exclusive locks."; exit 1
fi
for p in 5050 5051 8080 "$CLI_PORT" "$EDITOR_PORT" "$WEB_PORT"; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then echo "port $p is in use"; exit 1; fi
done
echo "ok — nothing running, ports free"

# ---------------------------------------------------------------- 1. copy
say "1. rsync master -> worker (excluding data, logs, projects)"
rsync -a --info=progress2 \
  --exclude='user/data/' \
  --exclude='user/log/' \
  --exclude='user/projects/' \
  "$MASTER/" "$WORKER/"

mkdir -p "$WORKER/user/log" "$WORKER/user/projects" "$WORKER/user/data"

# ---------------------------------------------------------------- 2. data
say "2. data: copy the H2 bars, symlink the raw History store"
# The H2 files are per-install (exclusive lock). History is a shared raw archive.
rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"
ln -sfn "$MASTER/user/data/History" "$WORKER/user/data/History"
ls -la "$WORKER/user/data/" | sed 's/^/   /'

# ---------------------------------------------------------------- 3. ports
say "3. patch (a) internal/AppSettings.txt — sqcli + editor ports"
sed -i \
  -e "s|<AppWebServerPortSQUANT>[0-9]*</AppWebServerPortSQUANT>|<AppWebServerPortSQUANT>${CLI_PORT}</AppWebServerPortSQUANT>|" \
  -e "s|<AppWebServerPortSQEDITOR>[0-9]*</AppWebServerPortSQEDITOR>|<AppWebServerPortSQEDITOR>${EDITOR_PORT}</AppWebServerPortSQEDITOR>|" \
  "$WORKER/internal/AppSettings.txt"
cat "$WORKER/internal/AppSettings.txt" | sed 's/^/   /'

# ---------------------------------------------------------------- 4. paths
say "4. patch (b) settings.xml — rewrite every absolute path to the worker"
# Without this the worker is a silent ALIAS of the master and will corrupt it.
sed -i "s|${MASTER}/|${WORKER}/|g" "$WORKER/user/settings/settings.xml"

say "5. patch (c) settings.xml — WebServerPortUsed (the third port)"
sed -i "s|<WebServerPortUsed>[0-9]*</WebServerPortUsed>|<WebServerPortUsed>${WEB_PORT}</WebServerPortUsed>|" \
  "$WORKER/user/settings/settings.xml"

say "6. patch (d) settings.xml — coreUsage ${CORES}"
# Inherited from the master this is -1, i.e. every core. Two installs both taking
# every core is how a worker starves the owner's build.
if grep -q '<coreUsage>' "$WORKER/user/settings/settings.xml"; then
  sed -i "s|<coreUsage>[-0-9]*</coreUsage>|<coreUsage>${CORES}</coreUsage>|" \
    "$WORKER/user/settings/settings.xml"
else
  sed -i "0,/<Settings>/s||<Settings>\n  <coreUsage>${CORES}</coreUsage>|" \
    "$WORKER/user/settings/settings.xml"
fi

# ---------------------------------------------------------------- 5. heap
say "7. worker heap: sqcli ${SQCLI_XMX}, GUI 8g (in case you ever open it there), -Xms 1g"
sed -i -e 's/^option -Xmx.*$/option -Xmx8g/' -e 's/^option -Xms.*$/option -Xms1g/' \
  "$WORKER/StrategyQuantX.config"
sed -i 's/^option -Xms.*$/option -Xms1g/' "$WORKER/sqcli.config"
grep -q 'Xmx' "$WORKER/sqcli.config" \
  && sed -i "s/^option -Xmx.*\$/option -Xmx${SQCLI_XMX}/" "$WORKER/sqcli.config" \
  || echo "option -Xmx${SQCLI_XMX}" >> "$WORKER/sqcli.config"

# ---------------------------------------------------------------- verify
say "VERIFY — stray paths still pointing at the master"
STRAY=$(grep -o "${MASTER}/[^<]*" "$WORKER/user/settings/settings.xml" || true)
if [ -n "$STRAY" ]; then
  echo "FAIL — these keys still point at the master:"; echo "$STRAY" | sed 's/^/   /'
  echo "The worker would be an alias of the master. Fix before starting it."; exit 1
fi
echo "ok — no path in settings.xml points at the master"

say "VERIFY — ports differ from the master"
printf '   master : %s\n' "$(grep -oE '<AppWebServerPort[A-Z]*>[0-9]+' "$MASTER/internal/AppSettings.txt" | tr '\n' ' ')"
printf '   worker : %s\n' "$(grep -oE '<AppWebServerPort[A-Z]*>[0-9]+' "$WORKER/internal/AppSettings.txt" | tr '\n' ' ')"
printf '   master web: %s | worker web: %s\n' \
  "$(grep -o '<WebServerPortUsed>[0-9]*' "$MASTER/user/settings/settings.xml")" \
  "$(grep -o '<WebServerPortUsed>[0-9]*' "$WORKER/user/settings/settings.xml")"

say "VERIFY — cores"
printf '   master : %s\n' "$(grep -o '<coreUsage>[-0-9]*' "$MASTER/user/settings/settings.xml")"
printf '   worker : %s\n' "$(grep -o '<coreUsage>[-0-9]*' "$WORKER/user/settings/settings.xml")"

say "VERIFY — heap"
printf '   worker sqcli : %s\n' "$(grep Xmx "$WORKER/sqcli.config")"
printf '   worker gui   : %s\n' "$(grep Xmx "$WORKER/StrategyQuantX.config")"

say "DONE"
echo "Worker ($ROLE): $WORKER  ($(du -sh --exclude=user/data "$WORKER" 2>/dev/null | cut -f1) + symlinked History)"
echo
echo "Next: start it headless and confirm it answers on its OWN port:"
echo "  bin/sqx-worker.sh --role $ROLE start"
echo "  curl -sg \"http://localhost:${CLI_PORT}/call?cmd=-project%20action=list\""
echo "  bin/sqx-worker.sh --role $ROLE stop"
