"""The «Contra el activo y el azar» tab: the original strategy on `oos2` against holding its
asset and against random traders with its own footprint."""

import pandas as pd

from core.study import blocks, result as envelope

SAYS = {"pass": "Bate a {a}: todo el intervalo de la diferencia de Sharpe está por encima de 0.",
        "watch": "No se distingue de {a}: el intervalo de la diferencia de Sharpe incluye el 0 "
                 "— con estos días no se puede decir ni que lo bata ni que sea peor.",
        "fail": "Peor que {a}: todo el intervalo de la diferencia de Sharpe está por debajo de "
                "0; mantener {a} comprado con el mismo riesgo rindió más."}
STAT = {"net": "beneficio neto (USD)", "sharpe": "Sharpe por operación", "pf": "PF",
        "retdd": "beneficio / DD", "dd": "DD máx. (USD, menos es mejor)"}
ALPHA = 0.05


def _asset(got: dict) -> list[dict]:
    """The comparison with the asset held at equal risk."""
    a = got["asset"]
    numbers = pd.DataFrame([
        ["Sharpe de la estrategia", round(got["sharpe"], 2), None, None],
        [f"Sharpe de {a} comprado", round(got["asset_sharpe"], 2), None, None],
        ["diferencia", round(got["difference"], 2), *[round(x, 2) for x in got["difference_band"]]],
        [f"beta frente a {a}", round(got["beta"], 3), None, None],
        [f"Sharpe sin la parte de {a}", round(got["residual_sharpe"], 2),
         *[round(x, 2) for x in got["residual_band"]]]],
        columns=["", "valor", "intervalo bajo", "intervalo alto"])
    curves = got["curves"]
    keep = blocks.thin(len(curves))
    years = got["years"].mul(100).round(2)
    table = pd.DataFrame({"año": years.index.astype(str), "estrategia %": years["estrategia"],
                          f"{a} %": years["activo"],
                          "gana": ["sí" if s > g else "no" for s, g in years.to_numpy()]})
    return [
        {"kind": "callout", "state": got["state"], "text": SAYS[got["state"]].format(a=a)
         + f" Estrategia original, parámetros fijos, sólo el oos2 ({got['from']} → "
           f"{got['to']}, {got['days']} días)."},
        blocks.table(f"Contra {a} comprado", numbers,
                     "Sharpe anual sobre el P/L diario marcado al cierre de cada día. Intervalos "
                     "al 95 % por bootstrap estacionario de días emparejados (bloques de un mes). "
                     "«Sin la parte del activo»: lo que queda tras quitar lo que la estrategia "
                     "gana sólo por estar expuesta a él; cerca de 0 = no aporta nada propio."),
        {"kind": "lines", "title": f"Estrategia y {a} con el mismo riesgo", "unit": "%",
         "x": [curves.index[i].date().isoformat() for i in keep],
         "series": [{"label": "estrategia", "role": "real",
                     "values": [float(curves["estrategia"].iloc[i] * 100) for i in keep]},
                    {"label": f"{a} comprado, misma volatilidad", "role": "reference",
                     "values": [float(curves["activo"].iloc[i] * 100) for i in keep]}]},
        {**blocks.table("Año a año", table, f"Rentabilidad de cada año natural; {a} escalado a la "
                        "volatilidad de la estrategia."),
         "states": [[None, None, None, "pass" if w == "sí" else "fail"] for w in table["gana"]]}]


def _monkey(m: dict | None) -> list[dict]:
    """The comparison with random traders of the same footprint."""
    if m is None:
        return [{"kind": "callout", "state": "none", "text": "Contra el azar: no se corre, el "
                 "oos2 tiene muy pocas operaciones de la original."}]
    rows = pd.DataFrame(
        [[STAT[r["statistic"]], round(r["real"], 3), round(r["mean"], 3), round(r["p95"], 3),
          round(r["below"] * 100, 1), r["p"]] for r in m["rows"]],
        columns=["estadístico", "la estrategia", "trader al azar medio", "al azar p95",
                 "% de traders al azar que supera", "p"])
    p = next(r["p"] for r in m["rows"] if r["statistic"] == "sharpe")
    beats = p <= ALPHA
    return [
        {"kind": "callout", "state": "pass" if beats else "watch",
         "text": (f"{'Bate' if beats else 'No se distingue d'}{' al' if beats else 'el'} trader al "
                  f"azar en Sharpe: p = {p:.4f}. {m['draws']:,} traders con su misma huella — "
                  f"las mismas {m['trades']} operaciones, duración, tamaño, dirección y costes "
                  "— que sólo cambian cuándo entran, sobre las barras reales del oos2.")},
        {**blocks.table("Contra el trader al azar", rows,
                        "p = parte de los traders al azar que igualan o superan a la estrategia; "
                        "el menor observable es 1/(traders+1). En un activo que sube, el azar "
                        "comprando también gana: por eso se mira además contra el activo. "
                        f"Reconciliación del motor con las operaciones reales: {m['reconcile']:.5f}; "
                        f"semilla {m['seed']}."),
         "states": [[None] * 5 + ["pass" if r["p"] <= ALPHA else None] for r in m["rows"]]}]


def tab(got: dict) -> dict:
    """One strategy's two comparisons, as a tab.

    Args:
        got: `run.against()[strategy]`.

    Returns:
        Against the asset — verdict, numbers with intervals, both curves, year by year —
        then against chance: verdict on Sharpe and every statistic with its p.
    """
    return envelope.tab("asset", "Contra el activo y el azar", _asset(got) + _monkey(got["monkey"]),
                        note="La curva es la estrategia original, no una celda de la matriz: "
                             "escoger una de las 30 después de verlas sería ya elegir sobre la "
                             "muestra que se juzga. Y sólo el oos2: el oos1 ya sirvió para "
                             "cribar la población, y un tramo que eligió no puede juzgar.")
