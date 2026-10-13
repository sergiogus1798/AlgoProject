"""An `.abk` loaded by `core.bankfile`, as the strategies' XML, statistics and daily equity."""

import numpy as np
import pandas as pd

from core import bankfile


def texts(bank: dict) -> dict[str, str]:
    """Each strategy's XML by name; its identity is `core.sqxfile._hashed` of the text."""
    raw, ends = bank["xml"], np.cumsum(bank["index"]["xml_len"], dtype="i8")
    return {name: bytes(raw[end - size:end]).decode("utf-8")
            for name, end, size in zip(bank["names"], ends.tolist(), bank["index"]["xml_len"].tolist())}


def unbound(bank: dict, stats: dict[str, dict], block: int, markets: dict[str, dict] | None = None) -> str:
    """Why the bank's trades are not the result stored in the .sqx files, or "" when they are.

    Args:
        bank: What `bankfile.load` returned.
        stats: Strategy name -> `core.sqxstats.stats` of its file on disk (the main result).
        block: The sample block the databank filled (10 or 20; `sqxview.measured`).
        markets: Strategy name -> `core.sqxstats.every` of its file. Required for a bank in data
            mode "all" (several markets): every result but "Portfolio" is bound; ignored in "main".

    Returns:
        "" when, per strategy and per market, the filled orders count `NumberOfTrades` and add up
        to `NetProfit` (🔬 2026-10-13, 1,114 strategies of four harvests, main result: counts equal
        for all, net within 4e-3 absolute and 6e-8 relative -- the stats are float32), else the
        first that does not, naming strategy and market with both numbers. A dump of other costs or
        of an older run cannot pass, nor can a market whose trades the .sqx does not know.
    """
    if bank["data"] == "all" and markets is None:
        return "el .abk lleva varios mercados y no se pasaron los resultados por mercado del .sqx"
    labels, names = bank["labels"], bank["names"]
    o = bank["orders"]
    o = o[o["flags"] & 1 == 0]
    size, width = len(names), len(labels)
    at = o["strategy"].astype("i8") * width + o["res"]
    n = np.bincount(at, minlength=size * width).reshape(size, width)
    net = np.bincount(at, weights=bankfile.half_up(o["pl"], 2), minlength=size * width).reshape(size, width)
    for i, name in enumerate(names):
        if bank["data"] == "all":
            want = {k: v.get(block, {}) for k, v in markets.get(name, {}).items() if not k.startswith("Portfolio")}
        else:
            want = {str(bank["strings"][bank["index"]["main"]][i]): stats.get(name, {}).get(block, {})}
        for label, st in want.items():
            cols = np.flatnonzero(labels == label)
            count, total, goal = n[i, cols].sum(), net[i, cols].sum(), st.get("NetProfit", np.nan)
            if count != st.get("NumberOfTrades") or not abs(total - goal) <= 0.01 + 1e-6 * abs(goal):
                return (f"{name} ({label}): el .abk lleva {count} operaciones y {total:.2f} de beneficio, "
                        f"el .sqx {st.get('NumberOfTrades')} y {st.get('NetProfit')}")
        if bank["data"] == "all":
            seen = np.flatnonzero(n[i])
            if extra := [labels[c] for c in seen if labels[c] not in want]:
                return f"{name} ({extra[0]}): el .abk lleva operaciones de un mercado que el .sqx no tiene"
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
