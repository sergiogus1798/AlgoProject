"""Known-answer tests of the market profile, and the proof that it never reads past `build`.

Synthetic bars built so the answer is known by construction: a persistent series must score
trend, an anti-persistent one must score reversion, white noise must pass no filter. A feed
poisoned after the build end must give the same profile as one that ends there, D1 context
included. The D1 look-ahead, the position kernel and the sweep: tests/test_marketprofile_sweep.py.

Run: python3 tests/test_marketprofile.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, barstore  # noqa: E402
from studies.research.marketProfile import inputs, many, one, series  # noqa: E402

BARS = 20000
SYMBOL = "EURUSD"


def synthetic(phi: float, seed: int, start: str = "2010-01-04") -> pd.DataFrame:
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
    return pd.DataFrame({"Open": opens, "High": np.maximum(opens, close) * (1 + wick[0]),
                         "Low": np.minimum(opens, close) * (1 - wick[1]), "Close": close},
                        index=pd.date_range(start, periods=BARS, freq="1h"))


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


def profile(bars: pd.DataFrame, cfg: dict) -> dict:
    """One synthetic cell measured and judged alone."""
    got = one.run(SYMBOL, "H1", bars, assetdata.load(SYMBOL), cfg)
    judged = many.run(pd.DataFrame(got["rows"]), cfg)
    return {"measures": judged["measures"],
            "scores": judged["scores"].set_index(["direction", "family"])}


def test_families(cfg: dict) -> None:
    """Persistence scores trend, anti-persistence scores reversion, noise passes nothing."""
    trend = profile(synthetic(0.2, 1), cfg)
    for direction in ("long", "short"):
        s = trend["scores"].loc[direction]
        assert s.loc["tendencia", "score"] > 15 > 5 > s.loc["reversion", "score"], s["score"]
        assert s.loc["tendencia", "measures_significant"] > 0, s
    m = trend["measures"].set_index("measure")
    assert m.loc["vr4", "significant"] and not m.loc["vr4_low", "significant"]
    print(f"tendencia  AR(+0.2): tendencia {trend['scores'].loc[('long', 'tendencia'), 'score']:.0f}"
          f", reversion {trend['scores'].loc[('long', 'reversion'), 'score']:.0f}")

    revert = profile(synthetic(-0.2, 2), cfg)
    for direction in ("long", "short"):
        s = revert["scores"].loc[direction]
        assert s.loc["reversion", "score"] > 15 > 5 > s.loc["tendencia", "score"], s["score"]
    m = revert["measures"].set_index("measure")
    assert m.loc["vr4_low", "significant"] and not m.loc["vr4", "significant"]
    print(f"reversion  AR(-0.2): reversion {revert['scores'].loc[('long', 'reversion'), 'score']:.0f}"
          f", tendencia {revert['scores'].loc[('long', 'tendencia'), 'score']:.0f}")

    noise = profile(synthetic(0.0, 3), cfg)
    assert not noise["measures"]["significant"].any(), noise["measures"].query("significant")
    assert not noise["scores"]["passes"].any() and not noise["scores"]["fragile"].any()
    print(f"ruido blanco: 0 de {len(noise['measures'])} pruebas significativas, "
          f"puntuación máxima {noise['scores']['score'].max():.0f}")


def test_build_only(cfg: dict) -> None:
    """Bars after the build end never reach a measure."""
    lo, hi = inputs.span(SYMBOL)
    index = pd.date_range(hi - pd.Timedelta(days=500), hi + pd.Timedelta(days=200), freq="15min")
    rng = np.random.default_rng(4)
    close = 1.2 * np.exp(np.cumsum(rng.normal(0, 0.0005, index.size)))
    feed = pd.DataFrame({"Open": close, "High": close * 1.0002, "Low": close * 0.9998,
                         "Close": close, "Volume": 1.0}, index=index)
    poisoned = feed.copy()
    poisoned.loc[poisoned.index >= hi, ["Open", "High", "Low", "Close"]] *= 1000.0
    real_source, results, frames = barstore.source, [], []
    for frame in (feed[feed.index < hi], poisoned):
        barstore.source = lambda feed_name, columns=None, f=frame: f[columns] if columns else f
        m1 = inputs.minute_bars(SYMBOL, 0)
        assert m1.index.max() < hi and m1.index.min() >= lo
        bars = inputs.bars(m1, "H1")
        assert bars.index.max() < hi
        results.append(pd.DataFrame(one.run(SYMBOL, "H1", bars, assetdata.load(SYMBOL),
                                            cfg)["rows"]))
        frames.append(one.framed(series.logs(bars), series.calendar(bars.index, "H1", cfg), cfg))
    barstore.source = real_source
    assert (poisoned.index >= hi).sum() > 10000
    pd.testing.assert_frame_equal(results[0], results[1])
    assert same_frame(frames[0], frames[1], slice(None)) > 15
    assert np.array_equal(frames[0]["d1_open"], frames[1]["d1_open"])
    assert {"needs_clock", "tag"} <= set(results[0].columns)
    assert inputs.SEGMENT == "build"
    print(f"sólo build: {int((poisoned.index >= hi).sum())} barras envenenadas tras "
          f"{hi.date()} no cambian ninguna de las {len(results[0])} medidas")


def test_fourth_filter(cfg: dict) -> None:
    """A measure that is significant, pays and is stable still fails below the minimum of trades
    a year; an asset's own minimum applies to it alone; nothing under the floor of 35 is accepted."""
    def row(symbol: str, measure: str, per_year: float) -> dict:
        """A measure row that passes the other three filters, at `per_year` trades a year."""
        return {"symbol": symbol, "timeframe": "H1", "direction": "long", "measure": measure,
                "family": "momentum", "p": 1e-6, "multiple": 5.0, "years_with_sign": 9, "years": 10,
                "trades_per_year": per_year}
    rows = pd.DataFrame([row("AAA", "m1", 45.0), row("AAA", "m2", 38.0),
                         row("BBB", "m3", 38.0), row("BBB", "m4", 12.0)])
    filters = dict(cfg["filters"], min_trades_per_year=40, min_trades_per_year_by_asset={"BBB": 35})
    got = many.judged(rows, filters).set_index("measure")
    assert got["frequent"].to_dict() == {"m1": True, "m2": False, "m3": True, "m4": False}
    assert got["passes"].to_dict() == {"m1": True, "m2": False, "m3": True, "m4": False}
    assert got["significant"].all() and got["pays"].all() and got["stable"].all()
    for bad in (dict(min_trades_per_year=34), dict(min_trades_per_year_by_asset={"BBB": 30})):
        try:
            many.judged(rows, dict(filters, **bad))
        except ValueError as error:
            assert "floor of 35" in str(error)
        else:
            raise AssertionError(f"{bad} must be refused")
    assert cfg["filters"]["min_trades_per_year"] == 40
    print("cuarto filtro: 38 op/año no pasa con 40, sí con 35 en el activo que lo nombra")


def test_clock_and_alternative(cfg: dict) -> None:
    """A clock measure never leads nor passes a family that has another; and the alternative
    correction is Benjamini-Hochberg inside each family."""
    def row(measure: str, family: str, p: float, clock: bool, multiple: float = 5.0) -> dict:
        """A trade measure row that pays, is stable and is frequent."""
        return {"symbol": "AAA", "timeframe": "H1", "direction": "long", "measure": measure,
                "family": family, "p": p, "multiple": multiple, "years_with_sign": 9, "years": 10,
                "trades_per_year": 100.0, "n_trades": 1000.0, "needs_clock": clock, "z": 3.0,
                "effect": 1.0, "cost": 0.2}
    rows = pd.DataFrame([row("hour", "sesion", 1e-6, True), row("day_break", "sesion", 0.5, False),
                         row("weekday", "reloj", 1e-6, True),
                         row("trend", "tendencia", 0.04, False)]
                        + [row(f"noise{k}", "patron", 0.2 + k / 100, False) for k in range(40)])
    full = dict(cfg, measures=[{"family": f} for f in ("sesion", "reloj", "tendencia", "patron")])
    got = many.run(rows, full)
    table = got["scores"].set_index("family")
    assert table.loc["sesion", "lead"] == "day_break" and not table.loc["sesion", "passes"]
    assert not table.loc["sesion", "needs_clock"]
    assert table.loc["reloj", "needs_clock"] and table.loc["reloj", "passes"]
    measures = got["measures"].set_index("measure")
    assert measures.loc["hour", "passes"] and measures.loc["hour", "needs_clock"]
    assert not measures.loc["trend", "significant"] and measures.loc["trend", "significant_family"]
    assert not table.loc["tendencia", "passes"] and table.loc["tendencia", "passes_family"]
    print("reloj: una medida de reloj no lidera ni hace pasar a su familia; corrección "
          "alternativa: 0,04 no sobrevive entre 44 pruebas y sí sola en su familia")


def main() -> None:
    """Run every test with a fixed seed and a light null."""
    cfg = inputs.config(["nulls.seed=7", "nulls.draws=400"])
    with threadpool_limits(1):   # BLAS threads fight each other on arrays this small
        test_families(cfg)
        test_build_only(cfg)
        test_fourth_filter(cfg)
        test_clock_and_alternative(cfg)
    print("OK test_marketprofile")


if __name__ == "__main__":
    main()
