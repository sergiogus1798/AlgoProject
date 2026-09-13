"""The panel's per-strategy content, rendered by the same functions that write the report file."""

import pandas as pd

from strategies.crossmarket import charts, panel, tables


def _rows(record: dict) -> pd.DataFrame:
    """The strategy's per-market rows as a frame, for every renderer here.

    Args:
        record: What cache.load()'s "body" holds for one strategy.

    Returns:
        One row per additional market.
    """
    return pd.DataFrame(record["rows"])


def verdict_tab(record: dict) -> str:
    """Verdict, per-market table and the diagnostics that decide whether it may be believed.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML. `inference.call()` is not touched here: `verdict` is already what
        analysis.analyse_strategy() computed from it.
    """
    rows, v = _rows(record), record["verdict"]
    head = (f'<div class="headline"><div class="stat"><b>{v["verdict"]}</b>'
            f'<span>{v["beaten"]}/{v["markets"]} mercados · familia {v["family"]}</span>'
            f'</div></div>')
    return (head + "<h3>Por mercado</h3>" + panel.market_table(rows)
            + "<h3>Comprobaciones</h3>" + panel.diagnostics(rows))


def exposure_tab(record: dict) -> str:
    """Test 1c across the strategy's markets.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML.
    """
    rows = _rows(record)
    return (charts.bars_by_market(rows[["market", "e"]].to_dict("records"), "e",
                                  "Concentración E por mercado (1,0 = azar)", rule=1.0)
            + tables.exposure_table(rows))


def significance_tab(record: dict) -> str:
    """Significance and breadth across the strategy's markets.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML.
    """
    return tables.breadth_block(record["breadth"]) + tables.significance_table(_rows(record))


def fingerprint_tab(record: dict) -> str:
    """Behavioural fingerprint against gold.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML.
    """
    return tables.fingerprint_table(_rows(record))


def cost_tab(record: dict) -> str:
    """Cost gradient, breakeven and execution stress.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML.
    """
    rows = _rows(record)
    return (charts.bars_by_market(rows[["market", "breakeven"]].to_dict("records"),
                                  "breakeven", "Múltiplo de coste de equilibrio (gate: 2,0)",
                                  rule=2.0)
            + tables.cost_table(rows))


def correlation_tab(record: dict) -> str:
    """Correlation matrix and PCA across the strategy's markets plus gold.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's HTML.
    """
    return tables.correlation_section(record["correlation"], record["pca"])


TABS = {"verdict": verdict_tab, "exposure": exposure_tab, "significance": significance_tab,
       "fingerprint": fingerprint_tab, "cost": cost_tab, "correlation": correlation_tab}


def section(name: str, record: dict) -> str:
    """One tab's HTML, for the strategy the panel is showing.

    Args:
        name: A key of TABS.
        record: What cache.load()'s "body" holds.

    Returns:
        The tab's content.
    """
    return TABS[name](record)


def runs(record: dict) -> list[str]:
    """Every market this strategy was tested on, for the test explorer's market dropdown.

    Args:
        record: What cache.load()'s "body" holds.

    Returns:
        Market feeds, in the order they were run.
    """
    return list(record["shapes"])


def figure(record: dict, market: str, model: str) -> str:
    """One (market, model) pair's null distribution with the real run marked.

    Args:
        record: What cache.load()'s "body" holds.
        market: A market feed, from runs().
        model: A key of trade_models.MODELS.

    Returns:
        The figure. Every model's shape was stored for every market, so browsing this
        dropdown never recomputes anything — only the "re-run" button does.
    """
    row = next(r for r in record["rows"] if r["market"] == market)
    return charts.distribution(record["shapes"][market][model], market,
                               f"modelo {model} — p = {row[f'p_{model}']:.4f}")
