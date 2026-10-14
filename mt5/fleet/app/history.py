"""What the collector keeps per account: every deal since it opened, the minute curve, the floating excursions."""

import json
from datetime import datetime, timezone

import pandas as pd

from core import fleetpaths

BALANCE_TYPE = 2  # DEAL_TYPE_BALANCE: deposits, withdrawals


def deals(login: int) -> list[dict] | None:
    """Every deal since the account opened (`<login>.history.json`), server clock; None until the collector has it."""
    f = fleetpaths.live_dir() / f"{login}.history.json"
    return json.loads(f.read_text(encoding="utf-8"))["deals"] if f.exists() else None


def minutes(login: int, server_days: list[int]) -> pd.DataFrame | None:
    """The account's minute rows (`server_time`, `equity`, `connected`…) on these server days, oldest first.

    Args:
        login: The account.
        server_days: Server epochs inside each wanted day; each day is one parquet file.

    Returns:
        None when none of the days has a file.
    """
    names = {
        datetime.fromtimestamp(d, timezone.utc).strftime("%Y-%m-%d")
        for d in server_days
    }
    files = [fleetpaths.history_dir(login) / f"{n}.parquet" for n in sorted(names)]
    frames = [pd.read_parquet(f) for f in files if f.exists()]
    return pd.concat(frames, ignore_index=True) if frames else None


def excursions(login: int) -> dict[str, dict] | None:
    """The floating profit's lowest and highest per position ticket ever seen; None until the collector has it."""
    f = fleetpaths.history_dir(login) / "excursions.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def trades(rows: list[dict]) -> list[dict]:
    """Group deals by position into trades.

    Args:
        rows: Deals of one account (`position`, `type`, `entry`, `time`, `profit`, `swap`,
            `commission`, `fee`, `symbol`, `magic`, `comment`).

    Returns:
        Per position that has an entry deal: `position`, `symbol`, `side`, `magic`, `comment`,
        `open` (server epoch), `close` (None while open), `net` (all its deals) and `volume`.
        Balance operations are not trades.
    """
    grouped: dict[int, list[dict]] = {}
    for d in rows:
        if d["type"] != BALANCE_TYPE:
            grouped.setdefault(d["position"], []).append(d)
    out = []
    for pos, ds in grouped.items():
        entry = [d for d in ds if d["entry"] in (0, 2)]
        exits = [d for d in ds if d["entry"] != 0]
        if not entry:
            continue
        e = min(entry, key=lambda d: d["time"])
        out.append(
            {
                "position": pos,
                "symbol": e["symbol"],
                "side": "buy" if e["type"] == 0 else "sell",
                "magic": e["magic"],
                "comment": e["comment"],
                "open": e["time"],
                "volume": e["volume"],
                "close": max(d["time"] for d in exits) if exits else None,
                "net": sum(
                    d["profit"] + d["swap"] + d["commission"] + d["fee"] for d in ds
                ),
            }
        )
    return out
