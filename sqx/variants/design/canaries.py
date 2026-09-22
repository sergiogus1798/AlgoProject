"""The controls: tuples whose result is known before the retest runs, and the pairs that must tie."""

import pandas as pd

RESULTS = ["NetProfit", "NumberOfTrades"]
ORIGIN = "origin"


def _picks(table: pd.DataFrame, count: int) -> list[int]:
    """Which permutations make the sharpest controls.

    Args:
        table: Output of `inputs.known`, indexed by permutation.
        count: How many are wanted.

    Returns:
        Permutation indices: the largest NetProfit, the smallest, then the fewest trades,
        in that order and without repeats. Extremes on purpose -- a chain that lost a
        parameter, loaded the wrong file or silently reused the parent returns a
        plausible middling number. It does not return the maximum of a grid of thousands.
    """
    order = [table["NetProfit"].idxmax(), table["NetProfit"].idxmin(),
             table["NumberOfTrades"].idxmin()]
    return list(dict.fromkeys(order))[:count]


def rows(design: dict, levels: dict[str, list[float]], origin: dict[str, float],
         table: pd.DataFrame, settings: dict) -> list[dict]:
    """Every control row of the batch, the origin first.

    Args:
        design: A parsed brief.
        levels: Every parameter's levels, frozen ones included.
        origin: The parent's own tuple.
        table: Output of `inputs.known`.
        settings: The `canaries` block of `config.yaml`.

    Returns:
        One dict per control, each with its tuple, its stratum and what it is expected to
        come back as. Three kinds, and they fail differently on purpose:

        - **the origin**, stratum `origin`. No expectation attached and none needed: it is
          the parent rebuilt through the factory, so if the rewriting corrupted anything
          this row is the one that stops matching the strategy it came from. It is also
          the row the deletion stage refuses to touch.
        - **known-result canaries**, stratum `canary`. Their NetProfit and trade count are
          what SQX stored for that exact tuple, so they are an absolute check on the whole
          chain -- design, rewrite, load, retest, export.
        - **inert pairs**, stratum `canary`. The origin with one frozen parameter moved as
          far as its rebuilt range goes. The brief froze it because it provably never
          moved a backtest, so each of these must come back equal to the origin. They are
          the only control that tests the freezing decision itself.

        An expectation is on the **in-sample** result, and it is only meaningful while the
        retest's in-sample range is the window the SPP ran on. A retest configured over a
        different history fails every canary for a reason that has nothing to do with the
        factory.
    """
    names = [c for c in table.columns if c not in RESULTS]
    out = [{"values": dict(origin), "stratum": ORIGIN, "origin": True,
            "expect_netprofit": None, "expect_trades": None, "expect_same_as": None}]

    for permutation in _picks(table, settings["n"]):
        row = table.loc[permutation]
        values = dict(origin)
        values.update({n: float(row[n]) for n in names})
        out.append({"values": values, "stratum": "canary", "origin": False,
                    "expect_netprofit": float(row["NetProfit"]),
                    "expect_trades": int(row["NumberOfTrades"]),
                    "expect_same_as": None})

    if settings["inert_pairs"]:
        for item in design["frozen"]:
            name = item["name"]
            far = max(levels[name], key=lambda v: abs(v - float(item["value"])))
            values = dict(origin)
            values[name] = far
            out.append({"values": values, "stratum": "canary", "origin": False,
                        "expect_netprofit": None, "expect_trades": None,
                        "expect_same_as": ORIGIN})
    return out
