"""One strategy's page: the verdict, what failed, and every family underneath it."""

from strategies.monteCarlo import charts, confidence, familypage, panel, scoring, text

GLANCE = (("net", "beneficio neto"), ("sharpe", "Sharpe por operación"),
          ("dd_pct", "drawdown máximo"), ("ret_dd", "Ret/DD"),
          ("losing_run", "racha perdedora"))


def header(result: dict, verdict: dict) -> str:
    """The verdict, the composite, and what fired, before anything else.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.

    Returns:
        The headline block. The composite is struck through when a gate fired: it is kept
        as a reference and marked as one, so nobody reads it as the answer.
    """
    vetoed = verdict["tier"] in scoring.VERDICTS[3:]
    shown = (f"<s>{verdict['composite']:.0f}</s>" if vetoed
             else f"{verdict['composite']:.0f}")
    return (f'<div class="headline">'
            f'<div class="stat"><b><span class="tier {"no" if vetoed else "pass"}">'
            f'{verdict["tier"]}</span></b><span>veredicto</span></div>'
            f'<div class="stat"><b>{shown}</b><span>compuesto sobre 100</span></div>'
            f'<div class="stat"><b>{sum(1 for f in verdict["flags"] if f["gate"])}</b>'
            f'<span>vetos disparados</span></div>'
            f'<div class="stat"><b>{result["n_trades"]:,}</b><span>operaciones</span></div>'
            f'</div><div class="note">{text.rationale(result, verdict)}</div>')


def failed(verdict: dict) -> str:
    """Every check that failed, in plain language, with its own number.

    Args:
        verdict: What scoring.verdict() returned.

    Returns:
        The failed-tests block, vetoes first. When nothing failed it says so rather than
        disappearing, because an absent section reads as a section that was not run.
    """
    fired = sorted(verdict["flags"], key=lambda f: not f["gate"])
    if not fired:
        return '<div class="note">Ninguna prueba falló ni levantó aviso.</div>'
    return "".join(
        f'<div class="{"fail" if f["gate"] else "note"}">'
        f'<b>{"VETO" if f["gate"] else "aviso"} · familia {f["family"]} · {f["test"]}</b> — '
        f'{text.sentence(f)}</div>' for f in fired)


def glance(result: dict, verdict: dict, cfg: dict) -> str:
    """The backtest against the median simulation, one line per statistic.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The at-a-glance table, each row carrying its own sample-size confidence.
    """
    runs = result["B"]["runs"]
    baseline = runs[next(iter(runs))]
    rows = []
    for key, label in GLANCE:
        s = baseline[key]
        rows.append([label, familypage.fmt(key, s["observed"]),
                     familypage.fmt(key, s["median"]),
                     familypage.fmt(key, s["p"][5]), f"{s['rank']:.0%}",
                     confidence.percentile(result["n_trades"], 5)])
    extra = [["inflación del drawdown", f"{result['A']['inflation']:.2f}×", "—", "—", "—",
              verdict["tiers"]["dd_95"]],
             ["PSR", f"{result['E']['psr']:.4f}", "—", "—", "—",
              confidence.average(result["n_trades"])]]
    return panel.table(["", "backtest", "mediana simulada", "percentil 5",
                        "rango del backtest", "confianza"], rows + extra)


def charts_scores(verdict: dict, cfg: dict) -> str:
    """The five sub-scores as bars, with what each one is built from.

    Args:
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The figure and the list of ingredients beside it.
    """
    items = "".join(f"<li><b>{k}</b> — {v}</li>" for k, v in scoring.BUILT_FROM.items())
    return (charts.scores(verdict["subscores"], cfg["scoring"]["tiers"])
            + f"<ul>{items}</ul>")


def page(result: dict, verdict: dict, band: dict, cfg: dict, source: dict) -> str:
    """The whole report for one strategy, in reading order.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        band: What fan.envelope() returned for the headline model.
        cfg: What config.load() returned.
        source: Export paths and the asset's cost values, for the appendix.

    Returns:
        A self-contained page. Verdict first, then what failed, then the numbers: a page
        that opens with figures invites the reader to believe the figures.
    """
    overlap = ('<div class="note"><b>Operaciones solapadas.</b> El '
               f'{result["overlap"]:.0%} de las operaciones estaban abiertas a la vez que la '
               'anterior. La curva sumada sigue valiendo, pero las rachas y el orden significan '
               'algo distinto que en una estrategia sola.</div>'
               if result["overlap"] > 0.01 else "")
    return panel.render(f"Monte Carlo — {result['name']}", [
        f"<h1>{result['name']}</h1>",
        '<p class="lede">Robustez de una estrategia ya aceptada: cuánto de este resultado es '
        'suerte, y de qué tipo.</p>',
        header(result, verdict), overlap,
        "<h2>Lo que falló</h2>", failed(verdict),
        "<h2>De un vistazo</h2>",
        '<p class="lede">El backtest contra la mediana de las simulaciones. La columna «rango» '
        'dice qué fracción de las simulaciones quedó por debajo del backtest: cerca del 100% es '
        'un backtest afortunado.</p>',
        glance(result, verdict, cfg),
        charts_scores(verdict, cfg),
        *familypage.family_a(result, band, cfg),
        *familypage.family_b(result, cfg),
        *familypage.family_c(result, cfg),
        *familypage.family_d(result, cfg),
        *familypage.family_e(result, cfg),
        "<h2>Datos y método</h2>",
        panel.method(source["args"], cfg, source["stability"], source),
        panel.limits(cfg),
        f'<footer>{result["name"]} · generado por '
        f'<code>strategies.monteCarlo.report</code> · sin semilla</footer>'])
