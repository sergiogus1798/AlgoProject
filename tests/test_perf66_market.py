"""Encargo 66 §9.9: the lazy mirror and `evaluate(directions=)` give the eager mirror's numbers, bit for bit."""

import numpy as np
import pandas as pd
import pytest

from studies.research.marketProfile import higher, inputs, one, series


def _eager(d: dict) -> dict:
    """The mirror as it was written before the lazy one: every array negated up front (the oracle)."""
    out = {**d, "o": -d["o"], "h": -d["l"], "l": -d["h"], "c": -d["c"], "sma": -d["sma"],
           "hi": {n: -v for n, v in d["lo"].items()}, "lo": {n: -v for n, v in d["hi"].items()},
           "chi": {n: -v for n, v in d["clo"].items()}, "clo": {n: -v for n, v in d["chi"].items()}}
    for key in higher.SIGNED:
        out[key] = {n: -v for n, v in d[key].items()} if isinstance(d[key], dict) else -d[key]
    out["d1_hi"], out["d1_lo"] = {n: -v for n, v in d["d1_lo"].items()}, {n: -v for n, v in d["d1_hi"].items()}
    out["rsi"], out["d1_rsi"], out["d1_ibs"] = 100 - d["rsi"], 100 - d["d1_rsi"], 1 - d["d1_ibs"]
    return out


@pytest.fixture(scope="module")
def framed() -> tuple[dict, dict, dict]:
    """A random-walk H1 series framed with the real config."""
    cfg = inputs.config(["nulls.seed=7"])
    index = pd.date_range("2018-01-01", periods=24 * 300, freq="1h")
    index = index[index.weekday < 5]
    rng = np.random.default_rng(3)
    c = 100 + np.cumsum(rng.normal(0, 0.3, index.size))
    bars = pd.DataFrame({"Open": c - rng.normal(0, .05, c.size), "High": c + abs(rng.normal(0, .2, c.size)),
                         "Low": c - abs(rng.normal(0, .2, c.size)), "Close": c}, index=index)
    cal = series.calendar(index, "H1", cfg)
    return one.framed(series.logs(bars), cal, cfg), cal, cfg


def test_mirror_lazy_equals_eager(framed: tuple) -> None:
    """Every key of the lazy mirror equals the eager one, nested dicts included."""
    d, _, _ = framed
    lazy, eager = higher.mirror(d), _eager(d)
    assert set(lazy) == set(eager)
    for key in eager:
        a, b = lazy[key], eager[key]
        pairs = [(a[n], b[n]) for n in b] if isinstance(b, dict) else [(a, b)]
        for left, right in pairs:
            assert np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True), key


def test_evaluate_same_rows_and_directions(framed: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    """evaluate() on the lazy mirror == on the eager one, and directions= only filters."""
    d, cal, cfg = framed
    specs = cfg["measures"]
    got = one.evaluate(d, cal, specs)
    monkeypatch.setattr(higher, "mirror", _eager)
    want = one.evaluate(d, cal, specs)
    assert len(got) == len(want) > 20
    for g, w in zip(got, want):
        assert g[:2] == w[:2]
        for left, right in zip(g[2:5], w[2:5]):
            assert np.array_equal(np.asarray(left, dtype=float), np.asarray(right, dtype=float), equal_nan=True)
    monkeypatch.undo()
    longs = one.evaluate(d, cal, specs, directions=("long",))
    assert [r[:2] for r in longs] == [r[:2] for r in got if r[1] != "short"]
