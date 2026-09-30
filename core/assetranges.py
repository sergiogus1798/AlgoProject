"""The MC Retest spread and slippage ranges of one asset, in the points SQX takes."""

from core.assetdata import policy, sqx_settings


def mc_retest(data: dict, segment: str = "build") -> dict:
    """The spread and slippage ranges the MC Retest task must randomise within.

    Args:
        data: One asset as load() returned it.
        segment: Which segment's costs the default multiples are read against — the one the
            MC Retest tasks run on.

    Returns:
        {"spread": {"min", "max", "source"}, ...} in points. A bound the asset declares is
        used as written; a null one falls back to `mc_retest.default_multiples` of
        `_policy.yaml` times the cost the backtest itself runs at, and `source` says which
        of the two it was.

    Absolute points is the only unit SQX accepts, so a multiple is resolved here rather than
    stored: a range is only meaningful at the instrument's own scale, and SQX's factory
    1.0-5.0 is between 1 and 5 points on an instrument whose spread is 1100.
    """
    multiples = policy()["mc_retest"]["default_multiples"]
    costs = {"spread": sqx_settings(data, segment)["defaultSpread"],
             "slippage": sqx_settings(data, segment)["defaultSlippage"]}
    out = {}
    for name, span in data["mc_retest"].items():
        if span["min"] is not None and span["max"] is not None:
            out[name] = {**{k: span[k] for k in ("min", "max")}, "source": "declarado"}
            continue
        factor, cost = multiples.get(name), costs.get(name)
        if factor is None or cost is None:
            out[name] = {"min": span["min"], "max": span["max"], "source": "sin decidir"}
            continue
        out[name] = {"min": round(factor["min"] * cost, 6), "max": round(factor["max"] * cost, 6),
                     "source": f"{factor['min']}x-{factor['max']}x el {name} de `{segment}`"}
    return out
