"""What the study is run on: its knobs, the structural batch's plan, and every file's trades per leg."""

from pathlib import Path

import pandas as pd

from core import assetdata, tradestore
from core.paths import export_dir
from core.study import config as study_config
from ledger import gate

CONFIG = Path(__file__).with_name("config.yaml")
STEP = 23           # the workflow step this reading is (owner, 2026-09-26)
PLAN = "structure.parquet"          # sqx.structural.make
RETAINED = "retained.parquet"       # sqx.structural.keep


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds.
    """
    return study_config.load(CONFIG, overrides)


def latest(project: str, databank: str) -> Path:
    """The newest trade export of one databank.

    Args:
        project: Project the retest ran in.
        databank: One leg's output databank.

    Returns:
        Its `trades.parquet`.
    """
    days = sorted(export_dir(project, databank, "x").parent.iterdir())
    return days[-1] / "trades.parquet"


def load(work: Path, project: str, databanks: list[str], feed: str, symbol: str) -> dict:
    """Everything one run of the reading needs, each leg cleared by the ledger first.

    Args:
        work: The batch directory: `structure.parquet`, `retained.parquet`, `sqx/`.
        project: The custom project the batch was retested in.
        databanks: The legs to read, by their output databank (`WFC_Build`…).
        feed: The main market's SQX feed; the cross-check markets are left out.
        symbol: The asset, for its point value and for the ledger's segment check.

    Returns:
        `plan` (the fabricated batch and what each file holds), `retained` (whether each
        retested file kept its edit), `legs` {segment: {variant_id: trades}}, `packed`
        (the exports read), `point_value`.

        ⚠️ `ledger.gate.allow` runs for every leg before its file is opened: `oos2` is
        reserved for the WFC and the WFM, and this is step 23. A refused leg is a
        PermissionError, never a silent skip.
    """
    segment = {t["databank"]: t["segment"] for t in assetdata.doctrine()["wfc"]["tasks"]}
    for bank in databanks:
        gate.allow(STEP, segment[bank], symbol)
    packed = [latest(project, bank) for bank in databanks]
    legs = {}
    for bank, path in zip(databanks, packed):
        frame = tradestore.read(path)
        legs[segment[bank]] = {name: tradestore.market(frame, name, feed)
                               for name in frame["strategy"].unique()}
    return {"plan": pd.read_parquet(work / PLAN), "retained": pd.read_parquet(work / RETAINED),
            "legs": legs, "packed": packed,
            "point_value": assetdata.load(symbol)["instrument"]["point_value"]}
