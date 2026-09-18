"""The per-market panels of the window-sweep tab: its tables, its histograms and its cone."""

import numpy as np

from strategies.crossmarket import charts, metrics, panel, sweep, tables

REASONS_ES = {"short_window": "ventana por debajo de sweep.min_months",
              "weak_blocks": "demasiadas operaciones en bloques débiles"}


def window_name(window: str) -> str:
    """A sweep window as the owner reads it.

    Args:
        window: A sweep.windows entry.

    Returns:
        "completa" for the whole window, "3 años" for 3y, "6 meses" for 6m.
    """
    if window == sweep.FULL:
        return "completa"
    count = int(window[:-1])
    words = {"y": ("año", "años"), "m": ("mes", "meses")}[window[-1]]
    return f"{count} {words[count != 1]}"


def sigma(value: float) -> str:
    """The null's σ, readable in dollars and in ATR units alike: no exponent, four figures."""
    return f"{value:,.0f}" if abs(value) >= 100 else f"{value:.4f}"


def at(point: dict, metric: str) -> dict | None:
    """One sweep point's summary for one statistic, or None where the point was withheld."""
    return None if point["table"] is None else point["table"][metric]


def p_cell(view: dict | None, alpha: float) -> str:
    """One p as the grid shows it: a coloured chip, or the cross that means it was withheld."""
    return ('<span class="no">✕</span>' if view is None
            else f'<span class="chip-{"pass" if view["p_value"] <= alpha else "fail"}">'
                 f'{view["p_value"]:.4f}</span>')


def power_table(sw: dict, model: str, metric: str, alpha: float) -> str:
    """One model's sweep point by point, beside the counts that say how far to trust each p.

    Args:
        sw: What analysis.window_sweep() returned for one market.
        model: Which free-placement model.
        metric: Which statistic the σ and the p are for.
        alpha: diagnostics.alpha, for colouring p.

    Returns:
        A scrollable table: blocks, real trades per block, the free room, the share of trades
        in weak blocks, the live trades per random run, the null's σ, and p — or why it was
        withheld.
    """
    head = tables._row(["ventana", "bloques (vacíos)", "ops/bloque mín · mediana",
                        "hueco libre, velas H1", "libre mín", "ops en bloques débiles",
                        "ops vivas por tirada", "σ del nulo", "p"], "th")
    body = []
    for window, point in zip(sw["windows"], sw["points"][model]):
        used = [b for b in window["blocks"] if b["trades"]]
        counts = [b["trades"] for b in used]
        view = at(point, metric)
        p = (f'<span class="no">✕ {REASONS_ES[window["reason"]]}</span>' if view is None
             else p_cell(view, alpha))
        body.append(tables._row([
            window_name(window["window"]),
            f'{len(window["blocks"])} ({len(window["blocks"]) - len(used)})',
            f"{min(counts)} · {np.median(counts):.0f}",
            f'{sum(b["free"] for b in window["blocks"]):,.0f}',
            f'{min(b["free_share"] for b in used):.0%}', f'{window["weak_share"]:.1%}',
            "—" if point["trades"] is None else f'{point["trades"]:,.0f} de {sum(counts):,}',
            "—" if view is None else sigma(view["std"]), p]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def distributions(sw: dict, model: str, metric: str, draws: int) -> str:
    """The null's own distribution at every block size, side by side.

    Args:
        sw: What analysis.window_sweep() returned for one market.
        model: Which free-placement model.
        metric: Which statistic the histograms draw.
        draws: nulls.draws, for the subtitle.

    Returns:
        One histogram per size with the real backtest marked on each, in a row. This is where
        the loss of power is visible rather than argued: the same real value sits in a wider
        and wider null as the blocks shrink, and a p that rises because of that looks nothing
        like a p that rises because the regime came back.
    """
    out = []
    for window, point in zip(sw["windows"], sw["points"][model]):
        name = window_name(window["window"])
        if point["shapes"] is None:
            out.append(f'<div class="fig"><figcaption><b>{name}</b><span>no calculada: '
                       f'{REASONS_ES[window["reason"]]}</span></figcaption></div>')
            continue
        out.append(charts.distribution(point["shapes"][metric], f"Bloque {name}",
                                       f"{draws:,} tiradas confinadas", charts.NARROW))
    return f'<div class="figure-row sweepdist">{"".join(out)}</div>'


def blocks_detail(sw: dict) -> str:
    """Every block of every window size on one market: the counts behind the power table.

    Args:
        sw: What analysis.window_sweep() returned for one market.

    Returns:
        One collapsed section per size. Blocks depend on the real trades and the calendar,
        not on the model, so they are listed once per market rather than once per model.
    """
    head = tables._row(["bloque", "velas H1", "operaciones", "ocupadas H1", "libres H1",
                        "libre", ""], "th")
    out = []
    for window in sw["windows"]:
        rows = "".join(tables._row(
            [f'{b["start"]} → {b["end"]}', f'{b["bars"]:,.0f}', str(b["trades"]),
             f'{b["occupied"]:,.0f}', f'{b["free"]:,.0f}', f'{b["free_share"]:.0%}',
             "" if not weak else "vacío" if not b["trades"] else '<span class="no">débil</span>'])
            for b, weak in zip(window["blocks"], window["weak"]))
        out.append(f'<details><summary>Bloques de la ventana {window_name(window["window"])} · '
                   f'{len(window["blocks"])}</summary><div class="scroll"><table>{head}{rows}'
                   f'</table></div></details>')
    return "".join(out)


def equity_cone(sw: dict, model: str, feed: str, window: str, draws: int) -> str:
    """One block size's confined runs as an equity cone, with the real curve on it.

    Args:
        sw: What analysis.window_sweep() returned for one market.
        model: Which free-placement model.
        feed: The market, for the subtitle.
        window: Which block size the chips selected.
        draws: nulls.draws, for the subtitle.

    Returns:
        The cone of that size's random runs. One size at a time: four cones side by side are
        unreadable, and the comparison across sizes is what the p curve and the histograms
        above already carry.
    """
    for w, point in zip(sw["windows"], sw["points"][model]):
        if w["window"] != window:
            continue
        if point["cone"] is None:
            return ('<div class="note">Este tamaño no se calculó: '
                    f'{REASONS_ES[w["reason"]]}.</div>')
        return charts.cone(point["cone"], f"Equity de las tiradas — bloque {window_name(window)}",
                           f"{feed} · {panel.NAMES[model]} · {draws:,} simulaciones",
                           charts.WIDE)
    return ""
