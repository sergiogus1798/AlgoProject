"""Every group judged together: the correction, the shrunk effects, the placebos, the board."""

import numpy as np
import pandas as pd

from engines.inference import fdr
from studies.research.marketProfile import many as profile_many
from studies.research.pooledProfile import pooled, shrink

TEST = ["group", "timeframe", "direction", "measure"]
CELL = ["symbol", "timeframe", "direction", "family"]


def cell(rows: list[pd.DataFrame], sims: np.ndarray, cfg: dict) -> dict:
    """One group on one timeframe: its tests, its assets' effects, its placebo p-values.

    Args:
        rows: Each asset's measure rows (one.run), the tests in the same order in all.
        sims: assets x draws x tests, the jointly resampled null statistics.
        cfg: The parsed config.

    Returns:
        {"tests": one row per test with at least `groups.min_assets` assets — the statistic,
        its p, the random-effects mean, tau and I2 of the excess over the null, in costs (in
        z for a measure with no trade) —, "assets": one row per test and asset with its raw
        and shrunk effect, "placebo_p": placebos x those tests}.
    """
    z = np.array([r["z"].to_numpy() for r in rows])
    tested = np.array([r["tested"].to_numpy() for r in rows])
    got = pooled.against_null(z, sims, tested, cfg["judge"]["placebos"])
    keep = np.flatnonzero(got["assets"] >= cfg["groups"]["min_assets"])
    tests, assets = [], []
    for k in keep:
        part = pd.DataFrame([r.iloc[k] for r, t in zip(rows, tested[:, k]) if t])
        trade = part["direction"].iloc[0] != "both"
        se = part["se"].to_numpy(dtype=float) if trade else np.ones(len(part))
        excess = part["z"].to_numpy(dtype=float) * se
        fit = shrink.random_effects(excess, se)
        tests.append({**part.iloc[0][[*TEST, "family"]], "assets": len(part),
                      "stat": got["stat"][k], "p": got["p"][k], "mean_excess": fit["mean"],
                      "tau": fit["tau"], "i2": fit["i2"], "trade": trade})
        assets.append(part.assign(excess=excess, se=se, shrunk_excess=fit["shrunk"]))
    return {"tests": pd.DataFrame(tests), "assets": pd.concat(assets, ignore_index=True),
            "placebo_p": got["placebo_p"][:, keep]}


def corrected(rows: pd.DataFrame, key: list[str], alpha: float) -> pd.DataFrame:
    """Benjamini-Hochberg over every row: `q` and `significant`, indexed like rows."""
    tests = [{"metric": "|".join(map(str, k)), "p": p} for k, p in zip(rows[key].to_numpy(), rows["p"])]
    q, named = fdr.adjusted(tests), fdr.discoveries(tests, alpha)
    return pd.DataFrame({"q": [q[t["metric"]] for t in tests],
                         "significant": [t["metric"] in named for t in tests]}, index=rows.index)


def filtered(assets: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Each asset's shrunk effect in money and the profile's other three filters on it.

    Returns:
        assets plus `shrunk_multiple` (the shrunk excess plus what the null's drift already
        gave: comparable with `multiple`), `pays` and `pays_shrunk` (the raw and the shrunk
        multiple against `cost_multiple`), `stable`, `frequent`, and `strict`: shrunk pays,
        stable and frequent. The thresholds are marketProfile's.
    """
    out = assets.copy()
    out["shrunk_multiple"] = out["shrunk_excess"] + out["multiple"] - out["excess"]
    out["pays"] = out["multiple"].fillna(-np.inf) >= filters["cost_multiple"]
    out["pays_shrunk"] = out["shrunk_multiple"].fillna(-np.inf) >= filters["cost_multiple"]
    out["stable"] = (out["years_with_sign"] / out["years"]).fillna(0) > filters["stable_share"]
    out["frequent"] = out["trades_per_year"].fillna(0) >= profile_many.min_trades(
        out["symbol"], filters)
    out["strict"] = out["pays_shrunk"] & out["stable"] & out["frequent"]
    return out


def placebo(cells: list[dict], alpha: float) -> dict:
    """What the procedure names when there is nothing: null draws judged as the real series.

    Args:
        cells: What cell() returned for every group and timeframe.
        alpha: The false discovery rate of the verdict.

    Returns:
        `worlds`, the share of them in which at least one group test is named
        (`any_named`), and the mean and the largest count of tests named. Draw j of one
        group is paired with draw j of the others: groups are taken as independent here.
    """
    p = np.concatenate([c["placebo_p"] for c in cells], axis=1)
    named = np.array([len(fdr.discoveries([{"metric": str(k), "p": v} for k, v in enumerate(row)],
                                          alpha)) for row in p])
    return {"worlds": int(named.size), "any_named": float((named > 0).mean()),
            "mean_named": float(named.mean()), "max_named": int(named.max())}


def board(tests: pd.DataFrame, assets: pd.DataFrame, inside: set) -> pd.DataFrame:
    """The board cells a passing group would bring, by the loose and by the strict route.

    Args:
        tests: Judged group tests (with `significant`).
        assets: What filtered() returned.
        inside: The (symbol, timeframe, direction, family) cells already on the board.

    Returns:
        One row per cell-family of an asset in a passing trade test: the measures that bring
        it, `strict` (some of them with the shrunk effect paying, stable and frequent),
        `alone` (the asset passes that test by itself) and `new` (not on the board today).
        Nothing here changes the board's gate: it only counts.
    """
    named = tests[tests["significant"] & tests["trade"]]
    rows = assets.merge(named[TEST], on=TEST)
    if rows.empty:
        return pd.DataFrame(columns=[*CELL, "group", "measures", "strict", "alone", "new"])
    out = rows.groupby(CELL, sort=True).agg(
        group=("group", "first"), measures=("measure", lambda m: " ".join(sorted(set(m)))),
        strict=("strict", "any"), alone=("significant_alone", "any"),
        best_shrunk_multiple=("shrunk_multiple", "max")).reset_index()
    out["new"] = [tuple(k) not in inside for k in out[CELL].to_numpy()]
    return out


def run(cells: list[dict], cfg: dict, inside: set) -> dict:
    """The whole study from every group's cell.

    Returns:
        {"tests": every group test with `q` and `significant` (Benjamini-Hochberg over all
        of them), "assets": every asset's raw and shrunk effect, with `significant_alone`
        (the same correction over the per-asset tests of this run), "board": board(),
        "placebo": placebo()}.
    """
    alpha, filters = cfg["judge"]["alpha"], cfg["profile"]["filters"]
    tests = pd.concat([c["tests"] for c in cells], ignore_index=True)
    assets = pd.concat([c["assets"] for c in cells], ignore_index=True)
    tests[["q", "significant"]] = corrected(tests, TEST, alpha)
    assets["significant_alone"] = corrected(assets, [*TEST, "symbol"], alpha)["significant"]
    assets = filtered(assets, filters)
    return {"tests": tests, "assets": assets, "board": board(tests, assets, inside),
            "placebo": placebo(cells, alpha)}
