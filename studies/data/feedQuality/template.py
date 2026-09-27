"""What a strategy's own rules say about which bars it can be filled on: its orders and its stop."""

import re
import zipfile
from pathlib import Path

from core.paths import MASTER, WORKERS, databank_dir
from sqx.projects.orders import PENDING, PORTFOLIO, carried

# An exit parameter is live when its formula is anything but SQX's `.None`. SQX writes the
# attributes in no fixed order, so `key=` is not always the first one.
EXIT = re.compile(r'<Param\b[^>]*\bkey="#(StopLoss\.StopLoss|ProfitTarget\.ProfitTarget|'
                  r'TrailingStop\.TrailingStop)#"[^>]*>\s*<Formula key="SQ\.Formulas\.[\w.]*?(\.None)?"')


def find(install: Path, project: str, databank: str, name: str) -> Path | None:
    """A strategy's .sqx, first where the harvest says it was, then on any other install.

    Returns:
        Its path, or None when no install still holds it: a databank is rebuilt and
        resynced, so a missing file is ordinary and that strategy goes unjudged.
    """
    for where in [install, MASTER] + [w["path"] for w in WORKERS.values()]:
        path = databank_dir(project, databank, where) / f"{name}.sqx"
        if path.is_file():
            return path
    return None


def rules(strategy: Path) -> dict:
    """Which of the feed's columns decides whether this strategy's trades touch an anomaly.

    Args:
        strategy: A .sqx file.

    Returns:
        {"pending": entries by stop or limit order, "exit_orders": a live stop loss, profit
        target or trailing stop, "stop": a live stop loss or trailing stop, "column": "mecha"
        when an order can be filled by a wick (either of the first two), else "cierre"}.
        Owner's answer 3.4: the rule is read from the strategy, never chosen per run.
    """
    with zipfile.ZipFile(strategy) as z:
        text = z.read(PORTFOLIO).decode("utf-8", "replace")
    live = {key for key, none in EXIT.findall(text) if not none}
    pending = bool(carried(strategy) & set(PENDING))
    exit_orders = bool(live)
    return {"pending": pending, "exit_orders": exit_orders,
            "stop": bool(live & {"StopLoss.StopLoss", "TrailingStop.TrailingStop"}),
            "column": "mecha" if pending or exit_orders else "cierre"}
