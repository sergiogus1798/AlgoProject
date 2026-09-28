"""One strategy's two equity curves: SQX's daily one, and the same at Darwinex's real spread and slippage."""

from pathlib import Path

import pandas as pd

from ui.daemon.results import store

# The `spread` study's trade column the window calls «real»: both costs, the owner's default
# reading (`reprice.judge`), the same column the databank's aggregate curve reads.
REAL = "Profit/Loss spread y slippage reales"
COLUMNS = ["identity", "sample", "Close time", "Profit/Loss", REAL]
NO_REPORT = "sin informe del estudio spread para esta estrategia"


def _rows(folders: list[Path], name: str, identity: str) -> tuple[pd.DataFrame, str] | None:
    """The strategy's repriced trades from the newest spread report that holds them.

    Args:
        folders: `<day>/spread/` folders, newest first.
        name: The strategy's name, which names a report run on it alone.
        identity: Its identity; a row is taken only under it.

    Returns:
        (its rows, the report's day), or None. A run on this strategy alone writes
        `estrategias/<name>.trades.parquet`; a population run, `trades.parquet`.
    """
    for folder in folders:
        for path in (folder / "estrategias" / f"{name}.trades.parquet", folder / "trades.parquet"):
            if path.is_file():
                rows = pd.read_parquet(path, columns=COLUMNS, filters=[("identity", "==", identity)])
                if len(rows):
                    return rows, folder.parent.name
    return None


def reports(project: str, databank: str) -> list[Path]:
    """The live `spread` report folders of a databank, newest first."""
    return [store.bank(project, databank) / d / "spread" for d in store.days(project, databank, "spread")]


def frozen(folder: Path, databank: str) -> list[Path]:
    """The `spread` report folders an archived version froze for that databank, newest first."""
    bank = folder / "reports" / databank.replace(" ", "_")
    return sorted(bank.glob("*/spread"), reverse=True)


def drawdown(curve: list[float]) -> float:
    """The worst fall from a peak of a cumulative curve, in money, as a negative number."""
    peak, worst = 0.0, 0.0
    for v in curve:
        peak = max(peak, v)
        worst = min(worst, v - peak)
    return worst


def curve(data: dict, spread: list[Path]) -> dict:
    """The two curves of one strategy, IS then OOS on one axis.

    Args:
        data: `harvest.read`'s dict (live or archived).
        spread: Where its `spread` reports are, newest first.

    Returns:
        `days`, `sqx` (cumulative daily P&L, OOS continuing from IS's last value), `real` (the
        same plus what the real costs change on each closing day, or None with `real_why`),
        `split` (index of the first OOS day), `real_net` and `sqx_net` per sample (each its
        own backtest from 0), `real_dd`, and `source`. The real curve is SQX's daily curve
        corrected by the repriced trades, so both share every day and differ only by cost.
    """
    eq = data["equity"].sort_values(["sample", "day"], kind="stable")      # IS sorts before OOS
    eq = eq.assign(pnl=eq.groupby("sample")["equity"].diff().fillna(eq["equity"]))
    found = _rows(spread, data["strategy"], data["identity"])
    real = real_net = real_dd = None
    if found is not None:
        rows, day = found
        rows = rows.assign(day=rows["Close time"].dt.normalize(), delta=rows[REAL] - rows["Profit/Loss"])
        fix = rows.groupby(["sample", "day"], as_index=False)["delta"].sum()
        eq = eq.merge(fix, on=["sample", "day"], how="outer").fillna({"pnl": 0.0, "delta": 0.0})
        eq = eq.sort_values(["sample", "day"], kind="stable")
        real = (eq["pnl"] + eq["delta"]).cumsum().round(2).tolist()
        real_net = {s: float(g[REAL].sum()) for s, g in rows.groupby("sample")}
        real_dd = drawdown(real)
    sqx = eq["pnl"].cumsum().round(2).tolist()
    oos = (eq["sample"] == "OOS").tolist()
    return {"days": [f"{d:%Y-%m-%d}" for d in eq["day"]], "sqx": sqx, "real": real,
            "split": oos.index(True) if True in oos else None,
            "sqx_net": {s: float(g["pnl"].sum()) for s, g in eq.groupby("sample")},
            "real_net": real_net, "real_dd": real_dd, "sqx_dd": drawdown(sqx),
            "real_why": None if real else NO_REPORT,
            "source": f"cosecha del {data['day']}"
                      + (f" · spread real del {found[1]}" if found else "")}
