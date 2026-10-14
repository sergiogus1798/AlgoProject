"""One finished workflow kept for good: its run folder, its timings and counts, and every finalist frozen in the archive."""

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from core.datapaths import campaign_dir
from core.paths import ROOT
from pipeline.campaign import shelf
from pipeline.campaign.freeze import freeze

CRITERIA = ROOT / "pipeline" / "autopilot" / "criteria.yaml"
COUNT = re.compile(r"([^:·;|]+): (\d+) → (\d+)")


def steps(resumen: Path) -> list[dict]:
    """The autopilot's `resumen.md` as rows: step, kind, seconds, what it did, and its `A → B` counts."""
    out = []
    for line in resumen.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 4 and cells[2].replace(".", "").isdigit():
            out.append(
                {
                    "step": cells[0],
                    "kind": cells[1],
                    "seconds": float(cells[2]),
                    "what": cells[3],
                    "counts": [
                        {"what": w.strip(), "in": int(a), "out": int(b)}
                        for w, a, b in COUNT.findall(cells[3])
                    ],
                }
            )
    return out


class Kept(TypedDict):
    """What the ledger records of a kept run: its folder and the numbers of its steps."""

    folder: str
    steps_minutes: float
    counts: list[str]
    finalists: int
    criteria: str


def keep(cell: dict, run: Path | None, state: str) -> Kept:
    """Write the workflow's own folder and return what the ledger records of it.

    Args:
        cell: The ledger row, with `project`.
        run: The autopilot's run folder, None when the run never began.
        state: done, failed or interrupted — the finalists are frozen only when done.

    Returns:
        `folder`, `steps_minutes`, `counts` (every `A → B` of the run in order), `finalists`, `criteria`; `workflow.json` also lists `not_kept`.
    """
    name = "_".join(
        [
            cell["template"],
            cell["symbol"],
            cell["timeframe"],
            cell["direction"],
            datetime.now().strftime("%Y%m%d-%H%M%S"),
        ]
    )
    folder = campaign_dir() / "runs" / name
    while folder.exists():  # an interrupted cell resumed within the same second
        folder = folder.with_name(folder.name + "b")
    folder.mkdir(parents=True, exist_ok=True)
    rows, finalists, skipped = [], [], []
    if run:
        shutil.copytree(run, folder / "run")
        rows = steps(run / "resumen.md") if (run / "resumen.md").exists() else []
        if state == "done" and (run / "finalistas.json").exists():
            finalists, skipped = freeze(
                cell,
                json.loads((run / "finalistas.json").read_text(encoding="utf-8")),
                folder,
                run,
            )
            shelf.place(cell, finalists, folder)
    facts: Kept = {
        "folder": str(folder),
        "steps_minutes": round(
            sum(r["seconds"] for r in rows) / 60, 1
        ),  # not `minutes`: the ledger merges rows, and that is the Build cap
        "counts": [
            f"{c['what']} {c['in']}→{c['out']}" for r in rows for c in r["counts"]
        ],
        "finalists": len(finalists),
        "criteria": hashlib.sha256(CRITERIA.read_bytes()).hexdigest()[:12],
    }
    (folder / "workflow.json").write_text(
        json.dumps(
            {
                **cell,
                **facts,
                "state": state,
                "run": str(run) if run else None,
                "steps": rows,
                "strategies": finalists,
                "not_kept": skipped,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return facts
