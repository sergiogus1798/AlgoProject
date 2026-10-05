#!/bin/bash
# workflow — the whole workflow of one project, steps 5 to 25, in one command. Nothing to decide:
# every choice is an argument, a missing one is an error, and the first failure ends it.
#
# Usage:
#   bin/workflow.sh simple   <PROJECT> <SYMBOL> <TF> <long|short> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES> [--smoke]
#   bin/workflow.sh template <PROJECT> <SYMBOL> <TF> <TEMPLATE.sqx> <PALETTE|-> "<PURPOSE>" <STRATEGIES> <MINUTES> [--smoke]
#   bin/workflow.sh run      <PROJECT> [--smoke] [--restart]
#   bin/workflow.sh plan     <PROJECT>
#
#   simple    creates a Simple Strategy project (no template, one side) on the custodian,
#             applies the palette, then runs it.
#   template  the same from an authored template; the palette fills its random hole, `-` when
#             the template has none (two fixed conditions a side, hard rule 14).
#   run       runs an existing project from wherever its rail says it is.
#   plan      prints what `run` would do and runs nothing.
#
#   --smoke    functional test, Test_ projects only: only the readability rules judge.
#   --restart  the old route (SQX starts and stops at every step, slower). Only when
#              the single session fails.
#
# Exit 0: the run ended (read the printed resumen.md). Non-zero: it did not start or it failed;
# the reason is printed. Never retry by hand what this script refused: report it.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

die() { printf 'workflow: %s\n' "$*" >&2; exit 1; }
MODE=${1:-}; P=${2:-}
[[ $MODE =~ ^(simple|template|run|plan)$ && -n $P ]] || { sed -n '2,24p' "$0"; exit 2; }
[[ $P =~ ^(Test|Trade|Research)_[A-Za-z0-9_]+$ ]] || die "nombre de proyecto no válido: $P (Test_/Trade_/Research_, solo guiones bajos)"
ROLE=custodian
CFX=$(python3 -c "from core.paths import project_dir, worker_dir; print(project_dir('$P', worker_dir('$ROLE')) / 'project.cfx')") || die "no se resuelve la ruta del proyecto"

if [[ $MODE == plan ]]; then
    exec python3 -m pipeline.autopilot.run --project "$P" --plan
fi

FLAGS=()
if [[ $MODE == simple || $MODE == template ]]; then
    [[ $# -ge 9 ]] || die "$MODE necesita 8 argumentos tras el modo: mira el uso (bin/workflow.sh)"
    SYMBOL=$3; TF=$4; WHAT=$5; PALETTE=$6; PURPOSE=$7; N=$8; MIN=$9; shift 9
    if [[ $MODE == simple ]]; then
        [[ $WHAT =~ ^(long|short)$ ]] || die "el lado es long o short, no «$WHAT»"
        KIND=(--simple "$WHAT")
        [[ $PALETTE != - ]] || die "una Simple Strategy necesita paleta"
    else
        [[ -f $WHAT ]] || die "no existe la plantilla $WHAT"
        KIND=(--template "$WHAT")
    fi
    [[ $N =~ ^[0-9]+$ && $MIN =~ ^[0-9]+$ ]] || die "STRATEGIES y MINUTES son números enteros"
    [[ -e $CFX ]] && die "$P ya existe en el $ROLE: usa «run»"
    python3 -m core.assets "$SYMBOL" || die "core.assets $SYMBOL salió con error (regla 5): no se crea nada"
    python3 -m sqx.projects.builder "$P" --purpose "$PURPOSE" "${KIND[@]}" --symbol "$SYMBOL" \
        --role $ROLE --timeframe "$TF" --workflow --max-strategies "$N" --minutes "$MIN" \
        || die "el builder no creó $P"
    if [[ $PALETTE != - ]]; then
        python3 -m sqx.projects.buildingblocks --project "$P" --palette "$PALETTE" --role $ROLE \
            || die "no se aplicó la paleta $PALETTE"
    fi
    FLAGS+=(--own-log)          # this script wrote the worker's recent log itself
else
    shift 2
    [[ -e $CFX ]] || die "$P no existe en el $ROLE: créalo con «simple» o «template»"
fi
for flag in "$@"; do
    [[ $flag =~ ^--(smoke|restart)$ ]] || die "opción desconocida: $flag"
    FLAGS+=("$flag")
done

LOG=$(mktemp)
python3 -m pipeline.autopilot.run --project "$P" --panel 21=CrossTF_Mothers --panel 22=Results \
    "${FLAGS[@]}" > "$LOG" 2>&1
CODE=$?
OUT=$(sed -n 's/^carpeta del run: //p' "$LOG" | head -1)
if [[ -z $OUT ]]; then      # refused before it began: its own words are the reason
    tail -5 "$LOG" >&2; rm -f "$LOG"; die "el autopiloto no empezó"
fi
rm -f "$LOG"
cat "$OUT/estado.txt"
[[ -e $OUT/fallo.md ]] && head -5 "$OUT/fallo.md"
echo "resumen: $OUT/resumen.md"
exit $CODE
