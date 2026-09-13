"""The panel's content, rendered by the same functions that write the report file."""

from strategies.monteCarlo import charts, familypage, panel, strategypage

FAMILIES = {"A": lambda r, v, b, c: familypage.family_a(r, v, b, c),
            "B": lambda r, v, b, c: familypage.family_b(r, v, c),
            "C": lambda r, v, b, c: familypage.family_c(r, v, c),
            "D": lambda r, v, b, c: familypage.family_d(r, v, c),
            "E": lambda r, v, b, c: familypage.family_e(r, v, c)}
UNITS = {"net": "Beneficio neto de la simulación, en $", "return_pct": "Retorno",
         "dd": "Drawdown máximo, en $", "dd_pct": "Drawdown, como % de la cuenta",
         "ret_dd": "Beneficio entre drawdown", "sharpe": "Sharpe por operación",
         "pf": "Profit factor", "losing_run": "Operaciones perdedoras seguidas"}
PCT = {"dd_pct", "return_pct"}


def verdict_block(result: dict, verdict: dict, cfg: dict) -> str:
    """The headline: tier, what failed, the at-a-glance table and the sub-scores.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The same blocks the report opens with, so the panel and the file cannot disagree.
    """
    return "".join([strategypage.header(result, verdict),
                    "<h2>Lo que falló</h2>", strategypage.failed(verdict),
                    "<h2>De un vistazo</h2>",
                    strategypage.glance(result, verdict, cfg),
                    strategypage.charts_scores(verdict, cfg)])


def family(name: str, result: dict, verdict: dict, band: dict, cfg: dict) -> str:
    """One family's whole section.

    Args:
        name: "A" to "E".
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        band: What fan.envelope() returned, used by Family A.
        cfg: What config.load() returned.

    Returns:
        The section's HTML.
    """
    return "".join(FAMILIES[name](result, verdict, band, cfg))


def runs(result: dict) -> list[dict]:
    """Every sub-test whose distribution the panel can draw.

    Args:
        result: What run.analyse() returned.

    Returns:
        One entry per sub-run with its label, its name and which family it belongs to.
        Families A and B are the reordering and resampling sweeps; C is the four execution
        stresses, whose names are their own.
    """
    out = []
    for group in ("A", "B"):
        out += [{"label": k, "title": result["titles"][k], "family": group}
                for k in result[group]["shapes"]]
    out += [{"label": k, "title": familypage.MODELS_ES[k], "family": "C"}
            for k in result["C"]]
    return out


def _find(result: dict, label: str) -> tuple[dict, dict]:
    """Where one sub-run's histogram and percentile table are kept.

    Args:
        result: What run.analyse() returned.
        label: A label from runs().

    Returns:
        (shapes by statistic, percentile table by statistic).
    """
    for group in ("A", "B"):
        if label in result[group]["shapes"]:
            return result[group]["shapes"][label], result[group]["runs"][label]
    return result["C"][label]["shapes"], result["C"][label]["table"]


def figure(result: dict, label: str, metric: str, title: str, band: dict | None = None) -> str:
    """One sub-run's distribution of one statistic, with its percentiles underneath.

    Args:
        result: What run.analyse() returned.
        label: A label from runs().
        metric: Key of metrics.NAMES.
        title: The sub-run's readable name.
        band: What work.band_for() returned for this label, or None to skip the cone —
            an ad-hoc re-run has no stream handy to compute one from.

    Returns:
        The figure and the table. Every simulated number the study produced is reachable
        this way, one pair of dropdowns at a time, instead of as forty figures at once.
    """
    shapes, tables = _find(result, label)
    got = tables[metric]
    rank = (f"El backtest queda por encima del {got['rank']:.0%} de las simulaciones."
            if metric != "dd_pct" else
            f"El backtest tuvo un drawdown mayor que el {got['rank']:.0%} de las "
            f"simulaciones.")
    body = [[f"Percentil {q}", familypage.fmt(metric, v)] for q, v in got["p"].items()]
    body += [["Media", familypage.fmt(metric, got["mean"])],
             ["Mediana", familypage.fmt(metric, got["median"])],
             ["Desviación estándar", familypage.fmt(metric, got["std"])],
             ["Curtosis (exceso)", f"{got['kurtosis']:.2f}"],
             ["Backtest", familypage.fmt(metric, got["observed"])],
             ["Simulaciones utilizables", f"{got['n']:,}"]]
    flat = ('<div class="note"><b>Esta prueba conserva este estadístico por '
            'construcción.</b> Reordenar las mismas operaciones no puede cambiarlo, así que '
            'la distribución es un solo valor. Es la comprobación de que el modelo hace lo '
            'que dice: mira el drawdown o la racha, que sí se mueven.</div>'
            if got["p"][min(got["p"])] == got["p"][max(got["p"])] else "")
    fig = charts.distribution(shapes[metric], f"{title} — {familypage.LABELS[metric]}",
                              rank, UNITS[metric], pct=metric in PCT)
    cone = (charts.cone(band, f"{title} — curva de equity",
                        "bandas 5-95 y 25-75 · línea naranja: el backtest") if band else "")
    return (f'<div class="figure-row">{fig}'
            f'{panel.table(["Qué", "Valor"], body)}</div>{flat}{cone}')
