"""What the T0-T4 reading is run on: the siblings made, the oos1 trades the study already loaded, and the build trades when phase 2 ran."""

import json
from pathlib import Path
from typing import cast

import pandas as pd

from core import assetdata, paths
from sqx.projects.workflow import CROSSTF_BUILD
from studies.transfer.crossmarket.travel import cells, validity

KEEP = ["strategy", "Open time", "Close time", "Type"]
MAIN_DATABANK = "Results"      # where the gate's harvest keeps each mother's own build trades


def made(plan: pd.DataFrame) -> pd.DataFrame:
    """One row per fabricated sibling, from the study's plan of cells.

    Args:
        plan: What `crossTF.inputs.plan` returned.

    Returns:
        `mother`, `sibling`, `timeframe`, `ratio`, `rounding_shift`, `clamped`, `unverified`.
    """
    rows = cast(pd.DataFrame, plan[plan["role"] == "scaled"]).rename(columns={"strategy": "sibling"})
    return cast(pd.DataFrame, rows[["mother", "sibling", "timeframe", "ratio", "rounding_shift", "clamped",
                 "unverified"]]).reset_index(drop=True)


def oos1(plan: pd.DataFrame, packed: pd.DataFrame) -> pd.DataFrame:
    """The oos1 trades of every mother on her own timeframe and of every sibling on hers.

    Args:
        plan: What `crossTF.inputs.plan` returned.
        packed: What `crossTF.inputs.oos` returned: every databank's trades, `block` set.

    Returns:
        KEEP; the control and unscaled cells of the old reading are left out.
    """
    cell = plan.loc[plan["role"].isin(["baseline", "scaled"]), ["strategy", "block"]]
    return cast(pd.DataFrame, packed.astype({"strategy": str}).merge(cell, on=["strategy", "block"])[KEEP])


def cards(feed: str) -> tuple[dict | None, dict | None, str]:
    """The asset's costs at each window and its cuts, or why it cannot be priced.

    Args:
        feed: SQX symbol the cells ran on.

    Returns:
        ({"build": costs, "oos1": costs}, cuts, "") or (None, None, reason) — no asset file
        declares the feed, or its card still has a field the owner has not decided (forex).
    """
    got = {segment: validity.card(feed, segment) for segment in ("build", "oos1")}
    bad = next((reason for _, reason in got.values() if reason), "")
    if bad:
        return None, None, bad
    return {k: v[0] for k, v in got.items()}, cells.cuts(assetdata.symbol_of(feed)), ""


def _day(days: Path, day: str) -> Path | None:
    """A databank's folder of that day, else its newest, else None."""
    if (days / day).is_dir():
        return days / day
    return max(days.iterdir(), default=None) if days.is_dir() else None


def build_banks(directory: Path) -> dict[str, str]:
    """THE SEAM of phase 2 (encargo 47, part S): which databank holds each sibling timeframe's
    BUILD-window retest.

    Args:
        directory: The batch's folder (`core.datapaths.crosstf_dir`).

    Returns:
        {timeframe: databank}: `build_databanks` of the batch's `blocks.json` when it names
        them, else the databank `CROSSTF_BUILD` gives each sibling timeframe `blocks.json`
        lists (the fabrication wrote it before step 11.7 existed in the project, so it cannot
        know them); {} without a `blocks.json`. A name whose export is not on
        disk is skipped by `build`, so a project without phase 2 reads «no build data».
    """
    found = directory / "blocks.json"
    if not found.exists():
        return {}
    blocks = json.loads(found.read_text(encoding="utf-8"))
    return blocks.get("build_databanks") or {
        tf: CROSSTF_BUILD["databank"].format(tf=tf) for tf in blocks.get("blocks", [])[1:]}


def build(export: Path, directory: Path, identity: dict, made: pd.DataFrame) -> pd.DataFrame | None:
    """The build-window trades of the siblings and of their mothers, or None when phase 2 did not run.

    Args:
        export: The `CrossTF` `trades.parquet` of this run, raw/<project>/<databank>/<day>/.
        directory: The batch's folder.
        identity: Mother name to identity, as the study resolved it.
        made: What `made` returned: which sibling belongs to which timeframe.

    Returns:
        KEEP. Siblings: each phase-2 databank's `trades.parquet` beside `export` (same day,
        else its newest), only the siblings fabricated for that databank's timeframe — every
        strategy is retested in every one of them, and pooled they gave a sibling 3-7 times
        her trades and z_build of ±10-19 (2026-10-09). Mothers: never rerun — the gate's harvest of `Results`
        (`core.paths.harvest_dir`, newest day), matched by `identity`. A mother missing there
        simply has no rows, which the table reads as «no build data».
    """
    banks = build_banks(directory)
    frames = []
    for tf, bank in banks.items():
        day = _day(export.parents[2] / bank.replace(" ", "_"), export.parent.name)
        if day:
            got = pd.read_parquet(day / "trades.parquet").astype({"strategy": str})[KEEP]
            frames.append(got[cast(pd.Series, got["strategy"]).isin(made.loc[made["timeframe"] == tf, "sibling"])])
    if not frames:
        return None
    harvest = _day(paths.harvest_dir(export.parents[2].name, MAIN_DATABANK, "x").parent, export.parent.name)
    if harvest and (harvest / "trades.parquet").is_file():
        name = {i: m for m, i in identity.items() if i}
        main = pd.read_parquet(harvest / "trades.parquet", columns=["identity", *KEEP[1:]])
        frames.append(main.assign(strategy=main["identity"].map(name)).dropna(subset=["strategy"])[KEEP])  # pyright: ignore[reportArgumentType]  # pandas stubs reject a dict mapper
    return pd.concat(frames, ignore_index=True)
