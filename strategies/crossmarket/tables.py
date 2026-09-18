"""Render Tests 1b and 1c, the fingerprint, cost and correlation into HTML tables and figures.
Kept out of panel.py so panel.py stays under CODESTYLE's 250-line cap. Pure rendering, computes
nothing — every number here already exists on the row or in the record it is given."""

from typing import Any

import pandas as pd

from strategies.crossmarket import figures

REFERENCE = {"block": "bloques de 6m"}   # how paired.py's reference keys read on screen


def _row(cells: list[str], tag: str = "td") -> str:
    """One table row, numbers right-aligned. Same convention as panel._row()."""
    first, rest = cells[0], cells[1:]
    return (f"<tr><{tag}>{first}</{tag}>"
            + "".join(f'<{tag} class="n">{c}</{tag}>' for c in rest) + "</tr>")


def _label(r: Any) -> str:
    """The row's first cell: strategy and market when both are present, market alone otherwise."""
    return (f"{r.strategy} · <code>{r.feed}</code>" if hasattr(r, "strategy")
            else f"<code>{r.feed}</code>")


def reference_name(key: Any) -> str:
    """How one of paired.py's reference windows is named on screen.

    Args:
        key: "block", or a half-width in months.

    Returns:
        A short label. A number is a **half**-width, so 3 means every window starting within
        three months either side of the entry — six months of market, centered on it.
    """
    return REFERENCE.get(key, f"centrada ±{key}m")


def exposure_table(rows: pd.DataFrame) -> str:
    """Test 1c: the drift-neutral excess, its risk-normalised form, and E with its interval.

    Args:
        rows: Per-market rows carrying a, a_ci_lo/hi, risk_normalised, e, e_meaningful,
            mu_t and e_ci.

    Returns:
        A scrollable table. **A per unit of risk leads**, because it divides by the market's
        typical bar move, which is never near zero; E follows with a Fieller interval, which
        is the only honest interval for a ratio whose denominator can be zero — where it
        cannot be bounded, the cell says so instead of printing a number that looks decided.
    """
    head = _row(["mercado", "A / unidad de riesgo", "A (exceso por vela)", "CI 90% de A", "E",
                 "CI 90% de E (Fieller)", "deriva (t)", "réplicas con deriva ≤ 0"], "th")
    body = []
    for r in rows.itertuples():
        ci = r.e_ci
        span = ("no acotado" if not ci["bounded"]
                else f'[{ci["lo"]:+.2f}, {ci["hi"]:+.2f}]')
        body.append(_row([_label(r), f"{r.risk_normalised:+.3f}", f"{r.a:+.2e}",
                          f"[{r.a_ci_lo:+.2e}, {r.a_ci_hi:+.2e}]", f"{r.e:+.2f}",
                          span if ci["bounded"] else f'<span class="no">{span}</span>',
                          f"{r.mu_t:+.2f}", f'{ci["sign_flip"]:.1%}']))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def paired_table(rows: pd.DataFrame) -> str:
    """Test 1b: the timing alpha in every unit, with its p and its interval.

    Args:
        rows: Per-market rows carrying paired_* and the unit conversions.

    Returns:
        A scrollable table. The log return the test computes is unreadable on its own — 0,0004
        — so the same number appears in basis points, in per cent, in ATR units and in
        dollars, and the last column is the one to read first: what the timing was worth over
        the whole sample, in money.
    """
    head = _row(["mercado", "alfa (bps)", "alfa (%)", "alfa (R)", "$ / operación",
                 "<b>$ acumulado</b>", "% de operaciones que ganan", "CI 90% (bps)",
                 "p (Wilcoxon)"], "th")
    body = [_row([_label(r), f"{r.paired_bps:+.2f}", f"{r.paired_pct:+.4f}",
                  f"{r.paired_r:+.3f}", f"{r.paired_usd:+,.2f}",
                  f"<b>{r.paired_usd_total:+,.0f}</b>", f"{r.paired_beat:.1%}",
                  f"[{r.paired_ci_lo * 1e4:+.2f}, {r.paired_ci_hi * 1e4:+.2f}]",
                  f"{r.paired_p:.4f}"]) for r in rows.itertuples()]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def sensitivity_table(rows: pd.DataFrame) -> str:
    """Test 1b under every definition of "the same stretch of market", side by side.

    Args:
        rows: Per-market rows carrying paired_sensitivity.

    Returns:
        A scrollable table, one row per market and reference. A p-value that survives all four
        does not depend on how the reference window was defined; one that survives a single
        definition was being carried by it, and that is the finding, not a detail.
    """
    head = _row(["mercado", "referencia", "alfa (bps)", "$ acumulado",
                 "% que ganan", "p (Wilcoxon)"], "th")
    body = []
    for r in rows.itertuples():
        for s in r.paired_sensitivity:
            mark = " ·  <span class='tagline'>la de la tabla</span>" if (
                s["reference"] == r.paired_reference) else ""
            body.append(_row([f"<code>{r.feed}</code>", reference_name(s["reference"]) + mark,
                              f'{s["bps"]:+.2f}', f'{s["usd_total"]:+,.0f}',
                              f'{s["beat_share"]:.1%}', f'{s["p"]:.4f}']))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def fingerprint_table(rows: pd.DataFrame) -> str:
    """Holding-time KS against gold, the excursions, the capture ratio and the return shape.

    Args:
        rows: Per-market rows carrying a `fingerprint` dict, from fingerprint.fingerprint().

    Returns:
        A scrollable table.
    """
    head = _row(["mercado", "KS holds vs. oro (p)", "MAE media (×ATR)", "MFE media (×ATR)",
                 "captura de MFE (mediana)", "skew", "kurtosis", "tail ratio"], "th")
    body = []
    for r in rows.itertuples():
        fp = r.fingerprint
        body.append(_row([_label(r), f"{fp['holding_ks']['p']:.4f}",
                          f"{fp['excursion']['mae']['mean']:.2f}",
                          f"{fp['excursion']['mfe']['mean']:.2f}",
                          f"{fp['capture']['median']:+.3f}",
                          f"{fp['shape']['skew']:+.2f}", f"{fp['shape']['kurtosis']:+.2f}",
                          f"{fp['shape']['tail_ratio']:.2f}"]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def cost_table(rows: pd.DataFrame) -> str:
    """Breakeven cost multiple, and decay under a bar shift or range slippage.

    Args:
        rows: Per-market rows carrying breakeven, bar_shift_decay, slippage_decay.

    Returns:
        A scrollable table.
    """
    head = _row(["mercado", "breakeven (x coste)", "decaimiento 1 vela",
                 "decaimiento slippage 25%"], "th")
    body = []
    for r in rows.itertuples():
        slip = r.slippage_decay.get("0.25", next(iter(r.slippage_decay.values())))
        body.append(_row([_label(r), f"{r.breakeven:.2f}", f"{r.bar_shift_decay:+.1%}",
                          f"{slip:+.1%}"]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def assumptions_table(rows: pd.DataFrame) -> str:
    """What the stress assumed per market, and whether it matches what SQX really charged.

    Args:
        rows: Per-market rows carrying costs and stress_settings.

    Returns:
        A scrollable table. `cobrado` is measured from the export and is the truth; `modelado`
        is what execution.yaml implies. A gap past 25% means that file describes a different
        broker from the one the backtest ran against — a reason to distrust the stress, never
        the backtest.
    """
    head = _row(["mercado", "coste cobrado (mediana $)", "coste modelado ($)", "diferencia",
                 "multiplicador de coste", "profundidad de fill", "origen"], "th")
    body = []
    for r in rows.itertuples():
        c, s = r.costs, r.stress_settings
        gap = "—" if c["modelled"] != c["modelled"] else f'{c["gap"]:+.0%}'
        source = ("sin declarar en execution.yaml" if not c["declared"]
                  else c["source"] + ("" if c["reviewed"]
                                      else ' · <span class="no">sin revisar</span>'))
        body.append(_row([_label(r), f'{c["charged"]:,.2f}',
                          "—" if c["modelled"] != c["modelled"] else f'{c["modelled"]:,.2f}',
                          f'<span class="{"no" if c["diverges"] else ""}">{gap}</span>',
                          f'{s["cost_shock"][0]:.1f}x – {s["cost_shock"][1]:.1f}x',
                          f'{s["fill_depth"]:.0%} de la MAE', source]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def correlation_section(corr: dict) -> str:
    """The correlation heatmap of the markets' weekly equity, the base asset included.

    Args:
        corr: What correlation.correlation_matrix().to_dict() returned.

    Returns:
        One figure. The PCA that used to sit beside it was removed: with two or three streams
        PC1 is close to a function of the mean pairwise correlation and added no axis.
    """
    return figures.heatmap(corr, "Correlación de las equities semanales")


def exits_table(rows: pd.DataFrame) -> str:
    """How each market's real trades ended, and how much of the money each way of ending holds.

    Args:
        rows: Per-market rows carrying `exits` and `reproducible_pnl`.

    Returns:
        One block per market: every `Close type` with its trade count, its share of the
        trades and its share of the gross P&L, and a line saying how much of the result rests
        on an exit the null reproduces. The counts were already on the page; the money was
        not, and it is the number that says how far the entry+exit caveat reaches. A market
        whose signal exits are 16% of the trades but 40% of the profit is not 84% a pure
        entry test.
    """
    head = _row(["salida", "operaciones", "% de operaciones", "P/L neto",
                 "% del P/L bruto", "¿la reproduce el nulo?"], "th")
    out = []
    for r in rows.itertuples():
        body = "".join(_row([e["exit"], f'{e["trades"]:,}', f'{e["share"]:.1%}',
                             f'{e["net"]:+,.0f} $', f'{e["gross_share"]:.1%}',
                             '<span class="ok">sí</span>' if e["reproducible"]
                             else '<span class="no">no</span>']) for e in r.exits)
        out.append(f"<h3><code>{r.feed}</code></h3>"
                   f'<div class="scroll"><table>{head}{body}</table></div>'
                   f'<p class="lede"><b>{r.reproducible_pnl:.1%}</b> del P/L bruto de este '
                   f"mercado sale de operaciones cuya salida el nulo sí reproduce — tope de "
                   f"barras y cierre de viernes. El resto descansa en la salida por señal, "
                   f"que no se puede reproducir sin leer el <code>.sqx</code>: para esa parte "
                   f"el p es un test conjunto de entrada <b>y</b> salida.</p>")
    return "".join(out)
