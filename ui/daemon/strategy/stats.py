"""The basic statistics of one strategy per sample — IS, OOS1, both joined, and OOS2 behind its door."""

import pandas as pd

from core.study import blocks
from ui.daemon.strategy import costcurve
from ui.daemon.tearsheet import oos2, tradestats

HARVEST = {"IS": "IS", "OOS1": "OOS", "OOS2": "OOS2"}     # the window's names → the cosecha's
JOINED = "IS+OOS1"                                         # both samples as one, IS's curve first
DEFAULT_UNIT = "USD por operación"                         # owner, 2026-09-30 (feedback §3.1)


def _figure(value: object) -> float | None:
    """A metric of the cosecha as JSON can carry it: float32 widened, NaN as missing."""
    return None if value is None or pd.isna(value) else float(value)


def _pf(pnl: pd.Series) -> float | None:
    """Gross profit over gross loss; None without a losing trade."""
    loss = -pnl[pnl < 0].sum()
    return float(pnl[pnl > 0].sum() / loss) if loss > 0 else None


def _histogram(values: pd.Series, unit: str, sample: str) -> dict:
    """The trade distribution of one sample as a contract `distribution` block."""
    block = blocks.distribution(
        f"Distribución de las operaciones, {sample}", unit, values.to_numpy(), float(values.mean()),
        f"Una barra por tramo de retorno por operación ({unit}). La banda sombreada va del "
        f"percentil 5 al 95, la línea discontinua es la mediana y la "
        "continua la media.", bins=40)
    return block | {"mark": "media", "row_unit": "$"}


def one(sample: str, equity: pd.DataFrame, trades: pd.DataFrame, metrics: dict) -> dict:
    """One sample's figures and, per unit, its return distribution.

    Args:
        sample: IS, OOS1, IS+OOS1 or OOS2.
        equity: The sample's daily cumulative P&L (`day`, `equity`).
        trades: The sample's trades.
        metrics: The cosecha's SQX metrics row; the joined sample has no Sharpe there.

    Returns:
        `rows` [{label, value, unit}] and
        `returns` {unit: {rows, histogram}}.
    """
    pnl = trades["Profit/Loss"].astype(float)
    curve = equity.sort_values("day")["equity"].astype(float).tolist()
    sharpe = metrics.get(f"Sharpe Ratio [{HARVEST[sample]}]") if sample in HARVEST else None
    rows = [{"label": "Operaciones", "value": len(trades), "unit": ""},
            {"label": "Net Profit (SQX, suma de operaciones)", "value": float(pnl.sum()), "unit": "USD"},
            {"label": "Profit Factor", "value": _pf(pnl), "unit": ""},
            {"label": "Win Rate", "value": float((pnl > 0).mean() * 100) if len(pnl) else None,
             "unit": "%"},
            {"label": "DD máximo (curva diaria de SQX)", "value": costcurve.drawdown(curve),
             "unit": "USD"},
            {"label": "Sharpe (SQX)", "value": _figure(sharpe), "unit": ""}]
    returns = {}
    for unit in tradestats.UNITS:
        values = tradestats.returns(trades, unit)
        short = tradestats.SHORT[unit]
        returns[unit] = {"rows": [{"label": k, "value": v, "unit": "" if "asimetría" in k
                                   or "curtosis" in k else short}
                                  for k, v in tradestats.shape(values).items()],
                         "histogram": _histogram(values, short, sample) if len(values) else None}
    return {"rows": rows, "returns": returns}


def joined(data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """IS and OOS1 as one sample: OOS's daily curve continued from IS's last value.

    Returns:
        (the daily curve, the trades).
    """
    eq = data["equity"][data["equity"]["sample"].isin(("IS", "OOS"))].sort_values(["sample", "day"])
    first = eq[eq["sample"] == "IS"]["equity"]
    lift = (eq["sample"] == "OOS") * (float(first.iloc[-1]) if len(first) else 0.0)
    trades = data["trades"][data["trades"]["sample"].isin(("IS", "OOS"))]
    return eq.assign(equity=eq["equity"] + lift), trades


def build(project: str, data: dict, live: bool) -> dict:
    """Every sample of one strategy.

    Args:
        project: Project name, whose ledger opens OOS2.
        data: `harvest.read`'s dict, live or archived.
        live: False for an archived version, which never holds OOS2.

    Returns:
        `strategy`, `harvest_day`, `units`, `default_unit`, and `samples` {IS, OOS1, IS+OOS1,
        OOS2}: each `one`'s dict, or `{blocked, why?}` for OOS2 while sealed or without export.
    """
    samples = {}
    for sample in ("IS", "OOS1"):
        tag = HARVEST[sample]
        samples[sample] = one(sample, data["equity"][data["equity"]["sample"] == tag],
                              data["trades"][data["trades"]["sample"] == tag], data["metrics"])
    equity, trades = joined(data)
    samples[JOINED] = one(JOINED, equity, trades, data["metrics"])
    locked = oos2.blocked(project)
    if locked:
        samples["OOS2"] = locked
    else:
        got = oos2.read(project, data["identity"]) if live else "el archivo no guarda OOS2"
        samples["OOS2"] = ({"blocked": got} if isinstance(got, str) else
                           one("OOS2", got["equity"], got["trades"], got["metrics"]))
    return {"strategy": data["strategy"], "harvest_day": data["day"],
            "units": list(tradestats.UNITS), "default_unit": DEFAULT_UNIT, "samples": samples}
