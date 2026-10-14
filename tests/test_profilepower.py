"""Known-answer tests of the profile's power study, and the proof that it never reads past `build`.

Synthetic noise bars, so the answer is known by construction: with no planted edge the test
detects at its nominal rate, with a large one it detects always, and the same drift planted on
random bars (the control) is not detected. The plant adds exactly the effect asked for.

Run: python3 tests/test_profilepower.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, barstore  # noqa: E402
from studies.research.marketProfile import inputs as profile, series  # noqa: E402
from studies.research.profilePower import analytic, inputs, many, one, plant  # noqa: E402

BARS = 5000
SYMBOL = "EURUSD"
MEASURES = ["run3_follow", "channel20"]


def noise(seed: int) -> pd.DataFrame:
    """Hourly bars whose returns are white noise."""
    rng = np.random.default_rng(seed)
    close = 1.2 * np.exp(np.cumsum(rng.normal(0, 0.001, BARS)))
    opens = np.concatenate([[1.2], close[:-1]])
    wick = np.abs(rng.normal(0, 0.0003, (2, BARS)))
    return pd.DataFrame(
        {
            "Open": opens,
            "High": np.maximum(opens, close) * (1 + wick[0]),
            "Low": np.minimum(opens, close) * (1 - wick[1]),
            "Close": close,
        },
        index=pd.date_range("2010-01-04", periods=BARS, freq="1h"),
    )


def replications(
    cfg: dict, effect: float, reps: int, how: str = "condition"
) -> pd.DataFrame:
    """`reps` judged replications of each test measure at one effect, on noise."""
    cfg = {**cfg, "plant": {**cfg["plant"], "how": how}}
    bars, asset = noise(1), assetdata.load(SYMBOL)
    rows = [
        one.run((SYMBOL, "H1", m, "long", effect, r), bars, asset, cfg)
        for m in MEASURES
        for r in range(reps)
    ]
    return many.judged(pd.DataFrame(rows), cfg)


def test_size_and_power(cfg: dict) -> None:
    """Noise is detected at the nominal rate, a huge edge always, the random control not."""
    none = replications(cfg, 0.0, 40)
    rate = none["significant"].mean()
    assert 0.0 < rate <= 0.125, rate  # 5 % nominal, 80 replications
    assert (none["drawn"] < none["draws"]).any(), "no replication stopped early"
    # 20 costs, not more: a plant that large on a third of the bars becomes the series' drift,
    # which the profile's null keeps (60 costs is detected in no replication of channel20).
    huge = replications(cfg, 20.0, 6)
    assert huge["significant"].all() and huge["pays"].all(), huge[["p", "multiple"]]
    assert (huge["drawn"] == huge["draws"]).all()
    control = replications(cfg, 20.0, 6, "random")
    assert control["significant"].mean() <= 0.25, control["p"]
    print(
        f"potencia: sin edge detecta el {rate:.1%} (nominal 5 %), con 20 costes el 100 %, "
        f"el control al azar el {control['significant'].mean():.0%}"
    )


def test_plant(cfg: dict) -> None:
    """The planted series gains `effect` costs per trade on the base's own trades, and no more."""
    bars, asset, pcfg = noise(2), assetdata.load(SYMBOL), cfg["profile"]
    x, cal = series.logs(bars), series.calendar(bars.index, "H1", pcfg)
    spec = next(s for s in pcfg["measures"] if s["name"] == "channel20")
    _, entry, leave = one.trades(x, cal, pcfg, spec, "long")
    cost = inputs.cost_log(asset, x["o"])
    grown = plant.planted(
        x, entry, leave, 1, 3.0, cost, "condition", np.random.default_rng(0)
    )
    gain = (grown["o"][leave] - grown["o"][entry]) - (x["o"][leave] - x["o"][entry])
    assert abs(gain.mean() / cost[entry].mean() - 3.0) < 0.05, (
        gain.mean() / cost[entry].mean()
    )
    assert (grown["h"] - np.maximum(grown["o"], grown["c"]) > -1e-12).all()
    assert (grown["l"] - np.minimum(grown["o"], grown["c"]) < 1e-12).all()
    same = plant.planted(
        x, entry, leave, 1, 0.0, cost, "condition", np.random.default_rng(0)
    )
    assert np.allclose(same["c"], x["c"]) and np.allclose(same["o"], x["o"])
    held = plant.covered(entry, leave, BARS)
    assert plant.random(held, np.random.default_rng(0)).sum() == held.sum()
    print(
        f"plantado: 3 costes pedidos, {gain.mean() / cost[entry].mean():.3f} medidos en "
        f"{entry.size} operaciones"
    )


def test_arithmetic() -> None:
    """The cut's reach, the crossing of a curve, and the approximation's own inverse."""
    assert one.reach(5 / 3001, 3000) == 4 and one.reach(0.0016661112962345, 3000) == 4
    assert one.reach(0.05, 200) == 9
    x = np.array([0.0, 1.0, 2.0, 5.0])
    assert (
        abs(many.crossing(x, np.array([0.0, 0.4, 1.0, 1.0]), 0.8) - (1 + 2 / 3)) < 1e-9
    )
    assert np.isnan(many.crossing(x, np.array([0.0, 0.1, 0.2, 0.5]), 0.8))
    se = pd.Series([0.5, 2.0])
    back = analytic.power(analytic.detectable(se, 0.001, 0.8), se, 0.001)
    assert np.allclose(back, 0.8), back
    print(
        "aritmética: alcance del corte, cruce de la curva y la aproximación invertida"
    )


def test_build_only() -> None:
    """Bars after the build end never reach the study."""
    lo, hi = profile.span(SYMBOL)
    index = pd.date_range(
        hi - pd.Timedelta(days=300), hi + pd.Timedelta(days=100), freq="15min"
    )
    close = 1.2 * np.exp(
        np.cumsum(np.random.default_rng(4).normal(0, 0.0005, index.size))
    )
    feed = pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.0002,
            "Low": close * 0.9998,
            "Close": close,
            "Volume": 1.0,
        },
        index=index,
    )
    poisoned = feed.copy()
    poisoned.loc[poisoned.index >= hi, ["Open", "High", "Low", "Close"]] *= 1000.0
    real_source, got = barstore.source, []
    for frame in (feed[feed.index < hi], poisoned):
        barstore.source = lambda feed_name, columns=None, f=frame: (
            f[columns] if columns else f
        )
        got.append(inputs.bars(SYMBOL, "H1"))
    barstore.source = real_source
    assert got[1].index.max() < hi and got[1].index.min() >= lo
    pd.testing.assert_frame_equal(got[0], got[1])
    print(
        f"sólo build: {int((poisoned.index >= hi).sum())} barras envenenadas tras {hi.date()} "
        "no entran"
    )


def main() -> None:
    """Run every test with a fixed seed, a light null and a cut of 5 %."""
    cfg = inputs.config(["run.seed=7", "judge.cut=0.05", "judge.chunk=100"])
    cfg["profile"]["nulls"]["draws"] = 200
    with threadpool_limits(1):
        test_arithmetic()
        test_plant(cfg)
        test_build_only()
        test_size_and_power(cfg)
    print("OK test_profilepower")


if __name__ == "__main__":
    main()
