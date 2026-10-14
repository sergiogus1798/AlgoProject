#!/usr/bin/env python3
"""Checks engines.regimes.regime
against hand-built candles, the Wilder ATR definition and the arch package."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model

ROOT = (
    Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
)
sys.path.insert(0, str(ROOT))

from engines.regimes import regime as rg  # noqa: E402

BAD: list[str] = []
CFG = {"atr_period": 5, "garch_order": [1, 1], "garch_dist": "normal"}


def ok(name: str, cond: bool, detail: str = "") -> None:
    """Print PASS or FAIL for one check and record failures."""
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}: {detail}")
        BAD.append(name)


def candles(n: int, seed: int) -> pd.DataFrame:
    """Random daily OHLC on business days."""
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 1, n))
    o = np.r_[100.0, c[:-1]] + rng.normal(0, 0.2, n)
    hi = np.maximum(o, c) + rng.uniform(0.1, 1.5, n)
    lo = np.minimum(o, c) - rng.uniform(0.1, 1.5, n)
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.DataFrame({"Open": o, "High": hi, "Low": lo, "Close": c}, index=idx)


def wilder(d: pd.DataFrame, n: int) -> pd.Series:
    """Reference Wilder ATR: TR = max(H-L, |H-Cprev|, |L-Cprev|), SMA seed, then (A*(n-1)+TR)/n."""
    pc = d["Close"].shift(1)
    tr = pd.concat(
        [d["High"] - d["Low"], (d["High"] - pc).abs(), (d["Low"] - pc).abs()], axis=1
    ).max(axis=1)
    a = np.full(len(d), np.nan)
    a[n] = tr.iloc[1 : n + 1].mean()
    for t in range(n + 1, len(d)):
        a[t] = (a[t - 1] * (n - 1) + tr.iloc[t]) / n
    return pd.Series(a, d.index)


def t_daily() -> None:
    """Three days of hourly bars collapse to first open, max high, min low, last close."""
    idx = pd.date_range("2024-01-01", periods=72, freq="h")
    rng = np.random.default_rng(1)
    c = 100 + np.cumsum(rng.normal(0, 1, 72))
    o = np.r_[100.0, c[:-1]]
    b = pd.DataFrame(
        {
            "Open": o,
            "High": np.maximum(o, c) + 0.5,
            "Low": np.minimum(o, c) - 0.5,
            "Close": c,
        },
        index=idx,
    )
    d = rg.daily(b)
    ok("daily.rows", len(d) == 3, f"{len(d)}")
    for k in range(3):
        s = slice(24 * k, 24 * k + 24)
        row = d.iloc[k]
        exp = (
            o[s][0],
            (np.maximum(o, c) + 0.5)[s].max(),
            (np.minimum(o, c) - 0.5)[s].min(),
            c[s][-1],
        )
        got = (row["Open"], row["High"], row["Low"], row["Close"])
        ok(f"daily.day{k}", np.allclose(got, exp), f"{got} vs {exp}")
    ok(
        "daily.index",
        list(d.index) == list(pd.date_range("2024-01-01", periods=3)),
        f"{list(d.index)}",
    )


def t_atr() -> None:
    """Wilder ATR lagged one day, and no look-ahead."""
    d = candles(150, 2)
    out = rg.atr(d, CFG)
    v = out["vol"]
    ref = wilder(d, 5)
    ok(
        "atr.is_series_same_index",
        isinstance(v, pd.Series) and v.index.equals(d.index),
        "index",
    )
    ok(
        "atr.lagged_wilder",
        np.allclose(v.iloc[60:].values, ref.shift(1).iloc[60:].values, rtol=1e-6),
        f"max rel gap {np.nanmax(np.abs(v.values[60:] / ref.shift(1).values[60:] - 1))}",
    )
    print(
        f"INFO atr.cfg used: {CFG}; model='{out['model']}'; leading NaNs={int(v.isna().sum())}"
    )
    d2 = d.copy()
    k = 90
    d2.iloc[k, d2.columns.get_loc("High")] += 50
    d2.iloc[k, d2.columns.get_loc("Low")] -= 50
    v2 = rg.atr(d2, CFG)["vol"]
    ok(
        "atr.no_lookahead",
        np.allclose(v.iloc[: k + 1], v2.iloc[: k + 1], equal_nan=True),
        "value at day t moved with day t",
    )
    ok(
        "atr.next_day_reacts",
        v2.iloc[k + 1] > v.iloc[k + 1] + 1,
        f"{v.iloc[k + 1]} -> {v2.iloc[k + 1]}",
    )
    ok("atr.positive", (v.dropna() > 0).all(), "non-positive vol")


def sim_garch(n: int) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """Simulate GARCH(1,1) returns; return candles, true sigma and returns."""
    rng = np.random.default_rng(3)
    om, a, b = 2e-6, 0.08, 0.9
    s2, r = np.empty(n), np.empty(n)
    s2[0] = om / (1 - a - b)
    for t in range(n):
        if t:
            s2[t] = om + a * r[t - 1] ** 2 + b * s2[t - 1]
        r[t] = np.sqrt(s2[t]) * rng.normal()
    idx = pd.bdate_range("2010-01-01", periods=n)
    c = 100 * np.exp(np.cumsum(r))
    o = np.r_[100.0, c[:-1]]
    d = pd.DataFrame(
        {
            "Open": o,
            "High": np.maximum(o, c) * 1.001,
            "Low": np.minimum(o, c) * 0.999,
            "Close": c,
        },
        index=idx,
    )
    return d, pd.Series(np.sqrt(s2), idx), r


def t_garch() -> None:
    """GARCH(1,1) vol against arch's own fit and the true simulated sigma."""
    d, sig, r = sim_garch(3000)
    out = rg.garch(d, CFG)
    v = out["vol"]
    ref = arch_model(
        100 * np.diff(np.log(d["Close"].values)), p=1, q=1, dist="normal"
    ).fit(disp="off")
    cv = pd.Series(ref.conditional_volatility, d.index[1:])
    c1, c2 = v.corr(cv), v.corr(sig)
    print(
        f"INFO garch.cfg used: {CFG}; model='{out['model']}' note='{out['note']}'; "
        f"corr_arch={c1:.4f} corr_true={c2:.4f}"
    )
    ok("garch.vs_arch", c1 > 0.9, f"{c1}")
    ok("garch.vs_true", c2 > 0.8, f"{c2}")
    lag = {
        "same_day": v.corr(sig),
        "next_day_sigma": v.corr(sig.shift(-1)),
        "prev_day_sigma": v.corr(sig.shift(1)),
    }
    ok(
        "garch.aligned_to_sigma_D",
        lag["same_day"] >= max(lag.values()) - 1e-12,
        f"{lag}",
    )
    d2 = d.copy()
    k = 2000
    d2.iloc[k:, :] = d2.iloc[k:, :].values * 1.15
    v2 = rg.garch(d2, CFG)["vol"]
    rel = ((v2 - v) / v).abs()
    print(
        f"INFO garch.lookahead: shock day {k} (+15% jump); rel change vol[k-1]={rel.iloc[k - 1]:.4f} "
        f"vol[k]={rel.iloc[k]:.4f} vol[k+1]={rel.iloc[k + 1]:.4f}; max before k={rel.iloc[:k].max():.4f} "
        "(parameters are refitted on the whole sample: in-sample by design)"
    )
    ok(
        "garch.shock_hits_next_day",
        rel.iloc[k + 1] > 5 * rel.iloc[k],
        f"{rel.iloc[k]} vs {rel.iloc[k + 1]}",
    )


def t_tag() -> None:
    """Terciles of the vol series, balance, NaN warm-up and a missing day."""
    n = 300
    idx = pd.bdate_range("2021-01-04", periods=n)
    vol = pd.Series(np.random.default_rng(4).lognormal(0, 0.5, n), idx)
    vol.iloc[:3] = np.nan
    opens = (idx + pd.Timedelta(hours=13)).values
    out = rg.tag(opens, vol)
    q1, q2 = np.quantile(vol.dropna(), [1 / 3, 2 / 3])
    print(f"INFO tag.edges lib={out['edges']} np.quantile={[q1, q2]}")
    ok(
        "tag.edges",
        np.allclose(out["edges"], [q1, q2], rtol=1e-6),
        f"{out['edges']} vs {[q1, q2]}",
    )
    pos = out["positions"]
    exp = {
        "low": np.where(vol.values < q1)[0],
        "mid": np.where((vol.values >= q1) & (vol.values <= q2))[0],
        "high": np.where(vol.values > q2)[0],
    }
    for kx in rg.BUCKETS:
        ok(
            f"tag.{kx}",
            set(pos[kx].tolist()) == set(exp[kx].tolist()),
            f"{len(pos[kx])} vs {len(exp[kx])}",
        )
    sizes = [len(pos[kx]) for kx in rg.BUCKETS]
    ok("tag.balanced", max(sizes) - min(sizes) <= 2, f"{sizes}")
    ok(
        "tag.warmup_unlabelled",
        all(i not in set(np.concatenate(list(pos.values()))) for i in (0, 1, 2)),
        "NaN day tagged",
    )
    ok(
        "tag.coverage",
        np.isclose(out["coverage"], (n - 3) / n),
        f"{out['coverage']} vs {(n - 3) / n}",
    )
    try:
        rg.tag(np.array(["2030-01-01T10:00"], dtype="datetime64[ns]"), vol)
        ok(
            "tag.missing_day_raises",
            False,
            "no exception for a day absent from the series",
        )
    except ValueError as e:
        ok("tag.missing_day_raises", True, repr(e))


def main() -> None:
    """Run every check; exit 1 on any FAIL or ERROR."""
    for fn in (t_daily, t_atr, t_garch, t_tag):
        fn()
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
