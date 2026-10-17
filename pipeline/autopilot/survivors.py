"""Who walks the tail: the strategies left in the databank the last judged step cut."""

from typing import TypedDict

import pandas as pd

from core import assetdata
from core.paths import databank_dir
from ledger import study as studymod
from sqx.curate import apply_verdict
from sqx.projects import registry
from sqx.worker.preflight import by_identity
from ui.daemon.runner import where

# The steps whose `cut` in criteria.yaml names where the survivors live from then on: 16
# today («SPP OOS»), and 20 and 21 the day the owner gives one of them rules and a `cut`.
CUTS = ("16", "20", "21")


class Done(Exception):
    """A clean stop decided while running: nothing failed, there is nothing left to walk."""


def bank(cfg: dict, n: str) -> str:
    """The databank step `n` takes its mothers from: the `cut` of the last step before it
    that declares one.

    Args:
        cfg: `judge.settings()`.
        n: A WORKFLOW step number, e.g. "17".
    """
    return [
        cfg["steps"][s]["cut"]
        for s in CUTS
        if float(s) < float(n) and "cut" in cfg["steps"].get(s, {})
    ][-1]


def mothers(project: str, role: str, cfg: dict, n: str) -> pd.DataFrame:
    """Every survivor that reaches step `n` — all of them, never filtered by 17-19 (owner,
    2026-09-29).

    Args:
        project: Project name.
        role: The worker holding the project.
        cfg: `judge.settings()`.
        n: The step about to run.

    Returns:
        `strategy` (the file's name), `identity` and `file`, one row per identity: SQX can
        hold one strategy under two names, and it is one mother.

    Raises:
        Done: Nobody is left in that databank.
    """
    source = bank(cfg, n)
    files = by_identity(databank_dir(project, source, apply_verdict.install_of(role)))
    if not files:
        raise Done(
            f"«{source}» no tiene ninguna superviviente: no queda nada que pasear"
        )
    return pd.DataFrame(
        [
            {"strategy": fs[0].stem, "identity": i, "file": fs[0]}
            for i, fs in files.items()
        ]
    )


class About(TypedDict):
    """What a project is: asset, timeframe, feed and template family."""

    symbol: str
    timeframe: str
    feed: str
    family: str | None


def about(project: str) -> About:
    """What the project is, as every command of the tail needs it.

    Returns:
        `symbol` and `timeframe` (the project registry's newest row), `feed` (the asset's
        SQX symbol) and `family` (the template the ledger rows are signed under, or None).
    """
    row = next(r for r in reversed(registry.rows()) if r["name"] == project)
    return {
        "symbol": row["symbol"],
        "timeframe": row["timeframe"],
        "feed": assetdata.load(row["symbol"])["sqx_symbol"],
        "family": where.family(project),
    }


def study_of(project: str) -> tuple[str, About]:
    """The ledger study id of a project, and what the project is.

    Raises:
        ValueError: The registry names no template for the project, so no family signs its rows.
    """
    who = about(project)
    if who["family"] is None:
        raise ValueError(where.no_family(project))
    return studymod.study_id(who["symbol"], who["timeframe"], who["family"]), who
