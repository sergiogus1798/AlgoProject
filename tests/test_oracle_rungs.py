#!/usr/bin/env python3
"""Checks the random-entry ladder, the null statistics and the channel attribution
against their documented definitions."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engines.nulls import model, stats, verdict  # noqa: E402

BAD: list[str] = []
W0, W1 = 100, 5100


def ok(name: str, cond: bool, detail: str = "") -> None:
    """Print PASS or FAIL for one check and record failures."""
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}: {detail}")
        BAD.append(name)


def make(n: int, w0: int, w1: int, hmax: int, seed: int) -> dict:
    """Build a `located` dict by hand: n trades inside [w0, w1], holds 1..hmax."""
    rng = np.random.default_rng(seed)
    hold = rng.integers(1, hmax + 1, n)
    entry = np.sort(rng.integers(w0, w1 - hmax, n))
    return {
        "entry": entry,
        "exit": entry + hold,
        "hold": hold,
        "size": rng.uniform(0.5, 2.0, n),
        "window": (w0, w1),
    }


def pairs(h: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Rows of (hold, size) sorted within each draw, to compare multisets of pairs."""
    key = np.argsort(h * 1000.0 + s, axis=1)
    return np.stack([np.take_along_axis(h, key, 1), np.take_along_axis(s, key, 1)])


def t_rungs() -> None:
    """Shape, window, integrality, what each rung keeps, what varies, overlap, determinism."""
    loc = make(40, W0, W1, 30, 1)
    d = 2000
    for name, fn in model.RUNGS.items():
        o = fn(loc, d, np.random.default_rng(5))
        e, h, s = o["entries"], o["holds"], o["sizes"]
        ok(f"{name}.shape", e.shape == h.shape == s.shape == (d, 40), f"{e.shape} {h.shape} {s.shape}")
        ok(
            f"{name}.integer_entries",
            np.issubdtype(e.dtype, np.integer) or np.all(e == np.round(e)),
            f"{e.dtype}",
        )
        ok(f"{name}.window", e.min() >= W0 and (e + h).max() <= W1, f"min {e.min()} max end {(e + h).max()}")
        ok(f"{name}.holds_positive", h.min() >= 1, f"{h.min()}")
        ok(f"{name}.entries_vary", len(np.unique(e[:, 0])) > 100, "entries do not vary between draws")
        a = fn(loc, 50, np.random.default_rng(9))["entries"]
        b = fn(loc, 50, np.random.default_rng(9))["entries"]
        c = fn(loc, 50, np.random.default_rng(10))["entries"]
        ok(f"{name}.seed_same", np.array_equal(a, b), "same seed differs")
        ok(f"{name}.seed_diff", not np.array_equal(a, c), "different seed identical")
        o_ = np.argsort(e, axis=1)
        es, hs = np.take_along_axis(e, o_, 1), np.take_along_axis(h, o_, 1)
        ov = float((es[:, 1:] < es[:, :-1] + hs[:, :-1]).any(1).mean())
        print(f"INFO {name}.overlap: share of draws with overlapping trades = {ov:.3f} (docstring silent)")
        if name == "timing":
            ok(
                "timing.keeps_pairs",
                np.array_equal(
                    pairs(h.astype(float), s),
                    pairs(np.tile(loc["hold"], (d, 1)).astype(float), np.tile(loc["size"], (d, 1))),
                ),
                "(hold,size) pairs altered",
            )
            print(f"INFO timing.column_pairing: column i keeps own hold = {bool((h == loc['hold']).all())}")
        if name == "timing_holds":
            ok(
                "timing_holds.sizes_kept",
                np.allclose(np.sort(s, 1), np.sort(loc["size"])),
                "size multiset altered",
            )
            ok(
                "timing_holds.holds_from_own",
                set(np.unique(h)) <= set(loc["hold"].tolist()),
                "foreign hold value",
            )
            ok(
                "timing_holds.holds_vary",
                len(np.unique(np.sort(h, 1), axis=0)) > 100,
                "hold multiset never varies",
            )
            print(f"INFO timing_holds.paired: share of cells with own hold = {(h == loc['hold']).mean():.3f}")
        if name == "timing_sizing":
            ok(
                "timing_sizing.const_mean",
                np.allclose(s, loc["size"].mean()),
                f"{np.unique(s)[:3]} vs {loc['size'].mean()}",
            )
            ok(
                "timing_sizing.holds_kept",
                np.array_equal(np.sort(h, 1), np.tile(np.sort(loc["hold"]), (d, 1))),
                "hold multiset altered",
            )
        if name == "free":
            print(f"INFO free.sizes: unique={np.unique(s)[:4]} own mean={loc['size'].mean():.4f}")
            print(f"INFO free.holds: range {h.min()}..{h.max()} own {loc['hold'].min()}..{loc['hold'].max()}")
            ok("free.holds_vary", len(np.unique(h)) > 1, "holds constant")


def t_uniform() -> None:
    """Placement uniform over feasible starts; both support ends reached, nothing outside."""
    w0, w1 = 0, 60
    loc = make(3, w0, w1, 10, 2)
    loc["hold"] = np.array([1, 5, 10])
    loc["entry"] = np.array([0, 20, 40])
    loc["exit"] = loc["entry"] + loc["hold"]
    d = 20000
    for name, fn in model.RUNGS.items():
        o = fn(loc, d, np.random.default_rng(3))
        e, h = o["entries"].ravel(), o["holds"].ravel()
        u = (e - w0) / np.maximum(w1 - h - w0, 1)
        band = 3.29 * np.sqrt(1 / 12 / e.size)
        print(f"INFO {name}.uniform mean u={u.mean():.4f} exp=0.5 band={band:.4f}")
        ok(f"{name}.uniform_mean", abs(u.mean() - 0.5) <= band, f"{u.mean()}")
        bad = 0
        for hv in np.unique(h):
            m = h == hv
            if m.sum() < 2000:
                continue
            want = set(range(w0, w1 - int(hv) + 1))
            got = set(np.unique(e[m]).tolist())
            bad += got != want
        ok(
            f"{name}.support_exact",
            bad == 0,
            f"{bad} hold values with a hole or overshoot in the entry support",
        )


def t_stats() -> None:
    """profit_factor, drawdown, measure on hand cases."""
    pf = stats.profit_factor(np.array([[1, -2, 3, -1.0], [1, 2, 3, 4.0], [-1, -2, -3, -4.0]]))
    ok("pf.value", np.isclose(pf[0], 4 / 3), f"{pf[0]}")
    ok("pf.no_losses_inf", np.isinf(pf[1]) and pf[1] > 0, f"{pf[1]}")
    ok("pf.no_gains_zero", pf[2] == 0.0, f"{pf[2]}")
    rows = [[-3, 1, 1.0, 0, 0, 0], [2, -1, -2, 3, -4.0, 0], [1, 2, 3, 4.0, 1, 1], [5, -1, -1, 4.0, -3, 1]]
    dd = stats.drawdown(np.array(rows))
    ok("dd.first_loss", np.isclose(dd[0], 3), f"{dd[0]} (equity 0 -> -3)")
    ok("dd.peak_trough", np.isclose(dd[1], 4), f"{dd[1]} (cum 2,1,-1,2,-2: peak 2 to -2)")
    ok("dd.all_win", dd[2] == 0, f"{dd[2]}")
    ok("dd.mid", np.isclose(dd[3], 3), f"{dd[3]} (cum 5,4,3,7,4,5: peak 7 to 4)")
    ok("dd.positive", (dd >= 0).all(), f"{dd}")
    x = np.random.default_rng(7).normal(0.2, 1.0, (6, 50))
    m = stats.measure(x, ["net", "sharpe", "pf", "retdd", "dd"])
    ok("measure.net", np.allclose(m["net"], x.sum(1)), "net = sum")
    ok("measure.pf", np.allclose(m["pf"], stats.profit_factor(x)), "pf")
    ok("measure.dd", np.allclose(m["dd"], stats.drawdown(x)), "dd")
    ok("measure.retdd", np.allclose(m["retdd"], x.sum(1) / stats.drawdown(x)), "retdd = net/dd")
    s1, s0 = x.mean(1) / x.std(1, ddof=1), x.mean(1) / x.std(1)
    ok("measure.sharpe", np.allclose(m["sharpe"], s1) or np.allclose(m["sharpe"], s0), f"{m['sharpe'][:2]}")
    print(
        f"INFO measure.sharpe_ddof: ddof=1 {np.allclose(m['sharpe'], s1)} "
        f"ddof=0 {np.allclose(m['sharpe'], s0)}"
    )
    ok("measure.one_row", stats.measure(x[:1], ["net"])["net"].shape == (1,), "single row")
    ok("measure.only_asked", set(m) == {"net", "sharpe", "pf", "retdd", "dd"}, f"{set(m)}")


def t_attribute() -> None:
    """Channel gaps and total from rung means, higher-better and drawdown."""
    names = ["timing", "timing_holds", "timing_sizing", "free"]
    skew = np.array([0.0, 0.0, 0.0, 10.0])
    tm = {"net": (5.0, 4.2, 3.1, 1.5), "dd": (2.0, 2.9, 3.4, 4.1)}
    for key, (a, b, c, f) in tm.items():
        rr = {n: {key: np.array([v, v, v, v])} for n, v in zip(names[:3], (a, b, c))}
        rr["free"] = {key: f - 2.5 + skew}
        mean_free = float((f - 2.5 + skew).mean())
        real = 9.0 if key == "net" else 1.0
        r = verdict.attribute({key: real}, rr, key)
        sg = 1.0 if verdict.GOOD_HIGH[key] else -1.0
        tot = sg * (real - mean_free)
        ok(f"attribute.{key}.total", np.isclose(float(r["total"]), tot), f"{r['total']} vs {tot}")
        ok(
            f"attribute.{key}.holding",
            np.isclose(float(r["holding_time"]), sg * (a - b)),
            f"{r['holding_time']}",
        )
        ok(
            f"attribute.{key}.sizing",
            np.isclose(float(r["sizing"]), sg * (a - c)),
            f"{r['sizing']} vs {sg * (a - c)}",
        )
    print("INFO attribute.sign: channel = keeps - hands (higher-better); flipped for dd; tested exactly so")


def main() -> None:
    """Run every check; exit 1 on any FAIL or ERROR."""
    for fn in (t_rungs, t_uniform, t_stats, t_attribute):
        fn()
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
