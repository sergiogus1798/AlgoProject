"""Every cell judged together: the correction, the four filters, the scores, the overlap."""

import numpy as np
import pandas as pd

from engines.inference import fdr

KEY = ["symbol", "timeframe", "direction", "measure"]
CELL = ["symbol", "timeframe", "direction"]
FLOOR = 35     # owner, 2026-10-02: no asset may be asked for fewer trades a year than this


def min_trades(symbols: pd.Series, cfg: dict) -> pd.Series:
    """The minimum trades a year each row's asset must reach.

    Args:
        symbols: One asset name per row.
        cfg: The `filters` section: `min_trades_per_year` and `min_trades_per_year_by_asset`.

    Returns:
        The asset's own figure where the map names it, else the default.

    Raises:
        ValueError: A figure below FLOOR, the default or an asset's.
    """
    own = cfg.get("min_trades_per_year_by_asset") or {}
    low = {k: v for k, v in {"default": cfg["min_trades_per_year"], **own}.items() if v < FLOOR}
    if low:
        raise ValueError(f"min_trades_per_year below the floor of {FLOOR} a year: {low}")
    return symbols.map(own).fillna(cfg["min_trades_per_year"])


def corrected(rows: pd.DataFrame, alpha: float, within: list[str]) -> pd.DataFrame:
    """Benjamini-Hochberg inside each group of tests.

    Args:
        rows: One row per test, with KEY and `p`.
        alpha: False discovery rate held inside every group.
        within: Columns that define a group; empty for one group, every test together.

    Returns:
        `q` (the adjusted p) and `significant`, indexed like rows.
    """
    out = pd.DataFrame({"q": 1.0, "significant": False}, index=rows.index)
    for _, part in (rows.groupby(within, sort=False) if within else [(None, rows)]):
        tests = [{"metric": "|".join(k), "p": p} for k, p in zip(part[KEY].to_numpy(), part["p"])]
        q, named = fdr.adjusted(tests), fdr.discoveries(tests, alpha)
        out.loc[part.index, "q"] = [q[t["metric"]] for t in tests]
        out.loc[part.index, "significant"] = [t["metric"] in named for t in tests]
    return out


def judged(rows: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Every measure with its corrected p and the four filters.

    Args:
        rows: Every cell's measure rows (one.run), all assets together.
        cfg: The `filters` section of the config.

    Returns:
        rows plus `q` (Benjamini-Hochberg over every test present — the headline),
        `significant`, `pays` (mean effect per trade at least `cost_multiple` round-trip
        costs), `stable` (the sign holds in more than `stable_share` of the build years),
        `frequent` (at least `min_trades_per_year` a year, see min_trades) and `passes`, all
        four. A measure with no trade has no effect in money and cannot pass. Beside them the
        ALTERNATIVE correction, never the verdict: `q_family`, `significant_family` and
        `passes_family`, the same procedure run inside each family on its own.
    """
    out = rows.copy()
    out[["q", "significant"]] = corrected(out, cfg["alpha"], [])
    alone = corrected(out, cfg["alpha"], ["family"])
    out["q_family"], out["significant_family"] = alone["q"], alone["significant"]
    out["pays"] = out["multiple"].fillna(-np.inf) >= cfg["cost_multiple"]
    out["stability"] = out["years_with_sign"] / out["years"]
    out["stable"] = out["stability"].fillna(0) > cfg["stable_share"]
    out["frequent"] = out["trades_per_year"].fillna(0) >= min_trades(out["symbol"], cfg)
    rest = out["pays"] & out["stable"] & out["frequent"]
    out["passes"], out["passes_family"] = out["significant"] & rest, out["significant_family"] & rest
    return out


def _lead(trades: pd.DataFrame) -> pd.Series:
    """The trade measure that speaks for a family: the best payer among those that pass,
    else the one with the smallest corrected p."""
    passing = trades[trades["passes"]]
    if not passing.empty:
        return passing.sort_values("multiple", ascending=False).iloc[0]
    return trades.sort_values(["q", "multiple"], ascending=[True, False]).iloc[0]


def _tradable(members: pd.DataFrame) -> pd.DataFrame:
    """A family's trade measures that need no clock; the clock ones only when it has no other."""
    trades = members[members["n_trades"].notna()]
    free = trades[~trades["needs_clock"]]
    return trades if free.empty else free


def scores(measures: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Seven scores per cell and direction, each with the numbers of its lead measure.

    Args:
        measures: What judged() returned.
        cfg: The parsed config.

    Returns:
        One row per symbol, timeframe, direction and family. `score` is 0-100: the mean z of
        the family's measures against their nulls, clipped to [0, z_cap] — the directionless
        measures count for both directions. `p`, `multiple` and `stability` are the lead
        measure's; `passes` says some trade measure of the family passed the four filters,
        `fragile` that one was significant and paid but lived off a minority of years.
        A measure that needs the clock never leads and never makes a family pass while the
        family has a measure that does not; `needs_clock` marks the family left with only
        clock measures. `p_family` and `passes_family` are the alternative correction's.
    """
    cap = cfg["score"]["z_cap"]
    families = list(dict.fromkeys(m["family"] for m in cfg["measures"]))
    both = measures[measures["direction"] == "both"]
    rows = []
    for (symbol, timeframe, direction), own in measures[measures["direction"] != "both"].groupby(
            CELL, sort=False):
        shared = both[(both["symbol"] == symbol) & (both["timeframe"] == timeframe)]
        cell = pd.concat([own, shared])
        for family in families:
            members = cell[cell["family"] == family]
            trades = _tradable(members)
            lead = _lead(trades)
            rows.append({
                "symbol": symbol, "timeframe": timeframe, "direction": direction,
                "family": family, "score": 100 * members["z"].clip(0, cap).mean() / cap,
                "lead": lead["measure"], "p": lead["q"], "p_raw": lead["p"],
                "multiple": lead["multiple"], "effect": lead["effect"], "cost": lead["cost"],
                "stability": lead["stability"], "years_with_sign": lead["years_with_sign"],
                "years": lead["years"], "trades_per_year": lead["trades_per_year"],
                "significant": bool(lead["significant"]), "pays": bool(lead["pays"]),
                "stable": bool(lead["stable"]), "frequent": bool(lead["frequent"]),
                "passes": bool(trades["passes"].any()),
                "fragile": bool((trades["significant"] & trades["pays"]
                                 & ~trades["stable"]).any() and not trades["passes"].any()),
                "needs_clock": bool(lead["needs_clock"]), "p_family": lead["q_family"],
                "significant_family": bool(lead["significant_family"]),
                "passes_family": bool(trades["passes_family"].any()),
                "measures": len(members), "measures_significant": int(members["significant"].sum())})
    return pd.DataFrame(rows)


def correlation(table: pd.DataFrame) -> pd.DataFrame:
    """How alike the families score across cells: do seven families measure seven things.

    Args:
        table: What scores() returned.

    Returns:
        One row per pair of families and per scope ("ALL", then each timeframe): Pearson and
        Spearman correlation of the two scores over the cells of that scope.
    """
    rows = []
    for scope, part in [("ALL", table)] + list(table.groupby("timeframe", sort=False)):
        wide = part.pivot_table(index=CELL, columns="family", values="score")
        pearson, spearman = wide.corr(), wide.corr(method="spearman")
        rows += [{"scope": scope, "family_a": a, "family_b": b, "cells": len(wide),
                  "pearson": pearson.loc[a, b], "spearman": spearman.loc[a, b]}
                 for i, a in enumerate(wide.columns) for b in wide.columns[i + 1:]]
    return pd.DataFrame(rows)


def run(rows: pd.DataFrame, cfg: dict) -> dict:
    """The whole map from every cell's rows.

    Returns:
        {"measures": judged(), "scores": scores(), "correlation": correlation()}.
    """
    measures = judged(rows, cfg["filters"])
    table = scores(measures, cfg)
    return {"measures": measures, "scores": table, "correlation": correlation(table)}
