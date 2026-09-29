"""The tab the study opens on: what every market's real backtest did, before any simulation."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.transfer.crossmarket.contract import shared, words
from studies.transfer.crossmarket.simulate import joint, metrics

STATS = ("net", "return_pct", "dd", "dd_pct", "ret_dd", "sharpe", "pf", "losing_run")


def _stats(real: dict) -> list[float]:
    """The eight statistics of one backtest, shares in per cent."""
    return [real[k] * (100 if k.endswith("_pct") else 1) for k in STATS]


def master(rows: pd.DataFrame, base: dict) -> dict:
    """Every market's backtest at face value, the base asset last and marked as reference."""
    body = [[r.feed, *_stats(r.real), int(r.trades_all), int(r.trades)]
            for r in rows.itertuples()]
    body.append([f"{base['feed']} (activo base, referencia)", *_stats(base["real"]),
                 base["trades_all"], base["trades"]])
    return blocks.table("El backtest de cada mercado", pd.DataFrame(
        body, columns=["mercado", *[metrics.LABELS[k] for k in STATS],
                       "operaciones (SQX)", "usables en los tests"]),
        "Estadísticos de SQX sobre todas las operaciones, así que cuadran con la databank. "
        "«Usables» son las que ocupan al menos una vela: sin intervalo no se pueden desplazar, "
        "emparejar ni contar como exposición. En el activo base cada número es producto de la "
        "búsqueda: dice que el código funciona, nada de la estrategia.")


def equal_risk(rows: pd.DataFrame, base: dict, target: float) -> dict:
    """Each market's return once every one is sized to the same worst drawdown."""
    body = [[r.feed, r.equalised["factor"], r.equalised["return_pct"], r.real["ret_dd"],
             r.real["dd_pct"] * 100] for r in rows.itertuples()]
    body.append([f"{base['feed']} (base)", base["equalised"]["factor"],
                 base["equalised"]["return_pct"], base["real"]["ret_dd"],
                 base["real"]["dd_pct"] * 100])
    return blocks.table("A riesgo igualado", pd.DataFrame(
        body, columns=["mercado", "factor de tamaño", f"retorno (%) con DD = {target:.0%}",
                       "Ret/DD", "DD real (%)"]),
        f"El tamaño de cada mercado se multiplica hasta que su peor caída es el {target:.0%} "
        f"de la cuenta: un mercado que gana el doble sufriendo el triple no lo hizo mejor. El "
        f"peor drawdown es un solo momento; léelo junto al Ret/DD.")


def equity(record: dict, cfg: dict) -> dict:
    """Every market's equity in its own account, on one calendar axis."""
    dates, placed = shared.on_axis(record["equity"], "pct")
    series = [{"label": feed, "values": values,
               "role": "reference" if feed == record["base"]["feed"] else "real"}
              for feed, values in placed.items()]
    return {"kind": "lines", "title": "Equity de cada mercado, en su propia cuenta",
            "unit": "%", "x": dates, "series": series,
            "note": f"Cada mercado con su propia cuenta de {cfg['equity']['starting']:,.0f} $; "
                    f"eje vertical en % de esa cuenta; un backtest que empieza más tarde "
                    f"empieza más tarde en el gráfico."}


def correlation(corr: dict) -> dict:
    """The weekly-equity correlation matrix, base asset included, on a discrete scale."""
    names = list(corr)
    return {"kind": "grid", "title": "Correlación de las equities semanales", "rows": names,
            "cols": names, "values": [[corr[r][c] for c in names] for r in names],
            "scale": "diverging", "levels": [-0.6, -0.4, -0.2, -0.05, 0.05, 0.2, 0.4, 0.6],
            "labels": None,
            "note": "De retornos semanales de cada curva, no de sus métricas. Dos mercados a "
                    "0,8 no son dos confirmaciones: son una apuesta mirada dos veces."}


def joint_null(view: dict, alpha: float) -> dict:
    """The joint null as one a-priori number, or why there is none."""
    names = ", ".join(view["markets"]) or "ninguno"
    if view["reason"]:
        return blocks.table("El nulo conjunto", pd.DataFrame(
            [["sin p conjunto", joint.REASONS[view["reason"]]], ["mercados", names]],
            columns=["", ""]))
    return blocks.table("¿Se traslada? El nulo conjunto", pd.DataFrame(
        [["p conjunto", view["p"]], ["z del conjunto", view["z"]],
         ["estadístico real agrupado", view["observed"]],
         ["mediana del nulo conjunto", view["median"]],
         ["sorteos conjuntos batidos", view["beats"]], ["mercados", names]],
        columns=["", "valor"]),
        f"Un solo estadístico decidido de antemano — la media de mean_r, un voto por mercado — "
        f"contra {view['draws']:,} sorteos en los que el mismo desplazamiento de calendario "
        f"se aplica a todos los mercados a la vez, así que la dependencia entre ellos ya va "
        f"dentro. No combina los p por mercado. El activo base no entra. Modelo "
        f"{view['model']}, agregación {view['pool']}, criterio {alpha:.2f}.")


def tests(rows: pd.DataFrame) -> dict:
    """Every test's result per market, as numbers rather than a verdict."""
    return blocks.table("Qué dijo cada test", pd.DataFrame(
        [[r.feed, r.p, r.z, r.edge_r, r.paired_p, r.paired_usd_total, r.risk_normalised,
          len(r.warnings)] for r in rows.itertuples()],
        columns=["mercado", "p (1a)", "z (1a)", "ventaja (ATR)", "p (1b)",
                 "alfa 1b acumulado (USD)", "A / unidad (1c)", "avisos"]),
        "z es la distancia al nulo en unidades de su propia anchura: compara mercados donde "
        "el p ya no puede. No se convierte en ningún p normal.")


def evidence(rows: pd.DataFrame, base: dict) -> dict:
    """Sharpe, the track record its shape demands (MinTRL), and the bootstrap intervals."""
    entries = [(r.feed, r._asdict()) for r in rows.itertuples()]
    entries.append((f"{base['feed']} (base)", base))
    return blocks.table("Qué sostiene esos números", pd.DataFrame(
        [[f, r["sharpe"], int(r["trades"]), r["min_track_benchmark"], r["min_track_needed"],
          bool(r["min_track_enough"]), r["pf"], r["pf_ci_lo"], r["pf_ci_hi"], r["expectancy"],
          r["expectancy_ci_lo"], r["expectancy_ci_hi"]] for f, r in entries],
        columns=["mercado", "Sharpe / operación", "operaciones usables",
                 "Sharpe de referencia", "necesarias (MinTRL)",
                 "¿suficientes?", "PF", "PF CI 5 %", "PF CI 95 %", "expectancy",
                 "exp. CI 5 %", "exp. CI 95 %"]),
        "MinTRL: cuántas operaciones harían falta para que este Sharpe se distinga del de "
        "referencia, dados su sesgo y sus colas. La referencia ya no es cero: es el Sharpe de "
        "un operador aleatorio con la misma huella de mercado (misma ocupación de barras, "
        "mismo coste) -- casi siempre negativo, porque el coste supera lo que esa ocupación "
        "capta de la deriva del mercado. Compárese con «coste de equilibrio» (breakeven) en "
        "la pestaña de estrés: ambos preguntan lo mismo -- cuánta ventaja hace falta antes de "
        "que el coste se la coma -- desde direcciones distintas. Y recuérdese que este Sharpe "
        "premia ser más tranquilo que el azar aunque no gane más en neto: los dos p-valores "
        "pueden discrepar sin que el estudio se contradiga.")


def exits(rows: pd.DataFrame) -> dict:
    """How each market's trades ended, and how much of the money each way of ending holds."""
    body = [[r.feed, e["exit"], e["trades"], e["share"], e["net"], e["gross_share"],
             bool(e["reproducible"])] for r in rows.itertuples() for e in r.exits]
    share = "; ".join(f"{r.feed} {r.reproducible_pnl:.1%}" for r in rows.itertuples())
    return blocks.table("Por dónde salieron las operaciones", pd.DataFrame(
        body, columns=["mercado", "salida", "operaciones", "% de operaciones", "P/L neto",
                       "% del P/L bruto", "¿la reproduce el nulo?"]),
        f"P/L bruto que sale de salidas que el nulo reproduce (tope de barras, cierre de "
        f"viernes): {share}. El resto descansa en la salida por señal, y para esa parte el p "
        f"es un test conjunto de entrada y salida.")


def diagnostics(rows: pd.DataFrame) -> dict:
    """Every mechanical check, one column per market, with what each value should be."""
    feeds = list(rows.feed.unique())
    body = [[label, *[rows.loc[rows.feed == f, key].iloc[0] for f in feeds], expect]
            for key, label, expect in words.DIAGNOSTICS]
    return blocks.table("Comprobaciones mecánicas", pd.DataFrame(
        [[str(v) if isinstance(v, str) else v for v in row] for row in body],
        columns=["comprobación", *feeds, "qué se espera"]))


def breadth(summary: dict) -> dict:
    """Breadth, the worst market and the dispersion, the strategy's headline facts."""
    w = summary["worst_market"]
    return blocks.table("La estrategia en una tabla", pd.DataFrame(
        [["mercados con CI de expectancy > 0", f"{summary['cleared']}/{summary['markets']}"],
         ["peor PF", f"{w['pf']:.2f} en {w['market']}"],
         ["CV de PF entre mercados", f"{summary['pf_cv']:.2f}"],
         ["mercados bajo alpha (1a)", f"{summary['under_alpha']}/{summary['markets']}"],
         ["mercados bajo alpha (1b)", f"{summary['paired_under_alpha']}/{summary['markets']}"],
         ["qué se está probando", summary["family"]],
         ["avisos en total", str(summary["warnings"])]], columns=["", "valor"]))


def tab(record: dict, cfg: dict) -> dict:
    """The whole opening tab."""
    rows, base = pd.DataFrame(record["rows"]), record["base"]
    note = ("Sin operaciones en " + ", ".join(record["missing"]) + ": la estrategia no llegó a "
            "disparar ahí. Es un resultado sobre la estrategia, no un dato que falte. "
            if record["missing"] else "")
    return envelope.tab("overview", "Backtest", [
        breadth(record["summary"]), master(rows, base),
        equal_risk(rows, base, cfg["equity"]["risk_target_dd"]), equity(record, cfg),
        correlation(record["correlation"]),
        joint_null(record["joint"], cfg["diagnostics"]["alpha"]), tests(rows),
        evidence(rows, base), exits(rows), diagnostics(rows)],
        note=note + "Lo que hicieron los backtests reales, antes de ninguna simulación. Cada "
                    "test tiene su propia pestaña; aquí sólo está su resultado.")
