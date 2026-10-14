"""Known-answer tests of the pooled profile, and the proof that it never reads past `build`.

Synthetic assets, so the answer is known by construction: groups of independent noise are not
named; a small persistence planted in every asset of a group is named by the group when no
asset passes alone; identical assets are resampled jointly, so their sum is as wide under the
null as it is in reality; and shrinkage pulls a noisy asset to its group.

Run: python3 tests/test_pooledprofile.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, barstore  # noqa: E402
from studies.research.marketProfile import inputs as profile  # noqa: E402
from studies.research.pooledProfile import inputs, many, one, shrink  # noqa: E402

BARS = 8000
COSTS = "EURUSD"  # the asset whose costs every synthetic asset is charged
MEASURES = [
    "vr4",
    "look12_hold4",
    "channel20",
    "extreme2",
    "bar1atr",
    "run3_follow",
    "run3_fade",
    "inside",
]


def synthetic(phi: float, seed: int) -> pd.DataFrame:
    """Hourly bars whose returns are AR(1) with coefficient phi: 0 is white noise."""
    rng = np.random.default_rng(seed)
    shock = rng.normal(0, 0.001, BARS)
    r = np.empty(BARS)
    r[0] = shock[0]
    for i in range(1, BARS):
        r[i] = phi * r[i - 1] + shock[i]
    close = 1.2 * np.exp(np.cumsum(r))
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


def cell(group: str, frames: list[pd.DataFrame], cfg: dict) -> dict:
    """A synthetic group measured asset by asset and turned into its judged cell."""
    got = [
        one.run(f"{group}{k}", group, "H1", f, assetdata.load(COSTS), cfg)
        for k, f in enumerate(frames)
    ]
    return many.cell([g["rows"] for g in got], np.array([g["sims"] for g in got]), cfg)


def test_groups(cfg: dict) -> None:
    """Noise groups are not named; an effect in every asset is, when no asset passes alone."""
    quiet = [
        cell(f"N{g}", [synthetic(0.0, 100 * g + k) for k in range(5)], cfg)
        for g in (1, 2)
    ]
    got = many.run(quiet, cfg, set())
    assert not got["tests"]["significant"].any(), got["tests"].query("significant")
    assert got["board"].empty and got["placebo"]["any_named"] <= 0.15, got["placebo"]
    print(
        f"ruido independiente: 0 de {len(got['tests'])} pruebas de grupo nombradas; en "
        f"placebos, algo nombrado el {got['placebo']['any_named']:.1%} de las veces"
    )

    trend = cell("T", [synthetic(0.03, 500 + k) for k in range(8)], cfg)
    got = many.run([*quiet, trend], cfg, set())
    named = got["tests"][got["tests"]["significant"]]
    assert set(named["group"]) == {"T"} and "vr4" in set(named["measure"]), named
    alone = got["assets"].merge(named[many.TEST])["significant_alone"]
    assert not alone.any(), (
        "an asset passed alone: the test no longer shows what pooling adds"
    )
    cells = got["board"]
    assert len(cells) and cells["new"].all() and not cells["alone"].any()
    inside = {tuple(k) for k in cells[many.CELL].to_numpy()}
    assert not many.run([*quiet, trend], cfg, inside)["board"]["new"].any()
    print(
        f"efecto en los 8 activos de un grupo: {len(named)} pruebas del grupo nombradas, "
        f"ningún activo pasa solo, {len(cells)} celdas-familia contadas"
    )


def test_joint(cfg: dict) -> None:
    """Assets of one group draw the same positions: identical assets stay identical under the
    null, and their sum is as wide as their correlation makes it."""
    frame = synthetic(0.0, 9)
    asset = assetdata.load(COSTS)
    a, b = (one.run(name, "G", "H1", frame, asset, cfg) for name in ("G0", "G1"))
    assert np.array_equal(a["sims"], b["sims"])
    other = one.run("H0", "H", "H1", frame, asset, cfg)
    assert not np.array_equal(a["sims"], other["sims"])
    tested = np.array([a["rows"]["tested"].to_numpy()] * 4)
    sims = np.array([a["sims"]] * 4)
    null = many.pooled.combined(many.pooled.standardised(sims), tested)
    spread = null[:, tested[0]].std(axis=0).mean()
    assert 1.8 < spread < 2.2, spread  # four identical assets: root of 4, not 1
    print(
        f"nula conjunta: cuatro activos idénticos, la suma se abre {spread:.2f} veces "
        "(2 si se conserva la correlación, 1 si se remuestrearan por separado)"
    )


def test_shrink() -> None:
    """Equal true effects collapse to the group's mean; a real outlier keeps most of its own."""
    se = np.full(6, 1.0)
    same = shrink.random_effects(np.array([1.2, 0.8, 1.1, 0.9, 1.0, 1.0]), se)
    assert same["tau"] == 0 and np.allclose(same["shrunk"], 1.0)
    far = shrink.random_effects(
        np.array([0.0, 0.1, -0.1, 0.0, 0.1, 9.0]), np.full(6, 0.5)
    )
    assert far["tau"] > 1 and 7 < far["shrunk"][-1] < 9 and far["i2"] > 0.9
    noisy = shrink.random_effects(
        np.array([0.0, 0.2, -0.2, 0.1, 6.0]), np.array([0.3, 0.3, 0.3, 0.3, 5.0])
    )
    assert noisy["shrunk"][-1] < 3, noisy  # a wide error is pulled to the group
    print(
        "encogimiento: efectos iguales -> la media; un activo ruidoso se acerca al grupo"
    )


def test_build_only(cfg: dict) -> None:
    """Bars after the build end never reach a group."""
    symbols = ["EURUSD", "GBPUSD"]
    hi = min(profile.span(s)[1] for s in symbols)
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
        got.append(inputs.bars(symbols, ["H1"])["H1"])
    barstore.source = real_source
    for s in symbols:
        assert got[1][s].index.max() < hi
        pd.testing.assert_frame_equal(got[0][s], got[1][s])
    print(
        f"sólo build: {int((poisoned.index >= hi).sum())} barras envenenadas tras {hi.date()} "
        "no entran en ningún grupo"
    )


def main() -> None:
    """Run every test with a fixed seed, a light null and a short list of measures."""
    cfg = inputs.config(["run.seed=7", "judge.placebos=100"])
    cfg["profile"]["nulls"]["draws"] = 600
    cfg["profile"]["measures"] = [
        m for m in cfg["profile"]["measures"] if m["name"] in MEASURES
    ]
    with threadpool_limits(1):
        test_shrink()
        test_build_only(cfg)
        test_joint(cfg)
        test_groups(cfg)
    print("OK test_pooledprofile")


if __name__ == "__main__":
    main()
