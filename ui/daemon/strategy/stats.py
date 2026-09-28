"""The basic statistics of one strategy per sample — IS, OOS1, and OOS2 behind its door."""

import numpy as np
import pandas as pd

from core.study import blocks
from ui.daemon.strategy import costcurve
from ui.daemon.tearsheet import oos2, tradestats

HARVEST = {"IS": "IS", "OOS1": "OOS", "OOS2": "OOS2"}     # the window's names → the cosecha's
DEFAULT_UNIT = "USD por lote"                              # owner, plan 24 §10
SPAN = (1, 99)          # the histogram's range, in percentiles: the tails pile in the end bins


def _figure(value: object) -> float | None:
    """A metric of the cosecha as JSON can carry it: float32 widened, NaN as missing."""
    return None if value is None or pd.isna(value) else float(value)


def _pf(pnl: pd.Series) -> float | None:
    """Gross profit over gross loss; None without a losing trade."""
    loss = -pnl[pnl < 0].sum()
    return float(pnl[pnl > 0].sum() / loss) if loss > 0 else None


def _histogram(values: pd.Series, unit: str, sample: str) -> dict:
    """The trade distribution of one sample as a contract `distribution` block."""
    lo, hi = np.percentile(values, SPAN)
    block = blocks.distribution(
        f"Distribución de las operaciones, {sample}", unit, values.to_numpy(), float(values.mean()),
        f"Una barra por tramo de retorno por operación ({unit}). La banda sombreada va del "
        f"percentil 5 al 95, la línea discontinua es la mediana y la continua la media; las "
        f"operaciones fuera de los percentiles {SPAN[0]}-{SPAN[1]} se acumulan en la primera y "
        "la última barra.", bins=40, span=(float(lo), float(hi)))
    return block | {"mark": "media"}


def one(sample: str, equity: pd.DataFrame, trades: pd.DataFrame, metrics: dict,
        real_net: float | None) -> dict:
    """One sample's figures and, per unit, its return distribution.

    Args:
        sample: IS, OOS1 or OOS2.
        equity: The sample's daily cumulative P&L (`day`, `equity`).
        trades: The sample's trades.
        metrics: The cosecha's SQX metrics row.
        real_net: The net at the real spread and slippage from the `spread` study, None when
            that study has not repriced this strategy.

    Returns:
        `rows` [{label, value, unit, study}] — `study` names what computes a None — and
        `returns` {unit: {rows, histogram}}.
    """
    pnl = trades["Profit/Loss"].astype(float)
    curve = equity.sort_values("day")["equity"].astype(float).tolist()
    tag = HARVEST[sample]
    rows = [{"label": "Operaciones", "value": len(trades), "unit": ""},
            {"label": "Beneficio neto (SQX, suma de operaciones)", "value": float(pnl.sum()), "unit": "USD"},
            {"label": "Beneficio neto con spread y slippage reales (suma de operaciones)", "value": real_net,
             "unit": "USD", "study": "spread"},
            {"label": "Factor de beneficio", "value": _pf(pnl), "unit": ""},
            {"label": "% ganadoras", "value": float((pnl > 0).mean() * 100) if len(pnl) else None,
             "unit": "%"},
            {"label": "DD máximo (curva diaria de SQX)", "value": costcurve.drawdown(curve),
             "unit": "USD"},
            {"label": "Sharpe (SQX)", "value": _figure(metrics.get(f"Sharpe Ratio [{tag}]")), "unit": ""}]
    returns = {}
    for unit in tradestats.UNITS:
        values = tradestats.returns(trades, unit)
        returns[unit] = {"rows": [{"label": k, "value": v, "unit": "" if "asimetría" in k
                                   or "curtosis" in k else unit}
                                  for k, v in tradestats.shape(values).items()],
                         "histogram": _histogram(values, unit, sample) if len(values) else None}
    return {"rows": rows, "returns": returns}


def build(project: str, data: dict, curve: dict, live: bool) -> dict:
    """Every sample of one strategy.

    Args:
        project: Project name, whose ledger opens OOS2.
        data: `harvest.read`'s dict, live or archived.
        curve: `costcurve.curve` of the same strategy, for the real-cost nets.
        live: False for an archived version, which never holds OOS2.

    Returns:
        `strategy`, `harvest_day`, `units`, `default_unit`, and `samples` {IS, OOS1, OOS2}:
        each `one`'s dict, or `{blocked, why?}` for OOS2 while sealed or without export.
    """
    real = curve["real_net"] or {}
    samples = {}
    for sample in ("IS", "OOS1"):
        tag = HARVEST[sample]
        samples[sample] = one(sample, data["equity"][data["equity"]["sample"] == tag],
                              data["trades"][data["trades"]["sample"] == tag], data["metrics"],
                              real.get(tag))
    locked = oos2.blocked(project)
    if locked:
        samples["OOS2"] = locked
    else:
        got = oos2.read(project, data["identity"]) if live else "el archivo no guarda OOS2"
        samples["OOS2"] = ({"blocked": got} if isinstance(got, str) else
                           one("OOS2", got["equity"], got["trades"], got["metrics"], None))
    return {"strategy": data["strategy"], "harvest_day": data["day"],
            "units": list(tradestats.UNITS), "default_unit": DEFAULT_UNIT, "samples": samples}
