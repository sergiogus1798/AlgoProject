"""An `.abk` loaded by `core.bankfile`, as the strategies' XML, statistics and daily equity."""

import numpy as np
import pandas as pd


def texts(bank: dict) -> dict[str, str]:
    """Each strategy's XML by name; its identity is `core.sqxfile._hashed` of the text."""
    raw, ends = bank["xml"], np.cumsum(bank["index"]["xml_len"], dtype="i8")
    return {name: bytes(raw[end - size:end]).decode("utf-8")
            for name, end, size in zip(bank["names"], ends.tolist(), bank["index"]["xml_len"].tolist())}


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
