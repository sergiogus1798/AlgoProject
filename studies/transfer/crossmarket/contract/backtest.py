"""The tab the study opens on: what every market's real backtest did, before any simulation."""

import pandas as pd

from core.study import blocks, result as envelope
from core.symbols import alias
from studies.transfer.crossmarket.contract import shared, words
from studies.transfer.crossmarket.simulate import joint, metrics

# MinTRL's cell when the real Sharpe does not clear the reference one (`min_track_record`
# returns None): no sample length would make it significant, so no number is printed.
UNREACHABLE = "No alcanzable"
SHARPE_TOTAL = ("Sharpe clásico de todo el backtest: P&L de cada día hábil (lunes a viernes, "
                "los días sin cierres cuentan como 0), media / desv. × √252.")


def master(rows: pd.DataFrame, base: dict) -> dict:
    """Every market's backtest at face value, the base asset last and marked as reference.

    §4.6 (owner, 2026-09-30): Profit Factor right after Net Profit; dropped Retorno en cuenta,
    Longest losing run and the "usables en los tests" count — the last is still the count the
    tests actually use (`r.trades`), just not printed here any more, since it is already on
    every per-market row of "Qué sostiene esos números" (Nº trades).
    """
    order = ["net", "pf", "dd", "dd_pct", "ret_dd"]
    body = [[alias(r.feed), *[r.real[k] * (100 if k.endswith("_pct") else 1) for k in order],
             r.sharpe_total, int(r.trades_all)] for r in rows.itertuples()]
    body.append([f"{alias(base['feed'])} (activo base, referencia)",
                 *[base["real"][k] * (100 if k.endswith("_pct") else 1) for k in order],
                 base["sharpe_total"], base["trades_all"]])
    return {**blocks.table("El backtest de cada mercado", pd.DataFrame(
        body, columns=["mercado", *[metrics.LABELS[k] for k in order], "Sharpe total",
                       "operaciones (SQX)"]),
        "Estadísticos de SQX sobre todas las operaciones, así que cuadran con la databank. En "
        "el activo base cada número es producto de la búsqueda: dice que el código funciona, "
        "nada de la estrategia."),
        "help": [None] * (len(order) + 1) + [SHARPE_TOTAL, None]}


def equal_risk(rows: pd.DataFrame, base: dict, target: float) -> dict:
    """Each market's return once every one is sized to the same worst drawdown."""
    body = [[alias(r.feed), r.equalised["factor"], r.equalised["return_pct"], r.real["ret_dd"],
             r.real["dd_pct"] * 100] for r in rows.itertuples()]
    body.append([f"{alias(base['feed'])} (base)", base["equalised"]["factor"],
                 base["equalised"]["return_pct"], base["real"]["ret_dd"],
                 base["real"]["dd_pct"] * 100])
    return blocks.table("A riesgo igualado", pd.DataFrame(
        body, columns=["mercado", "factor de tamaño", f"retorno (%) con DD = {target:.0%}",
                       "Ret/DD", "DD real (%)"]),
        "El peor drawdown es un solo momento de la muestra; léelo junto al Ret/DD, que es "
        "libre de escala y no depende de un único pico.")


def equity(record: dict, cfg: dict) -> dict:
    """Every market's equity in its own account, in dollars, on one calendar axis."""
    dates, placed = shared.on_axis(record["equity"], "usd")
    series = [{"label": alias(feed), "values": values,
               "role": "reference" if feed == record["base"]["feed"] else "real"}
              for feed, values in placed.items()]
    return {"kind": "lines", "title": "Equity de cada mercado, en su propia cuenta",
            "unit": "USD", "x": dates, "series": series, "auto_dash_negative": True,
            "zero_shade": True,
            "note": f"Cada mercado con su propia cuenta de {cfg['equity']['starting']:,.0f} $; "
                    f"un backtest que empieza más tarde empieza más tarde en el gráfico. "
                    f"Discontinua la que acaba bajo cero; sombreado verde por encima de cero, "
                    f"rojo por debajo."}


def correlation(corr: dict) -> dict:
    """The weekly-returns correlation matrix, base asset included, on a discrete scale."""
    names = list(corr)
    shown = [alias(n) for n in names]
    return {"kind": "grid", "title": "Correlación de los retornos semanales", "rows": shown,
            "cols": shown, "values": [[corr[r][c] for c in names] for r in names],
            "scale": "diverging", "levels": [-0.6, -0.4, -0.2, -0.05, 0.05, 0.2, 0.4, 0.6],
            "labels": None,
            "help": "Sobre el cambio semana a semana de cada curva de equity, no sobre su "
                    "nivel: dos curvas pueden compartir tendencia (nivel) sin compartir qué "
                    "semanas ganan o pierden (retorno), y es lo segundo lo que dice si dos "
                    "mercados son evidencia independiente o la misma apuesta mirada dos veces. "
                    "Una correlación media ρ entre N mercados dice que el número de mercados "
                    "«realmente independientes» ronda N / (1 + (N−1)·ρ): a ρ = 0,8 nueve "
                    "mercados valen como poco más de uno. Combinar dos mercados a menos de "
                    "0,3 diversifica de verdad; combinar dos por encima de 0,7 casi no añade "
                    "nada que el primero no dijera ya.",
            "note": "De retornos semanales de cada curva, no de sus métricas. Dos mercados a "
                    "0,8 no son dos confirmaciones: son una apuesta mirada dos veces."}


def joint_null(view: dict, alpha: float) -> dict:
    """The joint null as one a-priori number, or why there is none."""
    names = ", ".join(alias(m) for m in view["markets"]) or "ninguno"
    head = ("El nulo conjunto" if view["reason"] else "¿Se traslada? El nulo conjunto")
    if view["reason"]:
        return {**blocks.table(head, pd.DataFrame(
            [["sin p conjunto", joint.REASONS[view["reason"]]], ["mercados", names]],
            columns=["", ""])),
            "help": [None, "Un solo estadístico decidido de antemano — la media de mean_r, un "
                     "voto por mercado — contra miles de sorteos donde el mismo desplazamiento "
                     "de calendario se aplica a todos los mercados a la vez."]}
    return {**blocks.table(head, pd.DataFrame(
        [["p conjunto", view["p"]], ["z del conjunto", view["z"]],
         ["estadístico real agrupado", view["observed"]], ["mercados", names]],
        columns=["", "valor"]),
        f"Un solo estadístico decidido de antemano — la media de mean_r, un voto por mercado — "
        f"contra {view['draws']:,} sorteos en los que el mismo desplazamiento de calendario "
        f"se aplica a todos los mercados a la vez, así que la dependencia entre ellos ya va "
        f"dentro. No combina los p por mercado. El activo base no entra. Modelo "
        f"{view['model']}, agregación {view['pool']}, criterio {alpha:.2f}."),
        "help": ["p conjunto: qué fracción de los sorteos conjuntos igualó o superó al real. "
                 "z del conjunto: distancia al nulo en unidades de su propia anchura, para "
                 "comparar aunque el p sature.", None]}


def tests(rows: pd.DataFrame) -> dict:
    """Every test's result per market, as numbers rather than a verdict."""
    return {**blocks.table("Qué dijo cada test", pd.DataFrame(
        [[alias(r.feed), r.p, r.z, r.edge_r, r.paired_p, r.paired_usd_total, r.risk_normalised,
          len(r.warnings)] for r in rows.itertuples()],
        columns=["mercado", f"p ({words.TEST_1A})", f"z ({words.TEST_1A})", "ventaja (ATR)",
                 f"p ({words.TEST_1B})", f"Alpha acumulado ({words.TEST_1B}, USD)",
                 "A / unidad de riesgo (Exposición)", "avisos"]),
        "z es la distancia al nulo en unidades de su propia anchura: compara mercados donde "
        "el p ya no puede. No se convierte en ningún p normal."),
        "help": [None, None, None,
                 "Real menos la mediana de los sorteos aleatorios, en unidades de ATR: el "
                 "tamaño del efecto de Entrada aleatoria. Esta columna, junto con p y z, viene "
                 "de «Mean R» — la media del resultado por operación en R, el único "
                 "estadístico que decide el veredicto de esta estrategia, fijado de antemano; "
                 "no se mueve por lo que se elija en ningún selector de la pestaña Modelos.",
                 f"p del test de Wilcoxon de {words.TEST_1B}: la probabilidad de ver un Alpha "
                 f"de timing al menos así de grande si las entradas no eligieran momento — "
                 f"cada operación comparada con la media de todas las ventanas de su misma "
                 f"duración en su mismo tramo. Bajo (≤ 0,05): las entradas escogen mejores "
                 f"velas que las de alrededor. Se lee, no decide nada todavía.",
                 f"Cuánto de lo que ganó la estrategia lo puso el momento de entrar — el "
                 f"resultado de {words.TEST_1B} — sumado en dólares sobre toda la muestra.",
                 "«A dividido unidad»: el exceso por vela sobre la vela media del mercado "
                 "(A, de la pestaña Exposición), expresado en unidades de la volatilidad típica del "
                 "mercado para que mercados distintos comparen.",
                 "Cuántas de las 8 comprobaciones posibles saltaron en este mercado (pocas "
                 "operaciones, fills pendientes, error de fill, deriva no distinguible de "
                 "cero, calendario perdido, muestra corta para el Sharpe, mal ajuste de "
                 "duraciones, operaciones fuera de rejilla), sumadas en «avisos en total» de "
                 "La estrategia en una tabla."]}


def evidence(rows: pd.DataFrame, base: dict) -> dict:
    """Sharpe total, the reference Sharpe, and the track record its shape demands (MinTRL)."""
    entries = [(alias(r.feed), r._asdict()) for r in rows.itertuples()]
    entries.append((f"{alias(base['feed'])} (base)", base))
    body = [[f, r["sharpe_total"], r["min_track_benchmark"], int(r["trades"]),
             UNREACHABLE if pd.isna(r["min_track_needed"]) else r["min_track_needed"], r["pf"],
             r["expectancy"]] for f, r in entries]
    states = [[None, None, None, None,
              "fail" if not r["min_track_enough"] else None, None, None] for _, r in entries]
    return {**blocks.table("Qué sostiene esos números", pd.DataFrame(
        body, columns=["mercado", "Sharpe total", "Sharpe de referencia", "Nº trades",
                       "MinTRL", "PF", "Expectancy (retorno log. neto medio)"])),
        "states": states,
        "help": [None,
                 SHARPE_TOTAL,
                 "SR*: el Sharpe de un operador aleatorio con la misma huella de mercado "
                 "(misma ocupación de barras, mismo coste) — casi siempre negativo, porque el "
                 "coste supera lo que esa ocupación capta de la deriva del mercado. Está en "
                 "escala por operación, no anualizada: es la que MinTRL necesita, y no es la "
                 "misma escala que «Sharpe total» — ambos números viven aquí para que se vean "
                 "juntos, no para restarse.",
                 None,
                 "Cuántas operaciones harían falta para que el Sharpe por operación real se "
                 "distinga del de referencia, dados su sesgo y sus colas (Bailey / López de "
                 "Prado). En rojo cuando supera el Nº trades real: falta muestra para lo que "
                 "pide. «No alcanzable» (en rojo) cuando el Sharpe real no supera al de "
                 "referencia: ninguna muestra, por larga que sea, lo haría significativo.",
                 None,
                 "Retorno logarítmico neto medio por operación (no en unidades de R): el "
                 "mismo log(cierre/apertura) − coste que usa todo el estudio, sin normalizar "
                 "por ningún riesgo por operación."],
        "note": "MinTRL: cuántas operaciones harían falta para que este Sharpe se distinga del "
                "de referencia, dados su sesgo y sus colas (Bailey / López de Prado; γ₄ es "
                "curtosis no excesiva). Compárese con «coste de equilibrio» en breakeven: "
                "ambos preguntan lo mismo — cuánta ventaja hace falta antes de que el coste se "
                "la coma — desde direcciones distintas."}


def breadth(summary: dict) -> dict:
    """The worst and median PF, breadth, and the strategy's other headline facts."""
    w = summary["worst_market"]
    return {**blocks.table("La estrategia en una tabla", pd.DataFrame(
        [["Peor PF", f"{w['pf']:.2f} en {alias(w['market'])}"],
         ["Mediana de PF entre mercados", f"{summary['median_pf']:.2f}"],
         ["Mercados con CI de expectancy > 0", f"{summary['cleared']}/{summary['markets']}"],
         ["STD del PF entre mercados", f"{summary['pf_cv']:.2f}"],
         [f"Mercados bajo alpha en {words.TEST_1A}",
          f"{summary['under_alpha']}/{summary['markets']}"],
         [f"Mercados bajo alpha en {words.TEST_1B}",
          f"{summary['paired_under_alpha']}/{summary['markets']}"],
         ["Avisos en total", str(summary["warnings"])]], columns=["", "valor"])),
        "help": [None, "«Mercados con CI de expectancy > 0»: cuántos mercados tienen el "
                 "intervalo de confianza (5–95 %) de la expectancy por operación enteramente "
                 "por encima de cero — es la única criba de este estudio (breadth_floor). "
                 "«Avisos en total»: suma, sobre todos los mercados, de cuántas de las 8 "
                 "comprobaciones posibles saltaron en cada uno (pocas operaciones, fills "
                 "pendientes, error de fill, deriva no distinguible de cero, calendario "
                 "perdido, muestra corta para el Sharpe, mal ajuste de duraciones, operaciones "
                 "fuera de rejilla) — la misma cuenta que la columna «avisos» de Qué dijo cada "
                 "test, sumada. No todas se listan en Avisos: las que no son un problema real "
                 "quedan fuera de esa lista, pero siguen contando aquí."]}


def tab(record: dict, cfg: dict) -> dict:
    """The whole opening tab. Equity is second (§4.4, owner 2026-09-30), right after breadth."""
    rows, base = pd.DataFrame(record["rows"]), record["base"]
    note = ("Sin operaciones en " + ", ".join(record["missing"]) + ": la estrategia no llegó a "
            "disparar ahí. Es un resultado sobre la estrategia, no un dato que falte. "
            if record["missing"] else "")
    return envelope.tab("overview", "Backtest", [
        breadth(record["summary"]), equity(record, cfg), master(rows, base),
        equal_risk(rows, base, cfg["equity"]["risk_target_dd"]),
        correlation(record["correlation"]),
        joint_null(record["joint"], cfg["diagnostics"]["alpha"]), tests(rows),
        evidence(rows, base)],
        note=note + "Lo que hicieron los backtests reales, antes de ninguna simulación. Cada "
                    "test tiene su propia pestaña; aquí sólo está su resultado. Las "
                    "comprobaciones mecánicas se siguen calculando pero ya no se listan aquí: "
                    "solo generan un aviso cuando alguna falla de verdad (fill_mismatch).")
