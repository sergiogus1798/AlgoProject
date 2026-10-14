"""The collector's pure parts: a beat's history row, the skip test, and the floating MAE/MFE ledger."""

from datetime import datetime, timezone
from typing import Any

HISTORY_COLUMNS = ["written_gmt", "server_time", "balance", "equity", "floating", "margin",
                   "connected", "autotrading", "ping_us", "n_positions"]


def history_row(beat: dict) -> dict[str, Any]:
    """One minute-history row from a beacon beat."""
    row = {k: beat[k] for k in HISTORY_COLUMNS if k != "n_positions"}
    row["n_positions"] = len(beat["positions"])
    return row


def is_new(beat: dict, last_written_gmt: int | None) -> bool:
    """False when the beat is the one already stored (the VPS has gone silent)."""
    return beat["written_gmt"] != last_written_gmt


def server_day(beat: dict) -> str:
    """The beat's server calendar day, `YYYY-MM-DD` — the server epoch is read as if it were UTC."""
    return datetime.fromtimestamp(beat["server_time"], timezone.utc).strftime("%Y-%m-%d")


def update_excursions(excursions: dict, beat: dict) -> dict[str, Any]:
    """Fold a beat's open positions into the per-ticket floating min and max profit.

    Args:
        excursions: `{ticket: {magic, symbol, side, volume, time, min_profit, max_profit, last_seen}}`.
        beat: A beacon beat; a ticket no longer open stays as it was last seen.

    Returns:
        The same dict, updated in place.
    """
    for p in beat["positions"]:
        e = excursions.setdefault(str(p["ticket"]), {
            "magic": p["magic"], "symbol": p["symbol"], "side": p["side"], "volume": p["volume"],
            "time": p["time"], "min_profit": p["profit"], "max_profit": p["profit"]})
        e["min_profit"] = min(e["min_profit"], p["profit"])
        e["max_profit"] = max(e["max_profit"], p["profit"])
        e["last_seen"] = beat["written_gmt"]
    return excursions
