#!/bin/bash
# workflow-test — the WHOLE workflow, from the builder to step 26, as one functional test that
# says PASA or FALLA by itself (owner, 2026-10-13: «tu trabajo no termina hasta que se haya
# corrido TODO el workflow desde el builder hasta el final SIN ERRORES»). Profit is irrelevant:
# it proves every step runs. One run, no retry, no «run» to continue: a run that needed a fix
# does not count — fix it, then run this again from scratch.
#
# Usage:
#   bin/workflow-test.sh [TAG]        TAG: letters and digits for the project's name; default the hour
#
# What it runs — fixed, so two runs are comparable (owner, 2026-10-13, E2 and P26):
#   bin/workflow.sh simple Test_XAUUSD_H1_ruptura_wt<TAG> XAUUSD H1 long breakout ruptura_base_v3
#       10000 strategies, 30 minutes of Build, --smoke (only readability judges, 3 go on after step 8)
#       step 26 on FTMO and Hantec, 2021-07-01 to 2022-12-31, model ohlc_m1 — a window inside
#       oos1: the autopilot's step 26 is refused on oos2 (ledger.gate, assets/_policy.yaml)
#
# PASA only when ALL of these hold:
#   - bin/workflow.sh exits 0 and the last status line is FIN, with no FALLO anywhere;
#   - step 26 ran (a row «| 26 | mt5verify» in resumen.md) — a strategy that does not validate in
#     MT5 is a result, a step 26 that did not launch is a failure;
#   - no fast-route fallback: no `fallback` row in fases.csv (a `.abk` dumped and refused);
#   - the run did not end early («Se para antes», «no dejó ninguna superviviente»).
# Exit 0 = PASA, 1 = FALLA (the reasons are printed), 2 = it could not start.
#
# Never edit bin/workflow.sh while this runs: bash reads a script as it executes it, and an edit
# mid-run broke the end of a run on 2026-10-13 (the project was not retired).
set -uo pipefail
cd "$(dirname "$0")/.."

# Step 26 verifies on FTMO only: Hantec's one login (8063673) is a real funded account, stopped
# on purpose, and mt5.guard refuses it («sin cuenta de verificación»). Put hantec back in
# --mt5-firms when a Hantec demo login exists in machine.yaml (owner, 2026-10-15).
TAG=${1:-$(date +%H%M)}
[[ $TAG =~ ^[A-Za-z0-9]+$ ]] || { echo "workflow-test: TAG sólo lleva letras y dígitos, no «$TAG»" >&2; exit 2; }
P=Test_XAUUSD_H1_ruptura_wt$TAG
SAID=$(mktemp)
bin/workflow.sh simple "$P" XAUUSD H1 long breakout ruptura_base_v3 \
    "Prueba funcional del workflow entero, del builder al paso 26" 10000 30 --smoke \
    --mt5-from=2021-07-01 --mt5-to=2022-12-31 --mt5-model=ohlc_m1 --mt5-firms=ftmo 2>&1 | tee "$SAID"
CODE=${PIPESTATUS[0]}
OUT=$(sed -n 's|^resumen: \(.*\)/resumen.md$|\1|p' "$SAID" | tail -1)
rm -f "$SAID"
if [[ -z $OUT || ! -e $OUT/resumen.md ]]; then
    echo "workflow-test: FALLA — la corrida no empezó o no dejó resumen (salida $CODE)"; exit 2
fi

WHY=()
[[ $CODE -eq 0 ]] || WHY+=("bin/workflow.sh salió con $CODE")
[[ $(tail -1 "$OUT/estado.txt") == *" FIN "* ]] || WHY+=("la última línea de estado no es FIN: $(tail -1 "$OUT/estado.txt")")
grep -q 'FALLO' "$OUT/estado.txt" && WHY+=("hay un FALLO en estado.txt")
[[ -e $OUT/fallo.md ]] && WHY+=("existe fallo.md: $(head -1 "$OUT/fallo.md")")
grep -q '^| 26 | mt5verify' "$OUT/resumen.md" || WHY+=("el paso 26 no corrió (sin fila «| 26 | mt5verify» en resumen.md)")
grep -qE 'Se para antes|no dejó ninguna superviviente|no se lanza|ningún finalista' "$OUT/resumen.md" \
    && WHY+=("la corrida acabó antes del final: $(grep -oE 'Se para antes[^.|]*|no dejó ninguna superviviente[^.|]*|no se lanza[^|]*|ningún finalista[^.|]*' "$OUT/resumen.md" | head -1)")
N=$(grep -c ',fallback,' "$OUT/fases.csv" 2>/dev/null); N=${N:-0}
[[ $N -eq 0 ]] || WHY+=("$N caída(s) a la ruta lenta: $(grep ',fallback,' "$OUT/fases.csv" | head -1 | cut -d, -f4- | cut -c1-200)")

echo
if [[ ${#WHY[@]} -eq 0 ]]; then
    echo "workflow-test: PASA — $P, del builder al paso 26, sin errores. $OUT/resumen.md"
    exit 0
fi
echo "workflow-test: FALLA — $P. $OUT/resumen.md"
printf '  - %s\n' "${WHY[@]}"
exit 1
