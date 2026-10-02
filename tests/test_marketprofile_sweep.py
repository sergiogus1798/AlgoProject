"""Known-answer tests of the profile's wider frame, its position kernel and its exit sweep.

A bar must never read the D1 bar of its own day (known values, then poison); one position at a
time with the exit by signal, cap, trail and stop; and the sweep's plateau counts the neighbours
that pay, so an isolated spike never beats a plateau.

Run: python3 tests/test_marketprofile_sweep.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.research.marketProfile import higher, inputs, series, sweep, sweepjudge  # noqa: E402
from studies.research.marketProfile.measure import position, rules  # noqa: E402


def same_frame(a: dict, b: dict, where: np.ndarray | slice) -> int:
    """Assert every closed-day D1 value of two framed series is equal on `where`; how many."""
    count = 0
    for key in (k for k in a if k.startswith("d1_") and k != "d1_open"):
        pairs = [(a[key][n], b[key][n]) for n in a[key]] if isinstance(a[key], dict) else [
            (a[key], b[key])]
        for left, right in pairs:
            assert np.array_equal(left[where], right[where], equal_nan=True), key
            count += 1
    return count


def test_daily_context(cfg: dict) -> None:
    """A bar reads the D1 bar of the day before, never its own: known values, then poison."""
    index = pd.date_range("2015-01-05", periods=40 * 24, freq="1h")
    index = index[index.weekday < 5]
    day = pd.factorize(index.normalize())[0]
    level = np.log(100.0 + day)                           # every close of day d is log(100 + d)
    x = {"o": level, "h": level + 0.01 * (1 + day % 3), "l": level - 0.02, "c": level}
    cal = series.calendar(index, "H1", cfg)
    knobs = {"momentum": [2], "means": [2], "channels": [1, 3], "atr": 2, "vol": [1, 2], "rsi": 2,
             "median": 3, "band": [2], "streak": 2, "outside": 2, "narrow": 2, "squeeze": [1, 3]}
    got = higher.context(series.derive(x, cfg["derive"]), cal, knobs)
    high = np.log(100.0 + np.arange(day.max() + 1)) + 0.01 * (1 + np.arange(day.max() + 1) % 3)
    close = np.log(100.0 + np.arange(day.max() + 1))
    assert np.isnan(got["d1_hi"][1][day == 0]).all()                 # no day has closed yet
    for d in (1, 5, 17):
        here = day == d
        assert np.allclose(got["d1_hi"][1][here], high[d - 1])       # yesterday's high, all day
        assert np.allclose(got["d1_lo"][1][here], close[d - 1] - 0.02)
    for d in (5, 17):
        assert np.allclose(got["d1_hi"][3][day == d], high[d - 3:d].max())
        assert np.allclose(got["d1_mom"][2][day == d], close[d - 1] - close[d - 3])
        assert np.allclose(got["d1_above"][2][day == d], (close[d - 1] - close[d - 2]) / 2)
    cut = 12
    y = {k: np.where(day >= cut, v + 5.0, v) for k, v in x.items()}  # poison day `cut` onwards
    bad = higher.context(series.derive(y, cfg["derive"]), cal, knobs)
    seen = day <= cut                                # day `cut` itself still reads day cut - 1
    assert same_frame(got, bad, seen) > 15
    assert np.allclose(got["d1_open"][day == 5], level[day == 5][0])     # its own day's open
    assert np.array_equal(got["d1_open"][day < cut], bad["d1_open"][day < cut])
    assert np.allclose(got["d1_ibs"][day == 5], 0.02 / (0.02 + 0.01 * (1 + 4 % 3)))
    assert not np.allclose(got["d1_hi"][1][day == cut + 1], bad["d1_hi"][1][day == cut + 1])
    up = higher.mirror(got)
    assert np.allclose(up["d1_hi"][1][day == 5], -(close[4] - 0.02))  # the mirror's top is the low
    assert np.allclose(up["d1_mom"][2][day == 5], -(close[4] - close[2]))
    print("contexto D1: cada barra lee el día anterior ya cerrado; envenenar el día en curso y "
          "los siguientes no cambia nada de lo que ve")


def test_position() -> None:
    """One position at a time, fills at the next open; the exit by signal, by cap and by trail."""
    close = np.array([0, 0, 0, 1, 2, 3, 2.5, 1.9, 1.9, 1.9, 1.9, 1.9])
    enter = np.array([0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0], dtype=bool)
    leave = np.zeros(12, dtype=bool)
    leave[5] = True
    ruler, none = np.ones(12), np.zeros(12, dtype=bool)
    assert [a.tolist() for a in position.walk(enter, leave, 0, 0.0, close, ruler)] == [[3], [6]]
    assert [a.tolist() for a in position.walk(enter, none, 2, 0.0, close, ruler)] == [[3, 7], [5, 9]]
    assert [a.tolist() for a in position.walk(enter, none, 0, 1.0, close, ruler)] == [[3], [8]]
    stopped = position.walk(enter, none, 0, 0.0, np.array([5, 5, 5, 4.5, 3.9, 9, 9, 9, 9, 9, 9, 9.0]),
                            ruler, 1.0)
    assert [a.tolist() for a in stopped] == [[3], [5]]      # 3.9 is one ruler under the signal's 5
    clockless = {"hour", "weekday", "day", "bands", "ranges", "weekdays", "year"}
    source = Path(rules.__file__).read_text(encoding="utf-8")
    assert not any(f'cal["{k}"]' in source for k in clockless)       # a rule never reads the clock
    print("posición: una a la vez, entrada y salida en la apertura siguiente; salida por señal, "
          "por tope y por trailing")


def test_sweep(cfg: dict) -> None:
    """The sweep tries every entry, parameter and exit; a plateau counts the neighbours that pay."""
    spec = cfg["sweep"]["entries"]["extreme"]
    names = [e[0] for e in sweep.exits(spec, cfg["sweep"], 24)]
    assert names == ["hold0.5x", "hold1x", "hold2x", "hold4x", "trail2", "trail4", "mean20",
                     "mean5", "stop2_hold2x"]
    assert sweep.exits(cfg["sweep"]["entries"]["ibs_low"], cfg["sweep"], 24)[1][2] == 24
    assert set(sweep.ENTRIES) == set(cfg["sweep"]["entries"])

    def row(param: float, label: str, multiple: float, p: float) -> dict:
        """One variant of the `extreme` entry: stable and frequent, paying `multiple` costs."""
        return {"symbol": "AAA", "timeframe": "H1", "direction": "long", "family": "reversion",
                "entry": "extreme", "param": param, "exit": label, "p": p, "multiple": multiple,
                "measure": f"extreme_{param:g}_{label}", "years_with_sign": 9, "years": 10,
                "trades_per_year": 80.0, "n_trades": 800.0, "z": 5.0}
    rows = pd.DataFrame(
        [row(2.0, "hold1x", 3.0, 1e-6), row(1.5, "hold1x", 2.5, 0.5), row(3.0, "hold1x", 2.2, 0.5),
         row(2.0, "hold2x", 0.5, 0.5), row(2.0, "hold0.5x", 0.1, 0.5),     # a plateau across params
         row(2.0, "mean20", 9.0, 1e-6), row(1.5, "mean20", 0.2, 0.5), row(3.0, "mean20", -1.0, 0.5)])
    got = sweepjudge.judged(rows, cfg).set_index("measure")
    assert got.loc["extreme_2_hold1x", ["neighbours", "plateau"]].tolist() == [4, 2]
    assert got.loc["extreme_2_hold1x", "on_plateau"]
    assert got.loc["extreme_2_mean20", ["neighbours", "plateau"]].tolist() == [2, 0]   # a spike
    assert got.loc["extreme_2_mean20", "passes"] and not got.loc["extreme_2_mean20", "on_plateau"]
    top = sweepjudge.best(got.reset_index()).iloc[0]
    assert (top["exit"], top["variants"], top["plateau_any"]) == ("hold1x", 8, True)
    print("barrido: nueve salidas por entrada; la meseta cuenta vecinos que pagan y el pico "
          "aislado de 9× no gana a la meseta de 3×")


def main() -> None:
    """Run every test."""
    cfg = inputs.config(["nulls.seed=7"])
    test_daily_context(cfg)
    test_position()
    test_sweep(cfg)
    print("OK test_marketprofile_sweep")


if __name__ == "__main__":
    main()
