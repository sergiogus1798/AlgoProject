"""Assemble the databank page: what every strategy scored, and what disqualified the rest."""

import argparse
from pathlib import Path

import pandas as pd

from strategies.monteCarlo import scoring, text

TEMPLATE = Path(__file__).with_name("panel.html")
PASSING = scoring.VERDICTS[:3]


def render(title: str, sections: list[str]) -> str:
    """Put the assembled sections inside the page shell.

    Args:
        title: Browser title.
        sections: HTML blocks, in reading order.

    Returns:
        A self-contained page: no scripts, no fonts, no network. It has to open from a USB
        stick in five years.
    """
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", title).replace("__BODY__", "\n".join(sections)))


def table(headers: list[str], rows: list[list[str]]) -> str:
    """One table, first column a label and the rest numbers.

    Args:
        headers: Column titles.
        rows: Already-formatted cells.

    Returns:
        A scrollable table.
    """
    def line(cells: list[str], tag: str) -> str:
        """One row of the table."""
        return (f"<tr><{tag}>{cells[0]}</{tag}>"
                + "".join(f'<{tag} class="n">{c}</{tag}>' for c in cells[1:]) + "</tr>")

    body = "".join(line(r, "td") for r in rows)
    return f'<div class="scroll"><table>{line(headers, "th")}{body}</table></div>'


def headline(rows: pd.DataFrame) -> str:
    """The four numbers that decide whether the rest is worth reading.

    Args:
        rows: One row per strategy.

    Returns:
        A block of stat tiles.
    """
    passed = int(rows.tier.isin(PASSING).sum())
    inconclusive = int((rows.tier == scoring.VERDICTS[4]).sum())
    return (f'<div class="headline">'
            f'<div class="stat"><b>{len(rows)}</b><span>estrategias analizadas</span></div>'
            f'<div class="stat"><b>{passed}</b><span>sin ningún veto</span></div>'
            f'<div class="stat"><b>{rows.composite.median():.0f}</b>'
            f'<span>compuesto mediano</span></div>'
            f'<div class="stat"><b>{inconclusive}</b>'
            f'<span>sin muestra suficiente para decidir</span></div></div>')


def failures(flags: pd.DataFrame) -> str:
    """Every check that disqualified a strategy, most common first.

    Args:
        flags: One row per fired check, over every strategy.

    Returns:
        The summary block, one line per check with the number of one strategy that tripped
        it. Nothing that failed is buried: it comes before any score.
    """
    if flags.empty:
        return '<div class="note">Ninguna prueba falló en ninguna estrategia.</div>'
    counted = flags.groupby(["test", "gate"]).size().reset_index(name="n")
    counted = counted.sort_values(["gate", "n"], ascending=False)
    out = []
    for _, r in counted.iterrows():
        case = flags[flags.test == r.test].iloc[0].to_dict()
        kind = "veto" if r.gate else "aviso"
        many = f"{r.n} estrategias" if r.n > 1 else "1 estrategia"
        out.append(f'<div class="{"fail" if r.gate else "note"}"><b>{r.test}</b> — {kind}, '
                   f'{many}. Por ejemplo <code>{case["strategy"]}</code>: '
                   f'{text.FLAGS[r.test].format(**case)}</div>')
    return "".join(out)


def verdict_table(rows: pd.DataFrame) -> str:
    """Every strategy, its verdict and the numbers behind it.

    Args:
        rows: One row per strategy.

    Returns:
        The table, worst verdict last. Each name links to that strategy's own page.
    """
    order = rows.sort_values(["composite"], ascending=False)
    body = []
    for _, r in order.iterrows():
        tone = "pass" if r.tier in PASSING else "no"
        body.append([f'<a href="estrategias/{r.strategy}.html">{r.strategy}</a>',
                     f'<span class="tier {tone}">{r.tier}</span>', f"{r.composite:.0f}",
                     *[f"{r[f'score_{k}']:.0f}" for k in "ABCDE"],
                     f"{r.trades:,}", f"{r.dd_pct:.1%}", f"{r.dd_pct_95:.1%}",
                     f"{r.inflation:.2f}", f"{r.pf_5:.2f}", f"{r.psr:.3f}",
                     f"{int(r.gates)}"])
    return table(["estrategia", "veredicto", "compuesto", "A", "B", "C", "D", "E",
                  "operaciones", "DD real", "DD p95", "inflación", "PF p5", "PSR", "vetos"],
                 body)


def method(args: argparse.Namespace, cfg: dict, stab: dict, source: dict) -> str:
    """What was run, on what data, with which numbers.

    Args:
        args: Parsed command line.
        cfg: What config.load() returned.
        stab: What stability.spread() returned for the reference strategy.
        source: Export paths and the asset's cost values.

    Returns:
        The appendix. A report whose inputs cannot be named cannot be reproduced, and this
        module's runs are deliberately not reproducible any other way.
    """
    rows = [["simulaciones por prueba", f"{cfg['global']['n_sims']:,}"],
            ["cuenta inicial / riesgo por operación",
             f"{cfg['global']['starting_equity']:,.0f} $ / "
             f"{cfg['global']['risk_per_trade']:,.0f} $"],
            ["operaciones exportadas", str(source["export"])],
            ["barras diarias", str(source["bars"])],
            ["coste recuperado del propio backtest",
             f"{source['cost']['recovered']:.2f} $ mediana por operación"],
            ["coste modelado desde assets/",
             f"{source['cost']['modelled']:.2f} $ (ratio {source['cost']['ratio']:.2f})"],
            ["modelo de volatilidad", source["vol_model"]],
            ["estabilidad, peor número",
             f"{stab['worst']} ±{stab['worst_spread']:.1%} en {stab['runs']} repeticiones"],
            ["semilla", "ninguna: cada ejecución usa entropía nueva"]]
    return table(["qué", "valor"], rows)


def limits(cfg: dict) -> str:
    """What this report may not be used to conclude.

    Args:
        cfg: What config.load() returned.

    Returns:
        The closing block. It is not optional and it is not at the bottom by accident: the
        two conclusions people most want to draw from a Monte Carlo are the two it cannot
        support.
    """
    return f'''<h2>Lo que este informe no dice</h2>
<div class="note"><b>No mide sobreajuste.</b> No hay Deflated Sharpe ni CSCV, y no los habrá aquí:
harían falta todas las estrategias que se probaron durante la generación, y en esta fase no están.
Inventar un número de pruebas para poder calcularlos daría un número creíble y falso. Eso vive en el
análisis de generación, no aquí.</div>
<div class="note"><b>No valida el edge.</b> Llega dando por hecho que la estrategia ya lo tiene —
pasó el decaimiento y el retest — y sólo mide de qué depende: del orden, de qué operaciones
salieron, de la ejecución o del régimen.</div>
<div class="note"><b>El techo de drawdown es provisional.</b> Está en {cfg['scoring']['survival_dd_pct']:.0%}
de la cuenta como marcador de posición hasta que las reglas de la prop firm lo fijen. Todas las
familias se recalculan cambiando un número del config.</div>
<div class="note"><b>Nada de esto se repite igual dos veces.</b> No hay semilla, a propósito. La
sección de estabilidad dice cuánto se mueven los números que deciden; si se mueven demasiado, la
respuesta es subir las simulaciones, no fijar una semilla y creerse la primera.</div>'''
