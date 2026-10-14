"""The campaign's ledger: every cell ever queued, one JSON line per change of state, never rewritten."""

import json
from datetime import datetime
from typing import Any

from core.datapaths import campaign_dir

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
    file = campaign_dir() / "ledger.jsonl"
    out: dict[str, dict] = {}
    for line in file.read_text(encoding="utf-8").splitlines() if file.exists() else []:
        row = json.loads(line)
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
    file = campaign_dir() / "ledger.jsonl"
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def following() -> dict | None:
    """The cell the loop runs next: one left open by a stop or a crash, else the oldest pending."""
    rows = list(cells().values())
    for wanted in (OPEN, ("pending",)):
        for row in rows:
            if row["state"] in wanted:
                return row
    return None
