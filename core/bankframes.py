"""An `.abk` loaded by `core.bankfile`, as the strategies' XML, statistics and daily equity."""

import numpy as np
import pandas as pd

from core import bankfile


def texts(bank: dict) -> dict[str, str]:
    """Each strategy's XML by name; its identity is `core.sqxfile._hashed` of the text."""
    raw, ends = bank["xml"], np.cumsum(bank["index"]["xml_len"], dtype="i8")
    return {name: bytes(raw[end - size:end]).decode("utf-8")
            for name, end, size in zip(bank["names"], ends.tolist(), bank["index"]["xml_len"].tolist())}


def unbound(bank: dict, stats: dict[str, dict], block: int) -> str:
    """Why the bank's trades are not the result stored in the .sqx files, or "" when they are.

    Args:
        bank: What `bankfile.load` returned.
        stats: Strategy name -> `core.sqxstats.stats` of its file on disk.
        block: The sample block the databank filled (10 or 20; `sqxview.measured`).

    Returns:
        "" when each strategy's filled main-result orders count `NumberOfTrades` and add up to
        `NetProfit` (🔬 2026-10-13, 1,114 strategies of four harvests: counts equal for all, net
        within 4e-3 absolute and 6e-8 relative -- the stats are float32), else the first one
        that does not, with both numbers. A dump of other costs or of an older run cannot pass.
    """
    o = bank["orders"]
    o = o[(o["flags"] & 1 == 0) & (bank["labels"][o["res"]] == bank["strings"][bank["index"]["main"]][o["strategy"]])]
    n = np.bincount(o["strategy"], minlength=len(bank["names"]))
    net = np.bincount(o["strategy"], weights=bankfile.half_up(o["pl"], 2), minlength=len(bank["names"]))
    for i, name in enumerate(bank["names"]):
        st = stats.get(name, {}).get(block, {})
        want = st.get("NetProfit", np.nan)
        if n[i] != st.get("NumberOfTrades") or not abs(net[i] - want) <= 0.01 + 1e-6 * abs(want):
            return f"{name}: el .abk lleva {n[i]} operaciones y {net[i]:.2f} de beneficio, el .sqx {st.get('NumberOfTrades')} y {st.get('NetProfit')}"
    return ""


def _who(bank: dict, strategy: np.ndarray, res: np.ndarray) -> dict:
    """The `strategy` and `result` columns of a per-result frame."""
    used = np.unique(res)
    return {"strategy": pd.Categorical.from_codes(strategy.astype("i8"), bank["names"]),
            "result": pd.Categorical.from_codes(np.searchsorted(used, res), bank["strings"][used])}


def metrics(bank: dict) -> pd.DataFrame:
    """The stored statistics of every result and sample type.

    Returns:
        One row per (strategy, result, sample), in file order: `strategy`, `result`, `sample`
        (SQX's sample-type code, as `core.sqxstats.IS/OOS/FULL`) and one column per key —
        float64, and nullable Int64 for the keys typed `i` or `l`: a NaN there is a key that
        block does not carry (🔬 2026-10-13: 17 of 2,618 stored blocks lack four keys).
    """
    s = bank["stats"]
    f = pd.DataFrame(_who(bank, s["strategy"], s["res"]) | {"sample": s["sample"].astype("int64")})
    values = pd.DataFrame(np.asarray(s["v"]).reshape(len(s), len(bank["keys"])),
                          columns=[name for name, _ in bank["keys"]])
    return pd.concat([f, values.astype({name: "Int64" for name, kind in bank["keys"] if kind != "f"})],
                     axis=1)


def equity(bank: dict) -> pd.DataFrame:
    """The daily equity of every result of every strategy.

    Returns:
        `strategy`, `result`, `day` (datetime64[ns]) and `equity` (float64, exactly the
        float32 SQX holds), one row per point, runs in file order.
    """
    runs, points = bank["eqruns"], bank["equity"]
    who = _who(bank, np.repeat(runs["strategy"], runs["n"]), np.repeat(runs["res"], runs["n"]))
    return pd.DataFrame(who | {"day": points["day"].astype("datetime64[D]").astype("datetime64[ns]"),
                               "equity": points["v"].astype("f8")})
