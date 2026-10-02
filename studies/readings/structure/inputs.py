"""What the study is run on: its knobs, the structural batch's plan, and every file's trades per leg."""

import json
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


def latest(project: str, databank: str, required: set[str] | None = None) -> Path:
    """The newest trade export of one databank that actually carries this batch's variants.

    Args:
        project: Project the retest ran in.
        databank: One leg's output databank.
        required: Every `variant_id` the batch's plan fabricated, when known — the newest
            export is skipped if a later, unrelated retest into the same databank
            overwrote it with a different set of variants (found 2026-09-30: a WFC
            re-run two days after a structural batch's own retest left `KeyError` on
            every mother, because "newest" no longer meant "this batch's own export").
            `None` keeps the old newest-wins behaviour for a caller with no plan yet.

    Returns:
        Its `trades.parquet`. Prefers an export tagged `--batch structure`
        (`sqx.export.export_retest`) over the untagged layout an older export used, so a
        same-day stop-grid export (step 24, tag `stopgrid`) into the same databank cannot
        shadow this one; within each, newest first, but skipped in favour of an older
        export when `required` names variants the newest one does not carry.
    """
    root = export_dir(project, databank, "x").parent
    tagged = sorted(root.glob("*/structure/trades.parquet"), reverse=True)
    untagged = sorted(root.glob("*/trades.parquet"), reverse=True)
    candidates = tagged + untagged
    if not candidates:
        raise SystemExit(f"ningún export de trades para {project}/{databank}")
    if not required:
        return candidates[0]
    for path in candidates:
        names = set(pd.read_parquet(path, columns=["strategy"])["strategy"].unique())
        if required <= names:
            return path
    raise SystemExit(
        f"ningún export de {project}/{databank} lleva las {len(required)} variantes de "
        f"este lote — el más nuevo es de otro retest de esa databank, no de este batch")


def segments(work: Path) -> dict[str, str]:
    """Which segment each leg's databank was filed under, for THIS run.

    Args:
        work: The batch directory: holds `ran.json` when `sqx.variants.execute` wrote one.

    Returns:
        databank -> segment, read from `ran.json`'s legs when the file is there — the run's
        own record, immune to a later edit of `wfc.tasks[].segment` (OPEN.md #80). A run
        made before `ran.json` existed falls back to today's `assets/_build.yaml`, with a
        warning printed, because it is the one case where that config is all there is.
    """
    found = work / "ran.json"
    if found.exists():
        legs = json.loads(found.read_text(encoding="utf-8"))["legs"]
        return {leg["databank"]: leg["segment"] for leg in legs}
    print("⚠️  sin ran.json en el batch: releyendo assets/_build.yaml de HOY para un run que no "
          "lo escribió (OPEN.md #80) — si wfc.tasks[].segment cambió desde entonces, esto filia "
          "mal el tramo de cada pata.")
    return {t["databank"]: t["segment"] for t in assetdata.doctrine()["wfc"]["tasks"]}


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
    plan = pd.read_parquet(work / PLAN)
    required = set(plan["variant_id"])
    segment = segments(work)
    for bank in databanks:
        gate.allow(STEP, segment[bank], symbol)
    packed = [latest(project, bank, required) for bank in databanks]
    legs = {}
    for bank, path in zip(databanks, packed):
        frame = tradestore.read(path)
        legs[segment[bank]] = {name: tradestore.market(frame, name, feed)
                               for name in frame["strategy"].unique()}
    return {"plan": plan, "retained": pd.read_parquet(work / RETAINED),
            "legs": legs, "packed": packed,
            "point_value": assetdata.load(symbol)["instrument"]["point_value"]}
