#!/usr/bin/env python3
"""R7 and R6 of the gate (levels 3a and 3b): the homogeneity p reads identical quarters as
homogeneous and one profitable quarter as not, the drawdown p of a resampled build is centred
and of clustered losses is extreme, and a seed — given or drawn — replays the result."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import resample  # noqa: E402
from studies.screening.gate import level3ab  # noqa: E402

REPEATS = 400  # far under the config's: these are known answers, not measurements
QUARTERS = pd.date_range("2020-01-15", periods=8, freq="QS") + pd.Timedelta(days=14)


def cfg(seed: int | None = 7) -> dict:
    """The two config sections the level reads, at test size."""
    return {
        "homogeneity": {
            "permutations": REPEATS,
            "period": "quarter",
            "min_trades": 5,
            "seed": seed,
        },
        "drawdown": {"block": 8, "sequences": REPEATS, "percentile": 95, "seed": seed},
    }


def table(identity: str, per_quarter: list[np.ndarray]) -> pd.DataFrame:
    """A per-trade table like `operaciones.parquet`: one array of excess per quarter."""
    opened = np.concatenate(
        [
            q + pd.to_timedelta(np.arange(len(x)), unit="D")
            for q, x in zip(QUARTERS, per_quarter)
        ]
    )
    excess = np.concatenate(per_quarter)
    return pd.DataFrame(
        {
            "identity": identity,
            "open_time": opened,
            "close_time": opened,
            "excess": excess,
            "pnl": excess,
        }
    )


def population(seed: int = 0) -> dict:
    """Three strategies: the same trades every quarter, all the profit in one, and plain noise."""
    rng = np.random.default_rng(seed)
    same = rng.standard_t(4, 12) * 100 + 30
    noise = [rng.standard_t(4, 12) * 100 for _ in QUARTERS]
    oos = pd.concat(
        [
            table("same", [same] * len(QUARTERS)),
            table("one", [noise[0] + 400] + noise[1:]),
            table("noise", noise),
        ],
        ignore_index=True,
    )
    build = pd.concat(
        [
            pd.DataFrame({"identity": key, "pnl": rng.standard_t(4, 150) * 100 + 40})
            for key in ("same", "one")
        ],
        ignore_index=True,
    )
    return {"oos": oos, "build": build, "market": {"risk": 1000.0}}


def test_periods_join_the_thin_ones() -> None:
    """A period under the floor goes to the next; a thin tail, to the one before."""
    labels = np.repeat(["2020Q1", "2020Q2", "2020Q3", "2020Q4"], [6, 2, 5, 3])
    assert list(resample.periods(labels, 5)) == [6, 10]
    assert list(resample.periods(labels, 1)) == [6, 2, 5, 3]
    assert list(resample.periods(labels[:3], 5)) == [3]


def test_q_matches_the_spec_table_ranking() -> None:
    """The spec's toy: four quarters of ten, same total mean — the lopsided one has the low p."""
    rng = np.random.default_rng(1)
    noise = rng.standard_normal((4, 10))
    noise -= noise.mean(axis=1, keepdims=True)
    sizes = np.full(4, 10)
    p = [
        resample.homogeneity(
            (noise + np.array(means)[:, None]).ravel(),
            sizes,
            2000,
            np.random.default_rng(2),
        )
        for means in ((0.6, 0.1, 0.2, -0.1), (1.4, -0.2, -0.2, -0.2))
    ]
    assert p[0] > 0.05 > p[1], p
    assert np.isnan(resample.homogeneity(noise[0], np.array([10]), 10, rng))


def test_homogeneity_known_answers() -> None:
    """Identical trades in every quarter → q_p high; all the profit in one quarter → low."""
    facts = level3ab.run(population(), pd.Index(["same", "one", "noise"]), cfg())
    assert (
        facts.loc["same", "q_p"] == 1.0
    )  # no shuffle can be more alike than identical
    assert facts.loc["one", "q_p"] < 0.05
    assert list(facts.columns) == list(level3ab.FACTS)


def test_homogeneity_p_is_uniform_under_the_null() -> None:
    """Noise with no quarter effect: the p is not pushed to either end."""
    rng = np.random.default_rng(3)
    sizes = np.full(8, 12)
    p = np.array(
        [
            resample.homogeneity(rng.standard_t(4, 96), sizes, 200, rng)
            for _ in range(300)
        ]
    )
    assert 0.42 < p.mean() < 0.58 and 0.01 < (p <= 0.05).mean() < 0.10, (
        p.mean(),
        (p <= 0.05).mean(),
    )


def test_max_drawdown_spec_toy() -> None:
    """The spec's ten trades: 200 as they are, 340 with 80 less each; a first loss counts."""
    build = np.array([300, -100, 200, -200, 400, -150, 250, -50, 350, 0.0])
    assert (
        resample.max_drawdown(build) == 200 and resample.max_drawdown(build - 80) == 340
    )
    assert resample.max_drawdown(np.array([-50.0, 100.0])) == 50
    assert list(resample.max_drawdown(np.array([[1.0, 2.0], [-1.0, -2.0]]))) == [0, 3]


def test_drawdown_of_the_build_resampled_is_centred() -> None:
    """oos1 drawn from the build by the same block bootstrap: dd_p spreads around a half."""
    rng = np.random.default_rng(4)
    p = []
    for _ in range(200):
        build = rng.standard_t(4, 330) * 0.8 + 0.3
        start = rng.integers(0, 330 - 8 + 1, 25)
        oos = build[(start[:, None] + np.arange(8)).ravel()][:196]
        null = resample.drawdowns(build, oos.mean(), len(oos), 8, 200, rng)
        p.append(resample.p_upper(null, resample.max_drawdown(oos)))
    p = np.array(p)
    assert 0.40 < p.mean() < 0.60 and (p <= 0.01).mean() < 0.05, (
        p.mean(),
        (p <= 0.01).mean(),
    )


def test_drawdown_sees_clustered_losses() -> None:
    """The spec's example 2: the same trades with the worst losses packed together fall out."""
    rng = np.random.default_rng(5)
    build = rng.standard_t(4, 330) * 0.6 + 0.3
    oos = rng.standard_t(4, 196) * 0.7 + 0.19
    worst = np.argsort(oos)[:14]
    packed = np.r_[np.delete(oos, worst)[:90], oos[worst], np.delete(oos, worst)[90:]]
    p = [
        resample.p_upper(
            resample.drawdowns(
                build, x.mean(), len(x), 8, 2000, np.random.default_rng(6)
            ),
            resample.max_drawdown(x),
        )
        for x in (oos, packed)
    ]
    assert p[0] > 0.10 and p[1] <= 0.01, p


def test_expected_drawdown_is_in_r_and_scale_free() -> None:
    """dd_esperado_r is the simulated 95th percentile over 1R; dd_p does not see the unit."""
    data = population()
    facts = level3ab.run(data, pd.Index(["same", "one", "noise"]), cfg())
    doubled = level3ab.run({**data, "market": {"risk": 2000.0}}, facts.index, cfg())
    assert np.allclose(
        facts["dd_esperado_r"].dropna(), 2 * doubled["dd_esperado_r"].dropna()
    )
    assert (facts["dd_esperado_r"].dropna() > 0).all()
    assert facts.loc[["same", "one"], "dd_p"].between(0, 1).all()
    assert facts.loc["noise", ["dd_p", "dd_esperado_r"]].isna().all()  # no build trades
    assert not np.isnan(facts.loc["noise", "q_p"])


def test_same_seed_same_result_bit_for_bit() -> None:
    """A given seed replays, whoever else is alive; another seed does not."""
    data, alive = population(), pd.Index(["same", "one", "noise"])
    first = level3ab.run(data, alive, cfg(7))
    assert first.equals(level3ab.run(data, alive, cfg(7)))
    assert (first[["q_seed", "dd_seed"]] == 7).all().all()
    alone = level3ab.run(data, pd.Index(["one"]), cfg(7))
    assert alone.loc["one"].equals(first.loc["one"])
    assert not first["dd_esperado_r"].equals(
        level3ab.run(data, alive, cfg(8))["dd_esperado_r"]
    )


def test_null_seed_is_fresh_recorded_and_replays() -> None:
    """`seed: null` draws a root per run, writes it in the scorecard, and it reproduces the run."""
    data, alive = population(), pd.Index(["same", "one", "noise"])
    fresh, again = (
        level3ab.run(data, alive, cfg(None)),
        level3ab.run(data, alive, cfg(None)),
    )
    assert fresh["q_seed"].nunique() == 1 and fresh["dd_seed"].nunique() == 1
    assert fresh.loc["one", "q_seed"] != again.loc["one", "q_seed"]
    assert fresh.loc["one", "dd_seed"] != again.loc["one", "dd_seed"]
    replay = cfg()
    replay["homogeneity"]["seed"] = int(fresh.loc["one", "q_seed"])
    replay["drawdown"]["seed"] = int(fresh.loc["one", "dd_seed"])
    assert fresh.equals(level3ab.run(data, alive, replay))


def test_empty_harvest_gives_empty_facts() -> None:
    """With no data the level returns its facts empty (tests/test_gate_rules.py relies on it)."""
    facts = level3ab.run({}, pd.Index(["a"]), {})
    assert list(facts.columns) == list(level3ab.FACTS) and facts.isna().all().all()


if __name__ == "__main__":
    for check in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        check()
        print("ok", check.__name__)
