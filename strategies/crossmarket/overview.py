"""The main tab's tables: what every market's backtest really did, at face value and at equal
risk, with the evidence its sample size can hold up.

Nothing here is simulated. These are SQX's own trades, priced as SQX priced them; the tests
that compare them against something live in their own tabs."""

import pandas as pd

from strategies.crossmarket import charts, metrics

# The statistics of the real backtest, in the order a reader of any report expects them.
COLUMNS = [("net", "$"), ("return_pct", "%"), ("dd", "$"), ("dd_pct", "%"),
           ("ret_dd", ""), ("sharpe", ""), ("pf", ""), ("losing_run", "ops")]


def _row(cells: list[str], tag: str = "td", cls: str = "") -> str:
    """One table row, numbers right-aligned. Same convention as panel._row()."""
    first, rest = cells[0], cells[1:]
    attr = f' class="{cls}"' if cls else ""
    return (f"<tr{attr}><{tag}>{first}</{tag}>"
            + "".join(f'<{tag} class="n">{c}</{tag}>' for c in rest) + "</tr>")


def _cells(stats: dict) -> list[str]:
    """The eight statistics of one backtest, formatted for a table cell each."""
    out = []
    for key, unit in COLUMNS:
        value = stats[key] * (100 if key.endswith("_pct") else 1)
        out.append(charts.num(value) + (f" {unit}" if unit == "%" else ""))
    return out


def _usable(kept: int, dropped: int) -> str:
    """The trade count the tests could use, marked when it is short of what SQX reported."""
    return (f"{int(kept):,}" if not dropped
            else f'{int(kept):,} <span class="no">(−{int(dropped)})</span>')


def dropped_note(rows: pd.DataFrame, base: dict) -> str:
    """Why the two trade counts differ, when they do.

    Args:
        rows: Per-market rows carrying dropped and dropped_pnl.
        base: The record's `base` entry, carrying the same.

    Returns:
        A note, or nothing when every trade landed on the grid. The left-hand statistics are
        SQX's own over **every** trade; the tests run on the ones that occupy at least one
        bar, because a trade with no interval cannot be moved, matched to a window of its own
        length or counted as exposure.
    """
    entries = [(r.feed, r.dropped, r.dropped_pnl) for r in rows.itertuples()]
    entries.append((base["feed"], base["dropped"], base["dropped_pnl"]))
    short = [(f, d, p) for f, d, p in entries if d]
    if not short:
        return ""
    detail = ", ".join(f"<code>{f}</code> {d} ({p:+,.0f} $)" for f, d, p in short)
    return ('<div class="note"><b>Las dos columnas de operaciones no coinciden, y eso es '
            'correcto.</b> Los estadísticos de la izquierda son los de SQX sobre <b>todas</b> '
            'las operaciones, así que el beneficio neto y la caída de esta tabla cuadran con '
            'la databank. Los tests corren sobre las que ocupan al menos una vela: una '
            'operación que abre y cierra dentro de la misma vela no tiene intervalo que '
            'mover, ni ventana ciega de su misma duración contra la que compararse, ni '
            'exposición que medir. Casi todas son salidas <code>Exit Signal</code> de '
            f'duración <code>0s</code>. Aquí: {detail}.</div>')


def master(rows: pd.DataFrame, base: dict, colours: dict[str, str]) -> str:
    """Every market's real backtest, with the base asset shown apart as the reference.

    Args:
        rows: Per-market rows carrying `real` and `trades`.
        base: The record's `base` entry, carrying the same.
        colours: {feed: colour}, so the dot beside a market matches its curve.

    Returns:
        A scrollable table. The base asset is the last row and marked: on the market a
        strategy was fitted on, every one of these numbers is the product of the search that
        produced it, so it says the code works and nothing about the strategy.

        The statistics are SQX's own over **every** trade it reported, so they reconcile with
        the databank; the second count is how many of those the tests could place on the bar
        grid, and dropped_note() says why they differ when they do.
    """
    head = _row(["mercado", *[metrics.LABELS[k] for k, _ in COLUMNS], "operaciones (SQX)",
                 "usables en los tests"], "th")
    body = []
    for r in rows.itertuples():
        dot = f'<i class="dot" style="background:{colours.get(r.feed, "")}"></i>'
        body.append(_row([f'{dot}<code>{r.feed}</code>', *_cells(r.real),
                          f"{int(r.trades_all):,}", _usable(r.trades, r.dropped)]))
    dot = f'<i class="dot" style="background:{colours.get(base["feed"], "")}"></i>'
    body.append(_row([f'{dot}<code>{base["feed"]}</code> <span class="tagline">activo base '
                      f'· referencia, no evidencia</span>', *_cells(base["real"]),
                      f'{base["trades_all"]:,}',
                      _usable(base["trades"], base["dropped"])], cls="basis"))
    return (f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'
            + dropped_note(rows, base))


def equal_risk(rows: pd.DataFrame, base: dict, target: float) -> str:
    """What each market returned once every one of them risks the same.

    Args:
        rows: Per-market rows carrying `equalised` and `real`.
        base: The record's `base` entry.
        target: equity.risk_target_dd, as a fraction of the account.

    Returns:
        A scrollable table and the paragraph that says how to read it. Position size is
        multiplied so that the worst drawdown of each sample is exactly `target` of the
        account; the return moves by the same factor, because the sizing inside a backtest is
        fixed per trade and the curve therefore scales linearly.
    """
    head = _row(["mercado", "factor de tamaño", f"retorno con DD = {target:.0%}", "Ret/DD",
                 "DD real"], "th")
    entries = [(r.feed, r.equalised, r.real, "") for r in rows.itertuples()]
    entries.append((base["feed"], base["equalised"], base["real"], " (base)"))
    body = [_row([f"<code>{feed}</code>{tag}", f"{eq['factor']:.2f}x",
                  f"{eq['return_pct']:+,.1f} %", f"{real['ret_dd']:.2f}",
                  f"{real['dd_pct'] * 100:.1f} %"])
            for feed, eq, real, tag in entries]
    note = ('<p class="lede"><b>Por qué esta tabla.</b> Un mercado que gana el doble '
            'sufriendo el triple no lo hizo mejor: arriesgó más. Aquí se multiplica el '
            f'tamaño de posición de cada uno hasta que su peor caída es exactamente el '
            f'{target:.0%} de la cuenta, y el retorno se multiplica por ese mismo factor.<br>'
            '<b>Su punto débil.</b> El peor drawdown es <i>un</i> momento de la muestra, así '
            'que este número es ruidoso: léelo junto al <b>Ret/DD</b>, que usa los mismos dos '
            'números sin depender del tamaño de cuenta.</p>')
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>{note}'


def evidence(rows: pd.DataFrame, base: dict) -> str:
    """Sharpe, the track record its own shape demands, and the bootstrap CIs.

    Args:
        rows: Per-market rows carrying sharpe, trades, min_track_*, pf and expectancy CIs.
        base: The record's `base` entry, shown last as the reference.

    Returns:
        A scrollable table. MinTRL is Bailey / Lopez de Prado: given this Sharpe, this skew
        and this kurtosis, how many trades it would take for the Sharpe to be distinguishable
        from zero. It excludes nothing — it says what this sample can and cannot hold up.

        Every column here is computed on the trades the bar grid could hold, because all of
        them are built from returns repriced from the bars. That is the count shown, and it
        is the smaller of the two in the master table above.
    """
    head = _row(["mercado", "sharpe / operación", "operaciones usables",
                 "necesarias (MinTRL)",
                 "¿suficientes?", "PF (CI 90%)", "expectancy (CI 90%)"], "th")
    entries = [(r.feed, r._asdict(), "") for r in rows.itertuples()]
    entries.append((base["feed"], base, " (base)"))
    body = []
    for feed, r, tag in entries:
        enough = ('<span class="ok">sí</span>' if r["min_track_enough"]
                  else '<span class="no">no</span>')
        body.append(_row([f"<code>{feed}</code>{tag}", f"{r['sharpe']:.3f}",
                          f"{int(r['trades']):,}", f"{r['min_track_needed']:,.0f}", enough,
                          f"{r['pf']:.2f} [{r['pf_ci_lo']:.2f}, {r['pf_ci_hi']:.2f}]",
                          f"{r['expectancy']:+.2e} [{r['expectancy_ci_lo']:+.2e}, "
                          f"{r['expectancy_ci_hi']:+.2e}]"]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def tests(rows: pd.DataFrame, alpha: float) -> str:
    """The result of every test, one line per market, as numbers rather than a verdict.

    Args:
        rows: Per-market rows after every test has written into it.
        alpha: The level p-values are coloured against; it decides nothing.

    Returns:
        A scrollable table: the headline null's p and z (1a), the paired test's p and its
        alpha in dollars (1b), the drift-neutral excess and its risk-normalised form (1c),
        and how many reasons there are to distrust the row. z is (real − mean of the null) in
        units of the null's own standard deviation: p saturates at the resolution on the best
        markets and the null is wider where there are fewer trades, so two markets' p-values
        are not comparable as effect sizes and their z is. It is **not** turned into a
        normal-tail p anywhere — that tail does not hold for drawdown or the losing run, and
        the exact empirical p is already the test.
    """
    head = _row(["mercado", "p (1a)", "z (1a)", "ventaja (ATR)", "p (1b)",
                 "alfa 1b acumulado", "A / unidad (1c)", "avisos"], "th")
    body = []
    for r in rows.itertuples():
        flag = ('<span class="ok">ninguno</span>' if not r.warnings
                else f'<span class="no">{len(r.warnings)}</span>')
        body.append(_row([f"<code>{r.feed}</code>",
                          f'<span class="{"ok" if r.p <= alpha else ""}">{r.p:.4f}</span>',
                          f"{r.z:+.2f}",
                          f"{r.edge_r:+.3f}",
                          f'<span class="{"ok" if r.paired_p <= alpha else ""}">'
                          f"{r.paired_p:.4f}</span>",
                          f"{r.paired_usd_total:+,.0f} $", f"{r.risk_normalised:+.3f}", flag]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def breadth_block(summary: dict) -> str:
    """Breadth, worst-market floor and PF dispersion for one strategy.

    Args:
        summary: What breadth.summary() returned, or {} when no market was testable.

    Returns:
        A stat-tile block, or a note when there was nothing to summarise.
    """
    if not summary:
        return '<div class="note">Sin mercados evaluables: no hay nada que resumir.</div>'
    worst = summary["worst_market"]
    tiles = [(f'{summary["cleared"]}/{summary["markets"]}',
              "mercados con CI de expectancy &gt; 0"),
             (f'{worst["pf"]:.2f}', f'peor PF, en {worst["market"]}'),
             (f'{summary["pf_cv"]:.2f}', "CV de PF entre mercados"),
             (f'{summary["under_alpha"]}/{summary["markets"]}', "mercados bajo alpha (1a)"),
             (f'{summary["paired_under_alpha"]}/{summary["markets"]}',
              "mercados bajo alpha (1b)"),
             (summary["family"], "qué se está probando"),
             (str(summary["warnings"]), "avisos en total")]
    return ('<div class="headline">'
            + "".join(f'<div class="stat"><b>{value}</b><span>{label}</span></div>'
                      for value, label in tiles) + "</div>")
