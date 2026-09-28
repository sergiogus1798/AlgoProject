"""What reading a variant batch spends: its study, the door on each segment, and the ledger rows."""

from pathlib import Path

import pyarrow.parquet as pq

from core import assetdata
from engines.variants import panel
from ledger import gate, record, study

MAIN = "Main"


def market(work: Path) -> tuple[str, str]:
    """The asset and the timeframe the batch was retested on as its main market.

    Args:
        work: The batch directory, holding `segments.parquet` from `sqx.variants.collect`.

    Returns:
        ("USDJPY", "M30"), read off the result key SQX stored ("Main: USDJPY_DukasM1_the5ers/
        M30") and never from `_markets.yaml`, whose timeframe is the asset's default and not
        this run's. The batch records no study of its own, so this is where the ledger's
        symbol and timeframe come from.
    """
    key = pq.read_table(work / "segments.parquet", columns=["result_key"],
                        filters=[("market", "=", MAIN), ("segment", "=", "build")])
    feed, timeframe = key.column(0)[0].as_py().split(": ", 1)[1].split("/")
    return assetdata.symbol_for(feed), timeframe


def admit(step: float, segments: tuple, symbol: str) -> None:
    """Ask the ledger's door for every segment before anything is opened.

    Args:
        step: The workflow step — 17 the WFC, 18 the CSCV.
        segments: The segments the look reads.
        symbol: The asset.

    Raises:
        PermissionError: From `ledger.gate.allow`, left to stop the run: a refused look must
            not have happened, so the refusal comes before the parquet is read.
    """
    for segment in segments:
        gate.allow(step, segment, symbol)


def offered(symbol: str) -> list[str]:
    """Every composition of the split the WFC may read on this asset today.

    Args:
        symbol: The asset.

    Returns:
        Their labels (`panel.label`), those whose every segment `ledger.gate.allow` lets
        step 17 read — what a caller offers, so a composition touching a reserved segment
        the policy does not grant is never on the menu.
    """
    found = []
    for comp in panel.COMPOSITIONS:
        try:
            admit(17, comp[0] + comp[1], symbol)
        except PermissionError:
            continue
        found.append(panel.label(comp))
    return found

def log(work: Path, family: str, row: dict, segments: tuple) -> list[dict]:
    """One ledger row per segment read, through the door.

    Args:
        work: The batch directory; its name opens every row's note as `lote <name>`, which
            is how `ledger.blind` knows the look was recorded live.
        family: The template family the batch belongs to — the third part of the study id.
        row: The fields every row shares: step, launched_by, n_in, n_out, criterion, and
            optionally config_hash, thresholds and note.
        segments: The segments read.

    Returns:
        The rows as written. A look removes nobody, so the caller passes n_out = n_in.
    """
    symbol, timeframe = market(work)
    sid = study.study_id(symbol, timeframe, family)
    note = f"lote {work.name}" + (f" · {row['note']}" if row.get("note") else "")
    return [record.log(sid, {**row, "symbol": symbol, "timeframe": timeframe,
                             "segment": s, "note": note}) for s in segments]
