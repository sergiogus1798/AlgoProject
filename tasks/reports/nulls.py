"""How many strategies of a databank beat their monkeys, and how many should have by chance."""

import argparse
from datetime import date

import pandas as pd

from core.manifest import code_version, read as read_manifest
from core.paths import DATA
from tasks.analysis import excess as measure
from tasks.analysis.correlations import discoveries

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
        panel: What nulls.report wrote.
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
        panel: What nulls.report wrote.

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


def main() -> None:
    """Read a databank's null panel and write the observed-against-chance report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--rung", default="", help="por defecto el primero del panel")
    a = ap.parse_args()

    panel, made = newest(a.project, a.databank)
    draws = made["source"]["draws"]
    rung = a.rung or made["source"]["rungs"][0]
    found = rows(panel, rung, a.alpha, draws)

    lines = [f"# {a.project} / {a.databank} — cuantas baten al mono, y cuantas deberian",
             "",
             f"{len(panel):,} estrategias · muestra {made['source']['sample']} · "
             f"{draws:,} monos por estrategia · peldano `{rung}` · "
             f"informe {date.today().isoformat()} · codigo {code_version()}", ""]
    warning = contamination(panel)
    if warning:
        lines += [f"> ⚠️ **{warning}**", ""]
    lines += ["| estadistico | pasan | si NINGUNA tuviera edge | exceso | de las pasadas, suerte | nombrables |",
              "|---|---|---|---|---|---|"]
    for r in found:
        lines.append(f"| `{r['statistic']}` | {r['observed']} | {r['expected_all_null']:.0f} | "
                     f"**+{r['excess']:.0f}** | {100 * r['fdr']:.0f}% | {r['named']} |")
    first = found[0]
    lines += ["",
              f"**pasan**: baten a su mono a p<{a.alpha:.2f}. **si ninguna tuviera edge**: lo que "
              f"daria el azar puro, {a.alpha} x {first['n']:,}. **exceso**: lo que sobra, o sea "
              f"cuantas son probablemente reales. **nombrables**: las que sobreviven "
              f"Benjamini-Hochberg, o sea a cuantas puedes senalar con el dedo.",
              "",
              "El exceso y las nombrables contestan preguntas distintas y discrepan a proposito: "
              "una poblacion puede tener senal evidente sin que ninguna de sus miembros destaque "
              "lo suficiente para nombrarla.", ""]
    share = ", ".join(f"`{r['statistic']}` {r['share_null']:.2f}" for r in found)
    lines += [f"Estimacion de Storey de que fraccion no tiene edge: {share}. Un 0.00 no es un "
              f"error: es el estimador diciendo que no ve tests nulos, que es como se ve una "
              f"familia con senal por todas partes.", ""]
    if not first["reachable"]:
        lines.append(f"- Con {draws:,} monos el p mas pequeno posible es {first['floor']:.1e}, y "
                     f"Benjamini-Hochberg pide {first['bar']:.1e} para la MEJOR de {first['n']:,}. "
                     f"Eso solo impide nombrar el primer puesto — el procedimiento sube escalones, "
                     f"asi que puede nombrar k tests cuyo k-esimo p baje de k x {a.alpha}/{first['n']:,}. "
                     f"Para que la mejor fuese nombrable harian falta {first['draws_needed']:,} monos.")
    for r in found:
        if r["named"] == 0 and r["observed"] > r["expected_all_null"]:
            lines.append(f"- ⚠️ `{r['statistic']}`: {r['observed']} pasan y **ninguna es nombrable**. "
                         f"Hay senal ({r['excess']:.0f} de exceso) pero ninguna destaca lo bastante "
                         f"entre {r['n']:,} candidatas.")
        if r["saturated"]:
            lines.append(f"- ⚠️ `{r['statistic']}`: {r['saturated']} p topados en {r['floor']:.1e}. "
                         f"No estan medidos, estan tocando el suelo.")

    out = DATA / "reports" / a.project / a.databank.replace(" ", "_") / date.today().isoformat() / "monkeyExcess"
    out.mkdir(parents=True, exist_ok=True)
    (out / "excess.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n-> {out / 'excess.md'}")


if __name__ == "__main__":
    main()
