"""How many strategies of a databank beat their monkeys, and how many should have by chance."""

import argparse
import time
from datetime import date

import pandas as pd

from core.manifest import read as read_manifest
from core.paths import DATA, report_dir
from core.study import blocks, output, result as envelope
from core.study.render import markdown
from engines.inference import excess as measure
from engines.inference.fdr import discoveries

MODULE = "studies.screening.monkeyExcess.report"
ALPHA = 0.05
PREFILTERED = 0.95      # share profitable above which the sample was selected on this sample


def newest(project: str, databank: str) -> tuple:
    """The most recent null panel of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        (the panel, its manifest). Reports accumulate, so the newest is the current one.
    """
    folder = DATA / "reports" / project / databank.replace(" ", "_")
    found = sorted(folder.glob("*/monkey/nulls.csv"))[-1]
    return pd.read_csv(found), read_manifest(found.parent)


def rows(panel: pd.DataFrame, rung: str, alpha: float, draws: int) -> list[dict]:
    """The excess and the named survivors, one row per statistic.

    Args:
        panel: What studies.readings.monkey.report wrote.
        rung: Which rung's p-values to read.
        alpha: The level and the false discovery rate.
        draws: Null runs behind each p.

    Returns:
        One dict per statistic, carrying what excess() and resolution() found plus `named`,
        how many survive Benjamini-Hochberg. `observed` and `named` answer different
        questions and routinely disagree by a lot.
    """
    out = []
    for name in [c[len("real_"):] for c in panel.columns if c.startswith("real_")]:
        p = panel[f"p_{rung}_{name}"].to_numpy()
        got = measure.excess(p, alpha) | measure.resolution(p, alpha, draws)
        tests = [{"metric": s, "p": v} for s, v in zip(panel["strategy"], p)]
        out.append({"statistic": name, "named": len(discoveries(tests, alpha))} | got)
    return out


def contamination(panel: pd.DataFrame) -> str:
    """Whether the sample being tested is the one the strategies were selected on.

    Args:
        panel: What studies.readings.monkey.report wrote.

    Returns:
        A warning, or an empty string. A databank whose members are almost all profitable
        out of sample was filtered on that sample, and then the excess is not a verdict on
        the generator: it is a measurement of the filter. The check is on the data rather
        than on the project config because the config says what the task does **today** and
        the databank was filled whenever it was filled.
    """
    share = float((panel["real_net"] > 0).mean())
    if share < PREFILTERED:
        return ""
    return (f"MUESTRA PRESELECCIONADA: el {100 * share:.1f}% de estas estrategias gana dinero "
            f"en la muestra que se esta juzgando. Una poblacion asi fue filtrada POR esta "
            f"muestra, de modo que el exceso de abajo mide el filtro y no el generador. "
            f"Para leerlo como veredicto del generador hace falta una databank sin "
            f"condiciones de aceptacion sobre esta muestra.")


def result(panel: pd.DataFrame, made: dict, rung: str, alpha: float, started: float) -> dict:
    """The databank's excess over chance as one result, with every reason to read it warily.

    Args:
        panel: What studies.readings.monkey.report wrote.
        made: Its manifest.
        rung: Which rung's p-values to read.
        alpha: The level and the false discovery rate.
        started: When the computation began.

    Returns:
        The contract dict: a call on the first statistic, the table per statistic, and the
        warnings — preselection, unreachable resolution, signal nobody can be named for.
    """
    draws = made["source"]["draws"]
    found = rows(panel, rung, alpha, draws)
    first = found[0]
    warn = [{"code": "preseleccionada", "state": "fail", "text": contamination(panel)}] \
        if contamination(panel) else []
    if not first["reachable"]:
        warn.append({"code": "resolucion", "state": "watch",
                     "text": f"Con {draws:,} monos el p más pequeño posible es "
                             f"{first['floor']:.1e}, y Benjamini-Hochberg pide {first['bar']:.1e} "
                             f"para la mejor de {first['n']:,}. Para que fuese nombrable harían "
                             f"falta {first['draws_needed']:,} monos."})
    for r in found:
        if r["named"] == 0 and r["observed"] > r["expected_all_null"]:
            warn.append({"code": f"sin_nombre_{r['statistic']}", "state": "watch",
                         "text": f"{r['statistic']}: {r['observed']} pasan y ninguna es "
                                 f"nombrable. Hay señal ({r['excess']:.0f} de exceso) pero "
                                 f"ninguna destaca entre {r['n']:,}."})
        if r["saturated"]:
            warn.append({"code": f"topados_{r['statistic']}", "state": "watch",
                         "text": f"{r['statistic']}: {r['saturated']} p topados en "
                                 f"{r['floor']:.1e}: no están medidos, tocan el suelo."})
    table = pd.DataFrame([[r["statistic"], r["observed"], r["expected_all_null"], r["excess"],
                           r["fdr"], r["named"], r["share_null"]] for r in found],
                         columns=["estadístico", "pasan", "si ninguna tuviera edge", "exceso",
                                  "de las pasadas, suerte", "nombrables",
                                  "sin edge (Storey)"])
    return envelope.envelope(
        MODULE, None, None, {"alpha": alpha, "rung": rung}, started,
        [envelope.tab("excess", "Cuántas baten al mono, y cuántas deberían", [
            {"kind": "bars", "title": "Exceso sobre el azar, por estadístico",
             "unit": "estrategias", "reference": 0.0,
             "items": [{"label": r["statistic"], "value": r["excess"], "error": None,
                        "state": "pass" if r["excess"] > 0 else "fail"} for r in found]},
            blocks.table("Por estadístico", table,
                         f"Pasan: baten a su mono a p<{alpha:.2f}. Si ninguna tuviera edge: "
                         f"{alpha} x {first['n']:,}. Exceso: cuántas son probablemente "
                         f"reales. Nombrables: las que sobreviven Benjamini-Hochberg. El "
                         f"exceso y las nombrables discrepan a propósito.")],
            note=f"{len(panel):,} estrategias · muestra {made['source']['sample']} · "
                 f"{draws:,} monos por estrategia · peldaño {rung}.")],
        blocks.verdict(f"{first['excess']:+.0f} en {first['statistic']}",
                       "pass" if first["excess"] > 0 else "fail",
                       f"{first['observed']} baten al mono donde el azar daría "
                       f"{first['expected_all_null']:.0f}; {first['named']} se pueden nombrar."),
        warn)


def main() -> None:
    """Read a databank's null panel and write the observed-against-chance report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--rung", default="", help="por defecto el primero del panel")
    a = ap.parse_args()

    started = time.time()
    panel, made = newest(a.project, a.databank)
    got = result(panel, made, a.rung or made["source"]["rungs"][0], a.alpha, started)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "monkeyExcess"
    title = f"{a.project} / {a.databank} — cuántas baten al mono, y cuántas deberían"
    output.population(out, "monkeyExcess", got, title)
    print(markdown.render(got, title))
    print(f"\n-> {out / 'monkeyExcess.md'}")


if __name__ == "__main__":
    main()
