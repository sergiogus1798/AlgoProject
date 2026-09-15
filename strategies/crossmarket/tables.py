"""Render Test 1c, significance, fingerprint, cost and correlation into HTML tables and figures.
Kept out of panel.py so panel.py stays under CODESTYLE's 250-line cap. Pure rendering, computes
nothing — every number here already exists on the row or in the record it is given."""

from typing import Any

import pandas as pd

from strategies.crossmarket import figures


def _row(cells: list[str], tag: str = "td") -> str:
    """One table row, numbers right-aligned. Same convention as panel._row()."""
    first, rest = cells[0], cells[1:]
    return (f"<tr><{tag}>{first}</{tag}>"
            + "".join(f'<{tag} class="n">{c}</{tag}>' for c in rest) + "</tr>")


def _label(r: Any) -> str:
    """The row's first cell: strategy and market when both are present, market alone otherwise."""
    return (f"{r.strategy} · <code>{r.feed}</code>" if hasattr(r, "strategy")
            else f"<code>{r.feed}</code>")


def exposure_table(rows: pd.DataFrame) -> str:
    """Test 1c: concentration, drift-neutral excess and its CI, risk-normalised A, MFE capture.

    Args:
        rows: Per-market rows carrying e, e_meaningful, mu_t, a, a_ci_lo, a_ci_hi,
            risk_normalised and capture_median.

    Returns:
        A scrollable table, one row per market (and per strategy, when the frame holds more
        than one). E is shown only where the market's own drift is a drift: dividing by a
        mu_m that is statistically zero produced E = -69.4 on Brent, a market whose A was in
        fact the strongest of the three.
    """
    head = _row(["mercado", "E", "deriva del mercado (t)", "A", "IC 90% de A", "A / unidad",
                "captura MFE (mediana)"], "th")
    body = [_row([_label(r),
                 f"{r.e:.2f}" if r.e_meaningful else '<span class="no">no aplica</span>',
                 f"{r.mu_t:+.2f}", f"{r.a:+.2e}",
                 f"[{r.a_ci_lo:+.2e}, {r.a_ci_hi:+.2e}]", f"{r.risk_normalised:+.3f}",
                 f"{r.capture_median:+.3f}"]) for r in rows.itertuples()]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def significance_table(rows: pd.DataFrame) -> str:
    """Sharpe, minimum track-record length, and bootstrap CIs on PF and expectancy.

    Args:
        rows: Per-market rows carrying sharpe, trades, min_track_needed, min_track_enough,
            pf, pf_ci_lo/hi, expectancy, expectancy_ci_lo/hi.

    Returns:
        A scrollable table.
    """
    head = _row(["mercado", "sharpe", "trades", "necesarios (MinTRL)", "suficientes",
                "PF (IC 90%)", "expectancy (IC 90%)"], "th")
    body = []
    for r in rows.itertuples():
        enough = '<span class="ok">sí</span>' if r.min_track_enough else '<span class="no">no</span>'
        body.append(_row([_label(r), f"{r.sharpe:.3f}", str(int(r.trades)),
                          f"{r.min_track_needed:,.0f}", enough,
                          f"{r.pf:.2f} [{r.pf_ci_lo:.2f}, {r.pf_ci_hi:.2f}]",
                          f"{r.expectancy:+.2e} [{r.expectancy_ci_lo:+.2e}, "
                          f"{r.expectancy_ci_hi:+.2e}]"]))
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
    return (f'<div class="headline">'
            f'<div class="stat"><b>{summary["cleared"]}/{summary["markets"]}</b>'
            f'<span>mercados con IC de expectancy &gt; 0</span></div>'
            f'<div class="stat"><b>{worst["pf"]:.2f}</b>'
            f'<span>peor PF, en {worst["market"]}</span></div>'
            f'<div class="stat"><b>{summary["pf_cv"]:.2f}</b>'
            f'<span>CV de PF entre mercados</span></div>'
            f'<div class="stat"><b>{summary["under_alpha"]}/{summary["markets"]}</b>'
            f'<span>mercados bajo alpha (1a)</span></div>'
            f'<div class="stat"><b>{summary["paired_under_alpha"]}/{summary["markets"]}</b>'
            f'<span>mercados bajo alpha (1b pareado)</span></div></div>')


def fingerprint_table(rows: pd.DataFrame) -> str:
    """Holding-time KS against gold, and the shape of the real per-trade returns.

    Args:
        rows: Per-market rows carrying a `fingerprint` dict, from fingerprint.fingerprint().

    Returns:
        A scrollable table.
    """
    head = _row(["mercado", "KS holds vs. oro (p)", "skew", "kurtosis", "tail ratio"], "th")
    body = []
    for r in rows.itertuples():
        fp = r.fingerprint
        body.append(_row([_label(r), f"{fp['holding_ks']['p']:.4f}",
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
    head = _row(["mercado", "breakeven (x coste)", "decaimiento 1 barra",
                "decaimiento slippage 25%"], "th")
    body = []
    for r in rows.itertuples():
        slip = r.slippage_decay.get("0.25", next(iter(r.slippage_decay.values())))
        body.append(_row([_label(r), f"{r.breakeven:.2f}", f"{r.bar_shift_decay:+.1%}",
                          f"{slip:+.1%}"]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def correlation_section(corr: dict, pca: dict) -> str:
    """The correlation heatmap and PCA variance share, for one strategy.

    Args:
        corr: What correlation.correlation_matrix().to_dict() returned.
        pca: What correlation.pca() returned.

    Returns:
        Two figures: the heatmap, and one bar per principal component against the PDF's
        0.70 gate.
    """
    components = [{"market": f"PC{i + 1}", "share": s}
                  for i, s in enumerate(pca["variance_share"])]
    return (figures.heatmap(corr, "Correlación semanal entre mercados")
            + figures.bars_by_market(components, "share",
                                    "Varianza explicada por componente", rule=0.70))


def paired_table(rows: pd.DataFrame) -> str:
    """Test 1b: each trade against the average window of its own length in its own regime.

    Args:
        rows: Per-market rows carrying paired_mean, paired_median, paired_p, paired_beat and
            the bootstrap bounds.

    Returns:
        A scrollable table. Cost cancels between the trade and its reference, so nothing here
        depends on the cost assumption — and nothing here says the strategy is profitable,
        only that its entries did or did not beat blind entries of the same duration.
    """
    head = _row(["mercado", "alfa medio / operación", "mediana", "IC 90%",
                "% de operaciones que ganan", "p (Wilcoxon)"], "th")
    body = [_row([_label(r), f"{r.paired_mean:+.5f}", f"{r.paired_median:+.5f}",
                 f"[{r.paired_ci_lo:+.5f}, {r.paired_ci_hi:+.5f}]", f"{r.paired_beat:.1%}",
                 f"{r.paired_p:.4f}"]) for r in rows.itertuples()]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def drivers_table(rows: pd.DataFrame, base: dict) -> str:
    """What kind of market each one is: the structural properties of PDF section 5.4.

    Args:
        rows: Per-market rows carrying a `drivers` dict.
        base: The record's `base` entry, whose own drivers are shown as the reference.

    Returns:
        A scrollable table with the base asset first. These describe the market, not the
        strategy: with two markets they are a description of where the edge did and did not
        transfer, and the regression the source note asks for needs six or more.
    """
    head = _row(["mercado", "Hurst", f"VR", "% barras en tendencia (ADX)", "ATR % del precio",
                "ratio de eficiencia", "velas", "ventana"], "th")
    entries = [(base["feed"], base["drivers"], " (base)")]
    entries += [(r.feed, r.drivers, "") for r in rows.itertuples()]
    body = [_row([f"<code>{feed}</code>{tag}", f"{d['hurst']:.3f}",
                 f"{d['variance_ratio']:.3f}", f"{d['adx_trend_share']:.1%}",
                 f"{d['atr_pct']:.3f}", f"{d['efficiency']:.3f}", f"{d['bars']:,}",
                 f"{d['from']} … {d['to']}"]) for feed, d, tag in entries]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def warnings_block(rows: pd.DataFrame, texts: dict[str, str]) -> str:
    """Every reason to distrust each market's numbers, spelled out.

    Args:
        rows: Per-market rows carrying a `warnings` list.
        texts: inference.WARNINGS — the key to its sentence.

    Returns:
        One block per market, or a note when nothing fired. No market is ever hidden by these:
        they are the context the numbers are read in.
    """
    blocks = []
    for r in rows.itertuples():
        if not r.warnings:
            blocks.append(f'<p><code>{r.feed}</code> — <span class="ok">sin avisos</span></p>')
            continue
        items = "".join(f"<li>{texts[w]}</li>" for w in r.warnings)
        blocks.append(f'<p><code>{r.feed}</code></p><ul class="warn">{items}</ul>')
    return "".join(blocks)
