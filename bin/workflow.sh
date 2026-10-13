#!/bin/bash
# workflow — the whole workflow of one project, steps 5 to 21 and 26, in one command. Nothing to decide:
# every choice is an argument, a missing one is an error, and the first failure ends it.
#
# Usage:
#   bin/workflow.sh simple   <PROJECT> <SYMBOL> <TF> <long|short> <FAMILY> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES> [--until STEP] [--smoke] [MT5]
#   bin/workflow.sh template <PROJECT> <SYMBOL> <TF> <TEMPLATE.sqx> <PALETTE|-> "<PURPOSE>" <STRATEGIES> <MINUTES> [--until STEP] [--smoke] [MT5]
#   bin/workflow.sh run      <PROJECT> [--until wfm] [--smoke] [--restart] [MT5]
#   bin/workflow.sh plan     <PROJECT>
#
#   simple    creates a Simple Strategy project (no template, one side) on the custodian,
#             applies the palette, then runs it. FAMILY is the idea family, required, one key of
#             `_expected_sign` (assets/_markets.yaml); it is recorded in projects/registry.csv.
#   template  the same from an authored template; the palette fills its random hole, `-` when
#             the template has none (two fixed conditions a side, hard rule 14).
#   run       runs an existing project from wherever its rail says it is.
#   plan      prints what `run` would do and runs nothing.
#
#   --until    (simple, template) the project carries no task after this step, and the run ends
#              at its judge: oos (7), crossmarket (10), crosstf (12), mcretest (14), spp (16), wfm (19: the
#              project keeps every task and the run stops before step 20; repeat it on «run»).
#   --smoke    functional test, Test_ projects only: only the readability rules judge, and at most 3
#              strategies go on after step 8 (`judge.SMOKE_KEEP`): it proves the steps run, nothing else.
#   --restart  the old route (SQX starts and stops at every step, slower). Only when
#              the single session fails.
#   MT5        step 26, run only when the four are given, each as ONE word with «=»:
#              --mt5-from=YYYY-MM-DD|MT5 --mt5-to=YYYY-MM-DD --mt5-model=every_tick|ohlc_m1|open_prices|real_ticks
#              --mt5-firms=ftmo,hantec  (and --mt5-real-ticks). Without them the run ends before step 26.
#   --own-log  (run) the worker's recent log is the caller's own previous try, not
#              someone else's run: do not wait its 15 quiet minutes.
#
# Exit 0: the run ended (read the printed resumen.md). Non-zero: it did not start or it failed;
# the reason is printed. Never retry by hand what this script refused: report it.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

die() { printf 'workflow: %s\n' "$*" >&2; exit 1; }
# A project created and then not finished (its trim or its palette failed) is retired at once: left
# there, a retry would find it, go to «run» and build with the donor's blocks (hard rule 15).
# When the retire itself refuses (the worker up), a marker in its folder makes «run» refuse it.
undo() {
    python3 -m sqx.projects.retire "$P" --role $ROLE --yes --own >&2 \
        || { touch "$(dirname "$CFX")/A_MEDIO_CREAR"; die "$*; y $P NO se pudo retirar: «run» lo rechaza hasta que se retire a mano"; }
    die "$*; $P retirado: un reintento lo crea de nuevo"
}
MODE=${1:-}; P=${2:-}
[[ $MODE =~ ^(simple|template|run|plan)$ && -n $P ]] || { sed -n '2,28p' "$0"; exit 2; }
[[ $P =~ ^(Test|Trade|Research)_[A-Za-z0-9_]+$ ]] || die "nombre de proyecto no válido: $P (Test_/Trade_/Research_, solo guiones bajos)"
ROLE=custodian
CFX=$(python3 -c "from core.paths import project_dir, worker_dir; print(project_dir('$P', worker_dir('$ROLE')) / 'project.cfx')") || die "no se resuelve la ruta del proyecto"

if [[ $MODE == plan ]]; then
    exec python3 -m pipeline.autopilot.run --project "$P" --plan
fi

FLAGS=()
if [[ $MODE == simple || $MODE == template ]]; then
    FAMILY=
    if [[ $MODE == simple ]]; then    # FAMILY sits after the side: take it out, then both modes read alike
        [[ $# -ge 10 ]] || die "simple necesita 9 argumentos tras el modo (con FAMILY): mira el uso (bin/workflow.sh)"
        FAMILY=$6; set -- "${@:1:5}" "${@:7}"
    fi
    [[ $# -ge 9 ]] || die "$MODE necesita 8 argumentos tras el modo: mira el uso (bin/workflow.sh)"
    SYMBOL=$3; TF=$4; WHAT=$5; PALETTE=$6; PURPOSE=$7; N=$8; MIN=$9; shift 9
    UNTIL=; if [[ ${1:-} == --until ]]; then UNTIL=${2:-}; shift 2; fi
    [[ -z $UNTIL || $UNTIL =~ ^(oos|crossmarket|crosstf|mcretest|spp|wfm)$ ]] || die "--until no conoce el paso «$UNTIL»"
    if [[ $MODE == simple ]]; then
        [[ $WHAT =~ ^(long|short)$ ]] || die "el lado es long o short, no «$WHAT»"
        KIND=(--simple "$WHAT" --family "$FAMILY")
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
    if [[ $UNTIL == wfm ]]; then    # nothing to drop: the tail itself stops before step 20
        FLAGS+=(--until wfm)
    elif [[ -n $UNTIL ]]; then
        python3 -c "import sys; from pathlib import Path; from sqx.projects.workflow import trim; print('sin las tareas de después de', sys.argv[2] + ':', ', '.join(trim(Path(sys.argv[1]), sys.argv[2])))" "$CFX" "$UNTIL" \
            || undo "no se recortó $P a «$UNTIL»"
    fi
    if [[ $PALETTE != - ]]; then
        python3 -m sqx.projects.buildingblocks --project "$P" --palette "$PALETTE" --role $ROLE \
            || undo "no se aplicó la paleta $PALETTE"
    fi
    FLAGS+=(--own-log)          # this script wrote the worker's recent log itself
else
    shift 2
    if [[ ${1:-} == --until ]]; then    # only the tail's cut is repeated on a resume
        [[ ${2:-} == wfm ]] || die "«run» sólo conoce --until wfm"
        FLAGS+=(--until wfm); shift 2
    fi
    [[ -e $CFX ]] || die "$P no existe en el $ROLE: créalo con «simple» o «template»"
    [[ ! -e $(dirname "$CFX")/A_MEDIO_CREAR ]] || die "$P quedó a medio crear (sin su recorte o su paleta): retíralo y créalo de nuevo"
fi
for flag in "$@"; do
    [[ $flag =~ ^--(smoke|restart|own-log|mt5-real-ticks)$|^--mt5-(from|to|model|firms)=.+$ ]] || die "opción desconocida: $flag"
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
mv "$LOG" "$OUT/salida.txt"     # everything it printed stays with the run, the refusal's reason too
if [[ ! -e $OUT/estado.txt ]]; then     # its folder made, then refused (the worker not free)
    tail -5 "$OUT/salida.txt" >&2; die "el autopiloto no empezó"
fi
cat "$OUT/estado.txt"
[[ -e $OUT/fallo.md ]] && head -5 "$OUT/fallo.md"
echo "resumen: $OUT/resumen.md"
# Rule 6 (owner D28): a Test_ project is retired when the run ends. A failed run keeps it for
# inspection; a refusal (survivors not in the store) is an error, never silent. Trade_/Research_ stay.
if [[ $P == Test_* ]]; then
    if [[ -n ${UNTIL:-} || " ${FLAGS[*]} " == *" --until "* ]]; then   # unfinished on purpose: a later «run» resumes it
        echo "workflow: la corrida lleva --until: $P NO se retira, queda para continuarlo con «run»" >&2
    elif [[ $CODE -ne 0 ]]; then
        echo "workflow: la corrida falló: $P NO se retira, queda para inspeccionarlo" >&2
    else
        bin/sqx-worker.sh --role $ROLE stop >&2 || die "no se paró el $ROLE: $P NO se retira"
        python3 -m sqx.projects.retire "$P" --role $ROLE --yes --own >&2 \
            || die "$P NO se retiró (¿supervivientes sin guardar?): guárdalas con /store-save y retíralo con python3 -m sqx.projects.retire $P --role $ROLE --yes"
    fi
fi
exit $CODE
