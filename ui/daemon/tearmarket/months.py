"""Item 5: the month-sign count of a strategy against its market, IS and OOS apart, as a contract dict."""

import pandas as pd

from ui.daemon.tearmarket.source import SAMPLES

# The four cells in reading order: (key, label, strategy sign, market sign).
CELLS = (("both_up", "estrategia sube · mercado sube", 1, 1),
         ("up_down", "estrategia sube · mercado baja", 1, -1),
         ("down_up", "estrategia baja · mercado sube", -1, 1),
         ("both_down", "estrategia baja · mercado baja", -1, -1))
FLAT = "estrategia plana (P&L del mes 0)"
NO_MARKET = "mercado sin barras o sin variación"


def strategy_months(equity: pd.DataFrame) -> pd.Series:
    """Monthly P&L of one sample from its daily cumulative equity, rounded to the cent.

    Args:
        equity: One sample's rows, `day` and `equity` (the sample starts at 0).

    Returns:
        P&L per calendar month (Period index): last equity of the month minus that of the
        month before; the first month against 0.
    """
    s = equity.sort_values("day").set_index("day")["equity"]
    last = s.groupby(s.index.to_period("M")).last()
    return last.diff().fillna(last).round(2)


def market_months(bars: pd.DataFrame, months: pd.PeriodIndex) -> pd.Series:
    """Month return of the market: last close over first close of the month, minus one.

    Args:
        bars: The feed's bars at any timeframe.
        months: The strategy's months.

    Returns:
        Return per month, NaN where the month has no bar.
    """
    c = bars["Close"]
    g = c.groupby(c.index.to_period("M"))
    return (g.last() / g.first() - 1).reindex(months)


def count(pnl: pd.Series, ret: pd.Series) -> dict:
    """Months per cell, flat months and months with no market sign on their own lines.

    Args:
        pnl: Strategy P&L per month.
        ret: Market return per month, same index.

    Returns:
        `{cell key: months}` plus `flat`, `no_market` and `months`; the six add up to `months`.
    """
    flat = pnl == 0
    blind = ~flat & (ret.isna() | (ret == 0))
    live = ~flat & ~blind
    s, m = pnl[live].gt(0).map({True: 1, False: -1}), ret[live].gt(0).map({True: 1, False: -1})
    out = {k: int(((s == a) & (m == b)).sum()) for k, _, a, b in CELLS}
    return {**out, "flat": int(flat.sum()), "no_market": int(blind.sum()), "months": len(pnl)}


def tab(sample: str, n: dict, span: str) -> dict:
    """One sample's tab: the 2×2 table and the same counts as bars, both-down highlighted.

    Args:
        sample: "IS" or "OOS".
        n: What `count` returned.
        span: "YYYY-MM … YYYY-MM", the sample's first and last month.

    Returns:
        A contract tab.
    """
    table = {"kind": "table", "title": f"Meses {sample}: signo de la estrategia contra el mercado",
             "columns": ["", "mercado sube", "mercado baja", "total"],
             "rows": [["estrategia sube", n["both_up"], n["up_down"], n["both_up"] + n["up_down"]],
                      ["estrategia baja", n["down_up"], n["both_down"],
                       n["down_up"] + n["both_down"]],
                      [FLAT, "", "", n["flat"]], [NO_MARKET, "", "", n["no_market"]],
                      ["meses de la muestra", "", "", n["months"]]],
             "align": ["left", "right", "right", "right"],
             "note": ("Cada celda cuenta meses naturales. Las cuatro celdas, los meses planos y "
                      "los meses sin signo del mercado suman los meses de la muestra.")}
    items = [{"label": lab, "value": n[k], "error": None,
              "state": "watch" if k == "both_down" else "info"} for k, lab, _, _ in CELLS]
    items += [{"label": FLAT, "value": n["flat"], "error": None, "state": "none"},
              {"label": NO_MARKET, "value": n["no_market"], "error": None, "state": "none"}]
    bars = {"kind": "bars", "title": f"Meses {sample} por celda", "unit": "meses",
            "items": items, "reference": None,
            "note": ("Resaltada en ámbar: los meses en que la estrategia y el mercado bajaron a "
                     "la vez. Plana y sin signo del mercado van aparte, fuera de las cuatro celdas.")}
    return {"name": sample, "title": f"{sample} · {span}",
            "note": (f"{n['months']} meses {sample} ({span}). Mes de la estrategia: variación "
                     "de su curva diaria en el mes. Mes del mercado: último cierre / primer "
                     "cierre del mes − 1, con las barras del feed."),
            "selectors": [], "blocks": [table, bars]}


def result(meta: dict, equity: pd.DataFrame, bars: pd.DataFrame) -> dict:
    """The whole answer of item 5 for one strategy.

    Args:
        meta: `project`, `databank`, `identity`, `name`, `asset`, `feed`, `tf`, `day`, `wall_s`.
        equity: The strategy's equity rows, IS and OOS.
        bars: The feed's bars at `tf`, already cut at the end of oos1.

    Returns:
        A contract dict with one tab per sample and `summary.counts` per sample.
    """
    tabs, counts = [], {}
    for sample in SAMPLES:
        pnl = strategy_months(equity[equity["sample"] == sample])
        counts[sample] = count(pnl, market_months(bars, pnl.index))
        tabs.append(tab(sample, counts[sample], f"{pnl.index[0]} … {pnl.index[-1]}"))
    return {"module": "tearMarket", "strategy": meta["name"], "identity": meta["identity"],
            "config_hash": meta["day"], "computed_at": pd.Timestamp.now().isoformat(timespec="seconds"),
            "wall_s": meta["wall_s"], "verdict": None, "tabs": tabs,
            "warnings": [], "glossary": [
                {"term": "mes plano", "text": "Mes en que la curva de la estrategia no cambió: "
                 "no operó o cerró en cero. No entra en ninguna celda."},
                {"term": "mes del mercado", "text": f"{meta['feed']} en {meta['tf']}: último "
                 "cierre del mes / primer cierre del mes − 1."}],
            "summary": {"counts": counts, "asset": meta["asset"], "feed": meta["feed"],
                        "harvest_day": meta["day"], "project": meta["project"],
                        "databank": meta["databank"]}}
