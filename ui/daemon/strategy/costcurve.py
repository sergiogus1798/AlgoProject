"""One strategy's equity curve: SQX's daily one, IS then OOS1 on one axis."""

from typing import TypedDict


class Curve(TypedDict):
    """The curve payload; `split` is the index of the first OOS day (None without OOS)."""

    days: list[str]
    sqx: list[float]
    split: int | None
    sqx_net: dict[str, float]
    sqx_dd: float
    source: str


def drawdown(curve: list[float]) -> float:
    """The worst fall from a peak of a cumulative curve, in money, as a negative number."""
    peak, worst = 0.0, 0.0
    for v in curve:
        peak = max(peak, v)
        worst = min(worst, v - peak)
    return worst


def curve(data: dict) -> Curve:
    """The curve of one strategy, IS then OOS on one axis.

    Args:
        data: `harvest.read`'s dict (live or archived).

    Returns:
        `days`, `sqx` (cumulative daily P&L, OOS continuing from IS's last value), `split`
        (index of the first OOS day), `sqx_net` per sample (each its own backtest from 0),
        `sqx_dd` and `source`.
    """
    eq = data["equity"].sort_values(["sample", "day"], kind="stable")      # IS sorts before OOS
    eq = eq.assign(pnl=eq.groupby("sample")["equity"].diff().fillna(eq["equity"]))
    sqx = eq["pnl"].cumsum().round(2).tolist()
    oos = (eq["sample"] == "OOS").tolist()
    return {"days": [f"{d:%Y-%m-%d}" for d in eq["day"]], "sqx": sqx,
            "split": oos.index(True) if True in oos else None,
            "sqx_net": {s: float(g["pnl"].sum()) for s, g in eq.groupby("sample")},
            "sqx_dd": drawdown(sqx), "source": f"cosecha del {data['day']}"}
