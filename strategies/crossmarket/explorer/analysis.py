"""One strategy's whole cross-market analysis: Test 1a under every model, plus Fases 1-4, on
every additional market. The heavy half of work.py, split out to stay under 250 lines."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import (backtest, breadth, correlation, exposure, fingerprint,
                                    inference, significance, stress)

INFERENCE_KEYS = {"alpha": "ALPHA", "min_trades": "MIN_TRADES", "min_on_open": "MIN_ON_OPEN",
                  "min_markets": "MIN_MARKETS", "correlated": "CORRELATED"}


@contextmanager
def overridden(cfg: dict) -> Iterator[None]:
    """Apply the config drawer's overrides to inference.py's constants for one run only.

    Args:
        cfg: The run configuration; only the five keys of INFERENCE_KEYS are used here.

    Returns:
        A context manager. inference.py is never edited — its constants are patched for the
        duration of the call and restored after, which is how the drawer changes the verdict
        rule's knobs without touching disk, per the owner's decision not to modify that file.
    """
    original = {attr: getattr(inference, attr) for attr in INFERENCE_KEYS.values()}
    for key, attr in INFERENCE_KEYS.items():
        setattr(inference, attr, cfg[key])
    try:
        yield
    finally:
        for attr, value in original.items():
            setattr(inference, attr, value)


def analyse_market(cfg: dict, feed: str, folder: Path, price: pd.DataFrame,
                   gold_fixed: dict) -> tuple[dict, dict, pd.Series]:
    """Every test in this build on one strategy's trades on one additional market.

    Args:
        cfg: The run configuration.
        feed: SQX symbol of the market.
        folder: That market's trade CSV for this strategy.
        price: That market's bars.
        gold_fixed: What backtest.setting() returned for the same strategy on gold.

    Returns:
        (row, shapes, curve): the flat per-market row, every model's null histogram keyed by
        model name (so the test explorer can browse all four without recomputing), and the
        weekly equity curve for the correlation tab.
    """
    real = tradeio.read(folder)
    row = {"market": feed}
    shapes = {}
    for i, model in enumerate(cfg["models"]):
        out = backtest.run(real, price, cfg["draws"], model)
        located = inference.locate(out["real"], out["null"])
        row[f"p_{model}"], row[f"edge_r_{model}"] = located["p"], located["edge_r"]
        shapes[model] = inference.shape(out["real"], out["null"])
        if i == 0:
            row["p"], row["edge_r"] = located["p"], located["edge_r"]
            row.update({k: v for k, v in out.items() if k not in ("null", "real", "model")},
                       real_r=out["real"], null_r=located["null_r"],
                       resolution=located["resolution"])
    row["testable"] = inference.testable(row)

    fixed = backtest.setting(real, price)
    exp = exposure.run(real, price, cfg["bootstrap_draws"], cfg["bootstrap_block"])
    row.update({"e": exp["e"], "a": exp["a"], "mu_m": exp["mu_m"],
               "risk_normalised": exp["risk_normalised"], "a_ci_lo": exp["a_ci"]["lo"],
               "a_ci_hi": exp["a_ci"]["hi"], "capture_mean": exp["capture_mean"],
               "capture_median": exp["capture_median"]})

    returns = significance.trade_returns(fixed, price)
    rng = np.random.default_rng(backtest.SEED)
    mtr = significance.min_track_record(returns, cfg["alpha"])
    pf_ci = significance.bootstrap_metric(returns, significance.profit_factor,
                                          cfg["bootstrap_draws"], cfg["bootstrap_block"], rng)
    ex_ci = significance.bootstrap_metric(returns, significance.expectancy,
                                          cfg["bootstrap_draws"], cfg["bootstrap_block"], rng)
    sharpe = significance.moments(returns)[0]
    row.update({"pf": significance.profit_factor(returns), "pf_ci_lo": pf_ci["lo"],
               "pf_ci_hi": pf_ci["hi"], "expectancy": significance.expectancy(returns),
               "expectancy_ci_lo": ex_ci["lo"], "expectancy_ci_hi": ex_ci["hi"],
               "sharpe": sharpe, "min_track_needed": mtr["needed"],
               "min_track_enough": mtr["enough"]})

    row["fingerprint"] = fingerprint.fingerprint(feed, gold_fixed, {**fixed, "bars": price})
    row["cost_gradient"] = stress.cost_gradient(fixed, price,
                                                cfg["cost_multiples"]).to_dict("records")
    row["breakeven"] = stress.breakeven_multiple(fixed, price)
    row["bar_shift_decay"] = stress.bar_shift_stress(fixed, price, cfg["bar_shift"])
    row["slippage_decay"] = {str(f): stress.range_slippage_stress(fixed, price, f)
                             for f in cfg["slippage_fractions"]}
    return row, shapes, correlation.weekly_equity(fixed, price)


def analyse_strategy(setup: dict, cfg: dict, name: str,
                     on_market: Callable[[str], None] = lambda label: None) -> dict:
    """The whole cross-market analysis of one strategy, over every additional market.

    Args:
        setup: What serve.main() assembled: spec, bars per feed, trades folder.
        cfg: The run configuration.
        name: Strategy name, the CSV's stem.
        on_market: Called with a label after each market finishes, for the progress bar.

    Returns:
        The record work.py caches: rows, shapes, the strategy's verdict, its breadth summary
        and its correlation/PCA across markets plus gold.
    """
    spec = setup["spec"]
    gold_price = setup["bars"][spec["main"]]
    gold_fixed = backtest.setting(
        tradeio.read(setup["trades"] / spec["main"] / f"{name}.csv"), gold_price)
    curves = {"gold": correlation.weekly_equity(gold_fixed, gold_price)}

    rows, shapes = [], {}
    for market in spec["additional"]:
        feed = market["feed"]
        row, shape, curve = analyse_market(
            cfg, feed, setup["trades"] / feed / f"{name}.csv", setup["bars"][feed], gold_fixed)
        rows.append(row)
        shapes[feed] = shape
        curves[feed] = curve
        on_market(f"{name} — {feed}")

    per_market = pd.DataFrame(rows)
    testable = per_market[per_market["testable"]]
    verdict = {"family": inference.family(per_market), **inference.call(testable),
              "edge_r": float(testable["edge_r"].median()) if len(testable) else float("nan")}
    summary = breadth.summary(testable) if len(testable) else {}
    returns_matrix = correlation.returns_matrix(curves)
    return {"rows": per_market.to_dict("records"), "shapes": shapes, "verdict": verdict,
            "breadth": summary, "correlation": correlation.correlation_matrix(curves).to_dict(),
            "pca": correlation.pca(returns_matrix)}
