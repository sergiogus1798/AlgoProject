"""Turns SETUP plus the config drawer's overrides into the cfg one request runs with."""

import json
from collections.abc import Mapping

from strategies.retest.inputs import config


def scoped(setup: dict, payload: dict) -> dict:
    """One request's setup, with the drawer's overrides applied.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        payload: The request JSON. Its optional "cfg" is {"section.key": value} in the
            --set dotted form.

    Returns:
        A copy of setup with cfg replaced -- never mutated in place, so a run made with the
        drawer open does not change what any other strategy sees.
    """
    overrides = [f"{k}={v}" for k, v in payload.get("cfg", {}).items()]
    return {**setup, "cfg": config.load(setup["base_set"] + overrides)}


def from_query(setup: dict, args: Mapping[str, str]) -> dict:
    """One GET request's setup, from the drawer state the page attaches to every view.

    Args:
        setup: SETUP, as serve.py's main() assembled it.
        args: flask.request.args -- a Mapping, so any dict works in a test too.

    Returns:
        What scoped() returns.
    """
    return scoped(setup, {"cfg": json.loads(args.get("cfg", "{}"))})
