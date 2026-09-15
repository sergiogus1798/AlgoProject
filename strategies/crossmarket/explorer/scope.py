"""Turns the config drawer's overrides into the cfg one request runs with."""

import json
from collections.abc import Mapping

from strategies.crossmarket import config


def scoped(setup: dict, payload: dict) -> dict:
    """One request's configuration, with the drawer's overrides applied.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        payload: The request JSON. Its optional "cfg" is {"section.key": value, ...} in the
            same dotted form --set takes.

    Returns:
        A fresh config — never the shared one mutated in place, so a run made with the drawer
        open does not change what any other strategy or job sees.
    """
    return config.load(setup["base_set"]
                       + [f"{k}={json.dumps(v)}" for k, v in payload.get("cfg", {}).items()])


def from_query(setup: dict, args: Mapping[str, str]) -> dict:
    """One GET request's configuration, from the drawer state the page attaches to every view.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        args: flask.request.args — a Mapping, so any dict works in a test too.

    Returns:
        What scoped() returns. A GET carries no body, but the freshness check a view does
        still has to compare the stored result against whatever the drawer has active right
        now — not against config.yaml on disk — or a result saved under an override reads as
        permanently stale no matter how many times it is recomputed with that same override.
    """
    return scoped(setup, {"cfg": json.loads(args.get("cfg", "{}"))})
