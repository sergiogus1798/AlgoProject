"""Turns a result into the words the owner reads. Pure text: it computes nothing."""

import argparse

import pandas as pd

from strategies.monteCarlo import gates, scoring, stress

# One sentence per check that can fire, with the number that fired it. Written so that the
# sentence alone says what to do about it.
FLAGS = {
    "dd_99": "El drawdown del percentil 99 es {value:.1%} de la cuenta, por encima del techo "
             "de supervivencia {limit:.0%}. Con este riesgo por operación la cuenta no aguanta "
             "la peor de cien reordenaciones.",
    "inflation": "El drawdown del backtest fue afortunado: reordenando las mismas operaciones "
                 "sale {value:.1f} veces mayor (límite {limit:.0f}).",
    "inflation_watch": "El drawdown reordenado es {value:.1f} veces el del backtest; por encima "
                       "de {limit:.1f} conviene vigilarlo, no descartarlo.",
    "net_5": "En 1 de cada 20 remuestreos el beneficio es {value:,.0f} $, es decir negativo: "
             "el resultado depende de qué operaciones salieron.",
    "pf_5": "El profit factor del percentil 5 es {value:.2f}, por debajo de {limit:.2f}.",
    "outlier": "La mejor operación aporta el {value:.0%} del beneficio (límite {limit:.0%}). "
               "Mira las mayores ganadoras antes de creerte el total.",
    "oos_red": "El Sharpe mediano fuera de muestra es el {value:.0%} del de dentro. Eso es "
               "optimismo que el test de decaimiento no recogió.",
    "oos_amber": "El Sharpe fuera de muestra cae al {value:.0%} del de dentro (aviso por debajo "
                 "de {limit:.0%}).",
    "skip": "Perdiendo entradas al azar el beneficio queda en el {value:.0%} del real, por "
            "debajo del {limit:.0%} exigido.",
    "fill_degrade": "Con ejecuciones peores el beneficio queda en el {value:.0%} del real "
                    "(mínimo {limit:.0%}).",
    "cost_shock": "Con costes hasta el doble, el profit factor del percentil 5 baja a "
                  "{value:.2f} (mínimo {limit:.2f}).",
    "spread_widen": "Con un spread más ancho el profit factor del percentil 5 baja a "
                    "{value:.2f} (mínimo {limit:.2f}).",
    "high_vol": "En el tercil de volatilidad alta la mediana remuestreada es {value:,.0f} $: "
                "el sistema no gana en el régimen que más le va a tocar.",
    "dead_block": "Hay un bloque de 24 meses con mediana negativa ({value:,.0f} $): un periodo "
                  "entero en el que la estrategia no funcionó.",
    "windows": "Sólo el {value:.0%} de las ventanas móviles aguanta en positivo en su percentil "
               "5 (se pide {limit:.0%}).",
    "concentration": "El {value:.0%} del beneficio sale de un solo tercil de volatilidad "
                     "(límite {limit:.0%}).",
    "psr": "La PSR es {value:.3f}: con este número de operaciones y esta forma de la "
           "distribución, no se puede descartar que el edge sea cero.",
    "psr_amber": "La PSR es {value:.3f}, por debajo del objetivo {limit:.2f}.",
    "cost_file": "El coste modelado desde assets/ es {value:.2f} veces el que SQX cobró de "
                 "verdad. Las pruebas de la familia C se leen con esa reserva.",
    "sample": "Con {value:.0f} operaciones alguno de los números que deciden no es fiable. "
              "El veredicto se queda en INCONCLUSIVE."}

# What to call a check where it is named rather than explained, e.g. the verdict's failed
# list. Family C reuses stress.TITLES so the name is not typed twice.
TITLES = {**stress.TITLES,
          "dd_99": "Drawdown percentil 99", "inflation": "Drawdown inflado",
          "inflation_watch": "Drawdown inflado (aviso)", "net_5": "Beneficio percentil 5",
          "pf_5": "Profit factor percentil 5", "outlier": "Mejor operación",
          "oos_red": "Caída OOS", "oos_amber": "Caída OOS (aviso)",
          "high_vol": "Volatilidad alta", "dead_block": "Bloque muerto",
          "windows": "Ventanas móviles", "concentration": "Concentración por régimen",
          "psr": "PSR", "psr_amber": "PSR (aviso)", "cost_file": "Coste modelado",
          "sample": "Muestra insuficiente"}


def title(flag: dict) -> str:
    """One fired check's name, for a heading — never the internal key.

    Args:
        flag: What gates.check() produced.

    Returns:
        The Spanish name a reader can act on, e.g. "Ejecuciones degradadas" rather than
        "fill_degrade".
    """
    return TITLES[flag["test"]]


def sentence(flag: dict) -> str:
    """One fired check, in plain language, with its own number inside.

    Args:
        flag: What gates.check() produced.

    Returns:
        The sentence. A failure whose number is not in the sentence is a failure nobody
        can act on.
    """
    return FLAGS[flag["test"]].format(value=flag["value"], limit=flag["limit"])


def rationale(result: dict, verdict: dict) -> str:
    """Why the verdict is what it is, naming the metric that decided it.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.

    Returns:
        Two sentences: the binding constraint with its number, and what would have to
        change. The composite is never the explanation — the constraint is.
    """
    binding = verdict["binding"]
    if binding["gate"]:
        return ("Lo que decide: " + sentence(binding) + " Mientras esa prueba no pase, "
                "el compuesto no significa nada.")
    family = binding["family"]
    return (f"Ninguna prueba veta. Lo que limita la nota es la familia {family} "
            f"({binding['value']:.0f} sobre 100): {scoring.BUILT_FROM[family]}. "
            f"El compuesto es {verdict['composite']:.0f}.")


def row(result: dict, verdict: dict) -> dict:
    """One strategy reduced to the line the databank table and the CSV carry.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.

    Returns:
        A flat dict: verdict, composite, sub-scores and the numbers every gate read.
    """
    return {"strategy": result["name"], "trades": result["n_trades"],
            "tier": verdict["tier"], "composite": verdict["composite"],
            **{f"score_{k}": v for k, v in verdict["subscores"].items()},
            "net": result["observed"]["net"], "dd_pct": result["observed"]["dd_pct"],
            "ret_dd": result["observed"]["ret_dd"],
            "dd_pct_95": result["A"]["dd_pct_95"], "dd_pct_99": result["A"]["dd_pct_99"],
            "inflation": result["A"]["inflation"], "net_5": result["B"]["net_5"],
            "pf_5": result["B"]["pf_5"], "oos_ratio": result["B"]["oos_ratio"],
            "outlier_share": result["B"]["outlier"]["share"],
            "windows_ok": gates.passing(result["D"]["overlapping"]),
            "high_vol_net": result["D"]["regime"]["buckets"]["high"]["median_net"],
            # The 5% severity, for one flat column; the whole curve is in the HTML report.
            "stitched_dd_pct": result["D"]["stitch"][0.05]["dd_pct"], "psr": result["E"]["psr"],
            "gates": sum(1 for f in verdict["flags"] if f["gate"]),
            "flags": sum(1 for f in verdict["flags"] if not f["gate"]),
            "confidence": verdict["tiers"]["worst"]}


def _failure_counts(flags: pd.DataFrame) -> dict:
    """How many strategies each check disqualified.

    Args:
        flags: One row per fired check, over every strategy.

    Returns:
        {check: strategies}, most common first, vetoes before warnings.
    """
    if flags.empty:
        return {}
    return flags[flags.gate].test.value_counts().to_dict()


def markdown(args: argparse.Namespace, rows: pd.DataFrame, flags: pd.DataFrame,
             stab: dict, cfg: dict) -> str:
    """The written conclusion of a whole databank run.

    Args:
        args: Parsed command line.
        rows: One row per strategy, from row().
        flags: One row per fired check, over every strategy.
        stab: What stability.spread() returned for the run's reference strategy.
        cfg: What config.load() returned.

    Returns:
        Markdown. It opens with what did not pass, because a page that opens with an
        average invites the reader to read the average.
    """
    counts = rows.tier.value_counts().to_dict()
    lines = [f"# Monte Carlo — {args.project} / {args.databank}", "",
             f"{len(rows)} estrategias · {cfg['global']['n_sims']:,} simulaciones por prueba · "
             f"export {args.export}", "",
             "## Veredicto", "",
             "| veredicto | estrategias |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in counts.items()]
    survivors = rows[rows.tier.isin(scoring.VERDICTS[:3])]
    lines += ["", f"Pasan sin ningún veto: **{len(survivors)}** de {len(rows)}.", "",
              "## Por qué caen las que caen", ""]
    for test, n in _failure_counts(flags).items():
        lines.append(f"- `{test}` — {n} estrategia" + ("s" if n > 1 else ""))
    lines += ["", "## Estabilidad del propio Monte Carlo", "",
              f"Con {cfg['global']['n_sims']:,} simulaciones y {stab['runs']} repeticiones "
              f"independientes, el número que más se mueve es `{stab['worst']}`, con una "
              f"dispersión del {stab['worst_spread']:.1%} de su media. "
              + ("Es demasiado: sube `n_sims`." if stab["unstable"]
                 else "Por debajo de la tolerancia, así que las cifras que deciden son estables."),
              "", "## Lo que este informe no dice", "",
              "- **No detecta sobreajuste.** Ni DSR ni CSCV: harían falta las estrategias que se "
              "probaron durante la generación, que aquí no están.",
              "- **No valida el edge.** Asume que ya lo tiene y mide de qué depende.",
              "- **El techo de drawdown es un marcador de posición** "
              f"({cfg['scoring']['survival_dd_pct']:.0%}) hasta que estén las reglas de la "
              "prop firm."]
    return "\n".join(lines) + "\n"
