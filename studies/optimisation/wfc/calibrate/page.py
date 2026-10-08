"""The calibration's report in Spanish: the verdict on top, then the criterion beside the one without a null on the level."""

import numpy as np
import pandas as pd

from studies.optimisation.wfc.calibrate import families, rates

KIND = {families.NONE: "sin ventaja", families.FLAT: "ventaja, sin orden",
        families.ORDER: "ventaja, con orden"}
LEGEND = """## Cómo se lee

- **Familia**: un lote sintético de variantes que comparten un factor común (una semana mala lo
  es para todas). «Sin ventaja»: la media semanal es cero, o negativa cuando lleva costes. «Ventaja,
  sin orden»: todas ganan lo mismo (meseta plana). «Ventaja, con orden»: unas ganan más que otras
  y lo mantienen fuera.
- **Sharpe**: la media plantada, como Sharpe anualizado del exceso semanal de la variante media
  (cada variante tiene entre 0,7 y 1,7 veces ese Sharpe, según cuánto carga en el factor común).
  0,5 en 2,75 años es un estadístico t de 0,83: poco más que ruido.
- **Criterio** (la tabla de la propuesta del paso 17, §6, con el nulo del nivel del encargo 48;
  dueño, 2026-10-08): PASA si el orden no es perverso, la mediana fuera del top es > 0 y esa
  mediana supera su propio nulo de volteo de signos (p del nivel ≤ alfa del nivel, con los
  mismos sorteos del orden). LIMBO: la mediana es > 0 sin superar el nulo, o el orden es
  perverso con el top ganando. NO PASA: la mediana del top es ≤ 0.
- **Sin nulo en el nivel**: sólo para comparar: la tabla como se escribió primero, en la que
  basta con que la mediana del top sea > 0.
- **Las familias sintéticas no llevan costes**: su exceso bruto es su neto, y se sortean semana
  a semana, que es la unidad que voltea el nulo.
- **Falso PASA**: fracción de familias sin ventaja que salen PASA. **Falso NO PASA**: fracción
  de familias con ventaja plantada que salen NO PASA (el error irreversible: un NO PASA no se
  revisa). Una con ventaja que sale LIMBO no se pierde: queda en espera.
- **± error**: una tasa medida en N familias tiene un error típico de raíz(p·(1−p)/N).
"""


def num(value: float | None, digits: int = 2) -> str:
    """A number the Spanish way, or a dash."""
    return "—" if value is None or pd.isna(value) else f"{value:.{digits}f}".replace(".", ",")


def grid(rows: list[list], head: list[str]) -> str:
    """A markdown table."""
    lines = [head, ["---"] * len(head), *rows]
    return "\n".join("| " + " | ".join(str(c) for c in line) + " |" for line in lines)


def versus(table: pd.DataFrame) -> str:
    """Every scenario's PASA / LIMBO / NO PASA under the criterion and without a null on the level."""
    rows = []
    for r in table.to_dict("records"):
        rows.append([num(r["anos_fuera"]), KIND[r["tipo"]], num(r["sharpe"]),
                     *(num(r[f"{s}{suffix}"]) for suffix in ("", "_sin") for s in rates.STATES)])
    return grid(rows, ["años fuera", "familia", "Sharpe", "PASA", "LIMBO", "NO PASA",
                       "PASA (sin nulo)", "LIMBO (sin nulo)", "NO PASA (sin nulo)"])


def trade(table: pd.DataFrame, edge: float) -> str:
    """What the null on the level buys and costs at each out-of-sample length, in one line each."""
    lines = []
    for years, at in table.groupby("anos_fuera"):
        none = at[(at["tipo"] == families.NONE) & (at["sharpe"] == 0)].iloc[0]
        hit = at[(at["tipo"] != families.NONE) & (at["sharpe"] == edge)]
        lines.append(f"- **{num(years)} años fuera** — falso PASA sin ventaja: "
                     f"**{num(none['pasa'])}** con el criterio, {num(none['pasa_sin'])} "
                     f"sin nulo en el nivel; falso NO PASA con Sharpe {num(edge)}: "
                     f"**{num(hit['no_pasa'].max())}** con el criterio, "
                     f"{num(hit['no_pasa_sin'].max())} sin nulo; con ventaja que queda en "
                     f"LIMBO: **{num(hit['limbo'].max())}**, {num(hit['limbo_sin'].max())} sin "
                     f"nulo (peor de con y sin orden).")
    return "\n".join(lines)


def cells(table: pd.DataFrame) -> str:
    """The rate of every cell of the owner's table (order x the top's median above zero) and of each state."""
    rows = [[num(r["anos_fuera"]), KIND[r["tipo"]], num(r["sharpe"]),
             *(num(r[c]) for c in rates.CELLS), *(num(r[s]) for s in rates.STATES)]
            for r in table.to_dict("records")]
    return grid(rows, ["años fuera", "familia", "Sharpe", *(c.replace("_", " ") for c in rates.CELLS),
                       "PASA", "LIMBO", "NO PASA"])


def rehearsal(found: dict) -> str:
    """The real batches rehearsed in build -> oos1, or the plain statement that there is none."""
    if not found["lotes"]:
        return ("0 lotes: ningún lote tiene `variant_trades.parquet` todavía (lo escribe la "
                "fábrica del paso 16.5 en su próxima corrida en SQX).")
    rows = [[r["lote"], r["n"], r["casilla"].replace("_", " "), r["estado"].replace("_", " "),
             r["estado_sin"].replace("_", " "), num(r["rho"]), num(r["nivel_top"]),
             num(r["p_nivel"], 3), num(r["sd_rho_nulo"])] for r in found["lotes"]]
    said = found["tasas"]
    return (f"{len(rows)} lotes. PASA {num(said['pasa'])} (sin nulo {num(said['pasa_sin'])}) · "
            f"LIMBO {num(said['limbo'])} · NO PASA {num(said['no_pasa'])}. La verdad de un lote "
            "real no se conoce: son tasas de casilla, no falsos ni perdidos.\n\n"
            + grid(rows, ["lote", "variantes", "casilla", "estado", "sin nulo en el nivel", "ρ",
                          "nivel del top", "p del nivel", "sd de ρ en el nulo"]))


def text(table: pd.DataFrame, decision: dict, rehearsed: dict, cfg: dict, wfc: dict,
         written: bool) -> str:
    """The whole report.

    Args:
        table: What `rates.table` returned.
        decision: What `record.decide` returned.
        rehearsed: What `rehearsal.run` returned.
        cfg, wfc: The calibration's config and the WFC's.
        written: Whether the register was written by this run.
    """
    main, side = (table[table["bloque"] == b] for b in ("rejilla", "sensibilidad"))
    ref, n = cfg["reference"], cfg["families"]
    error = np.sqrt(decision["falso_pasa"] * (1 - decision["falso_pasa"]) / n)
    base = main[(main["tipo"] == families.NONE) & (main["sharpe"] == 0)]
    return "\n\n".join([
        "# Calibración del paso 17 (WFC)",
        f"**El registro {'ABRE' if decision['abre'] else 'NO ABRE'} el bloque ciego** "
        f"(`abre: {str(decision['abre']).lower()}`): {decision['motivo']}.\n\n"
        f"Criterio (con nulo en el nivel), a {num(ref['years_out'])} años "
        f"fuera: falso PASA sin ventaja **{num(decision['falso_pasa'])}** (tope "
        f"{num(cfg['max_false_pass'])}, ± {num(error)}; sin nulo en el nivel sería "
        f"{num(decision['falso_pasa_sin'])}) · falso NO PASA con Sharpe {num(ref['edge'])} "
        f"**{num(decision['falso_no_pasa'])}** (tope {num(cfg['max_false_fail'])}; sin nulo "
        f"{num(decision['falso_no_pasa_sin'])}). {n} familias "
        f"por escenario, {cfg['family']['variants']} variantes, {wfc['null']['draws']} sorteos, "
        f"alfa del orden {num(wfc['null']['alpha'])}, alfa del nivel "
        f"{num(wfc['level']['alpha'])}."
        + ("" if written else "\n\n**Registro NO escrito**: la corrida lleva `--set`; el "
           "registro sólo sale de la configuración tal como está en el ledger."),
        "## 1. El criterio frente al de sin nulo en el nivel, coste junto a ganancia",
        trade(main, ref["edge"]), versus(main),
        "## 2. Casillas de la tabla del criterio, por escenario", cells(main),
        "## 3. ¿Se parecen las variantes como en un lote real?",
        f"Desviación de la ρ en el nulo de volteo, familias sin ventaja: mediana "
        f"{num(base['sd_rho_p50'].median())} (5 %–95 % de las familias: "
        f"{num(base['sd_rho_p5'].min())} a {num(base['sd_rho_p95'].max())}). La corrida de "
        "referencia midió 0,09 a 0,41, mediana 0,26, en lotes reales (propuesta §4.2). Abajo, las "
        "casillas de referencia con las variantes menos parecidas (ruido propio 1,0) y más "
        "parecidas (0,2):",
        grid([[num(r["ruido_propio"]), KIND[r["tipo"]], num(r["sharpe"]), num(r["sd_rho_p50"]),
               num(r["pasa"]), num(r["no_pasa"]), num(r["pasa_sin"]), num(r["no_pasa_sin"])]
              for r in side.to_dict("records")],
             ["ruido propio", "familia", "Sharpe", "sd de ρ en el nulo", "PASA", "NO PASA",
              "PASA (sin nulo)", "NO PASA (sin nulo)"]),
        "## 4. Ensayo en lotes reales, build → oos1 (tramos ya gastados; nunca oos2)",
        rehearsal(rehearsed), LEGEND])
