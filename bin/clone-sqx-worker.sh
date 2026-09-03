#!/bin/bash
# Clone the SQX master into a headless worker.
# Requires: SQX and sqcli both CLOSED. Idempotent-ish: refuses if worker exists.
set -euo pipefail

MASTER="/home/sergioguslw/Desktop/SQX"
WORKER="/home/sergioguslw/Desktop/SQX_w1"
CLI_PORT=5060
EDITOR_PORT=5061
WEB_PORT=8081

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- preflight
say "Preflight"
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

# ---------------------------------------------------------------- 5. heap
say "6. worker heap: sqcli 32g, GUI 8g (in case you ever open it there)"
sed -i 's/^option -Xmx.*$/option -Xmx8g/'  "$WORKER/StrategyQuantX.config"
grep -q 'Xmx' "$WORKER/sqcli.config" \
  && sed -i 's/^option -Xmx.*$/option -Xmx32g/' "$WORKER/sqcli.config" \
  || echo "option -Xmx32g" >> "$WORKER/sqcli.config"

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

say "VERIFY — heap"
printf '   worker sqcli : %s\n' "$(grep Xmx "$WORKER/sqcli.config")"
printf '   worker gui   : %s\n' "$(grep Xmx "$WORKER/StrategyQuantX.config")"

say "DONE"
echo "Worker: $WORKER  ($(du -sh --exclude=user/data "$WORKER" 2>/dev/null | cut -f1) + symlinked History)"
echo
echo "Next: start it headless and confirm it answers on its OWN port:"
echo "  cd $WORKER && env -u ELECTRON_RUN_AS_NODE ./sqcli -project action=list"
echo "  curl -sg \"http://localhost:${CLI_PORT}/call?cmd=-project%20action=list\""
