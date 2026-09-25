#!/usr/bin/env python3
"""The three legs of the WFC/CSCV retest: what each one is called and where its output lands."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.assetdata import doctrine, load
from core.paths import worker_dir
from sqx.projects.setups import bounds

MAIN = "Main"
EXTRA = "AdditionalMarket: "
# "AdditionalMarket: XAGUSD_DukasM1_Infinox/M30:  XAGUSD_DukasM1_Infinox/M30" -> the feed.
FEED = re.compile(rf"^{re.escape(EXTRA)}([^/:]+)")


def legs(symbol: str | None = None) -> list[dict]:
    """The doctrine's three retest legs, in segment order.

    Args:
        symbol: When given, each leg also carries the dates that segment spans for this
            asset — which is the only per-asset part of the study.

    Returns:
        One dict per leg: `segment`, `title`, `databank`, and with a symbol also `from`
        and `to`. The order is the order of `wfc.tasks` in `assets/_build.yaml`, which is
        chronological, and every consumer relies on that: the united curve is these three
        concatenated.
    """
    study = doctrine()["wfc"]
    data = load(symbol) if symbol else None
    out = []
    for spec in study["tasks"]:
        leg = dict(spec)
        if data:
            leg["from"], leg["to"] = bounds(data, spec["segment"])
        out.append(leg)
    return out


def source() -> str:
    """The databank all three legs read — the fabricated batch, loaded once."""
    return doctrine()["wfc"]["input"]


def bank_dir(role: str, project: str, databank: str) -> Path:
    """Where an install keeps one databank's `.sqx` after `synctofiles`.

    Args:
        role: Worker role that owns the install.
        project: Project name on that install.
        databank: Databank name, exactly as the project declares it.

    Returns:
        The folder. It is read directly rather than through SQX: every per-day curve and
        every stored metric lives inside those files, and reading them needs no instance
        running (`core.sqxstats`).
    """
    return worker_dir(role) / "user/projects" / project / "databanks" / databank


def market(result_key: str) -> str:
    """The market a result key belongs to, as the harvest names it.

    Args:
        result_key: A `<Result resultKey>` as `core.sqxstats.results` returns it.

    Returns:
        "Main" for the asset the strategy was built on, the feed name for a cross-check
        market, and the key itself for anything else — "Portfolio", which is every market
        summed and is deliberately NOT harvested as a market: it would double-count.
    """
    if result_key.startswith(MAIN):
        return MAIN
    found = FEED.match(result_key)
    return found.group(1) if found else result_key
