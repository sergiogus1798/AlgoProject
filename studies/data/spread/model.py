"""The ways the daily relative spread can be reconstructed where Darwinex has no ticks.

Every model shares one contract: `fit(days) -> params` on `measure.days()` rows, and
`predict(params, days) -> Series` of the mean relative spread for any day carrying `rv` and
`price` — which Dukascopy gives for every year. The log models are fitted in log space and
brought back with the smearing factor exp(σ²/2), so they predict the mean, not the median.

| model | holds fixed | lets move |
|---|---|---|
| `relativo` | the spread as a fraction of price | nothing |
| `puntos` | the spread in price units | its weight in % as price moves |
| `volatilidad` | the elasticity to daily volatility | the spread with the day's volatility |
| `volatilidad_precio` | the elasticities to volatility and price level | both |
"""

import numpy as np
import pandas as pd


def _design(days: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """An intercept and the logs of the named columns."""
    return np.column_stack([np.ones(len(days))] + [np.log(days[c].to_numpy()) for c in cols])


def _fit_log(days: pd.DataFrame, cols: list[str]) -> dict:
    """Least squares of log(rel) on the logs of `cols`, with its smearing factor."""
    x, y = _design(days, cols), np.log(days["rel"].to_numpy())
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return {"cols": cols, "beta": beta.tolist(), "smear": float(np.exp(np.var(y - x @ beta) / 2))}


def _predict_log(params: dict, days: pd.DataFrame) -> pd.Series:
    """exp(Xβ) × smear, one value per day."""
    x = _design(days, params["cols"])
    return pd.Series(np.exp(x @ np.array(params["beta"])) * params["smear"], days.index)


MODELS = {
    "relativo": (lambda d: {"rel": float(d["rel"].mean())},
                 lambda p, d: pd.Series(p["rel"], d.index)),
    "puntos": (lambda d: {"spread": float(d["spread"].mean())},
               lambda p, d: p["spread"] / d["price"]),
    "volatilidad": (lambda d: _fit_log(d, ["rv"]), _predict_log),
    "volatilidad_precio": (lambda d: _fit_log(d, ["rv", "price"]), _predict_log),
}


def fit(name: str, days: pd.DataFrame) -> dict:
    """One model's parameters on the given days."""
    return MODELS[name][0](days)


def predict(name: str, params: dict, days: pd.DataFrame) -> pd.Series:
    """One model's mean relative spread for each of the given days."""
    return MODELS[name][1](params, days)
