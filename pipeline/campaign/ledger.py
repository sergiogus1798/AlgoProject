"""The campaign's ledger: every cell ever queued, one JSON line per change of state, never rewritten."""

from datetime import datetime
from typing import Any

from core.datapaths import campaign_dir
from ledger import shards

KEY = ("template", "symbol", "timeframe", "direction")
OPEN = (
    "running",
    "interrupted",
)  # a cell the loop takes up again before any pending one


def key(cell: dict) -> str:
    """The identity of a cell: what is never run twice."""
    return "|".join(cell[k] for k in KEY)


def cells() -> dict[str, dict]:
    """Every cell at its latest state, keyed by `key`, in the order they were queued."""
    out: dict[str, dict] = {}
    for row in shards.read_all(campaign_dir() / "ledger.jsonl"):
        out[key(row)] = {**out.get(key(row), {}), **row}
    return out


def mark(cell: dict, state: str, **facts: object) -> dict[str, Any]:
    """Append one line: the cell at a new state, with what is known of it now.

    Args:
        cell: A row carrying the four `KEY` fields.
        state: pending, running, done, failed or interrupted.
        facts: Anything else to record with the change.

    Returns:
        The line written.
    """
    row = {
        **{k: cell[k] for k in KEY},
        **facts,
        "state": state,
        "at": datetime.now().isoformat(timespec="seconds"),
    }
    file = shards.shard_path(
        campaign_dir() / "ledger.jsonl"
    )  # one writer per file (D27)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as out:
        out.write(shards.stamp(row) + "\n")
    return row


def following() -> dict | None:
    """The cell the loop runs next: one left open by a stop or a crash, else the oldest pending."""
    rows = list(cells().values())
    for wanted in (OPEN, ("pending",)):
        for row in rows:
            if row["state"] in wanted:
                return row
    return None
