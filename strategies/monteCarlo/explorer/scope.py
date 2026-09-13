"""Turns SETUP plus the config drawer's overrides into the cfg/asset one request runs with."""

import json
from collections.abc import Mapping

from strategies.monteCarlo import config


def scoped(setup: dict, payload: dict) -> dict:
    """One request's setup, with the config drawer's overrides applied.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        payload: The request JSON. Its optional "cfg" is {"section.key": value, ...} in the
            --set dotted form; its optional "asset" is {"spread": value, ...}.

    Returns:
        A copy of setup with cfg and asset replaced — never mutated in place, so a run made
        with the drawer open does not change what any other strategy or job sees.
    """
    overrides = [f"{k}={v}" for k, v in payload.get("cfg", {}).items()]
    cfg = config.load(setup["base_set"] + overrides)
    asset = {**setup["asset"], **{k: float(v) for k, v in payload.get("asset", {}).items()}}
    return {**setup, "cfg": cfg, "asset": asset}


def from_query(setup: dict, args: Mapping[str, str]) -> dict:
    """One GET request's setup, from the drawer state the page attaches to every view.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        args: flask.request.args — a Mapping, so any dict works in a test too.

    Returns:
        What scoped() returns. A GET carries no body, but the freshness check a view does
        still has to compare the stored result against whatever the drawer has active right
        now — not against config.yaml on disk — or a result saved under an override reads
        as permanently stale no matter how many times it is redone with that same override.
    """
    return scoped(setup, {"cfg": json.loads(args.get("cfg", "{}")),
                         "asset": json.loads(args.get("asset", "{}"))})
