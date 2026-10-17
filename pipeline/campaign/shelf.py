"""The survivors' shelf: every finalist of a finished workflow filed by asset, timeframe, direction, family and template."""

import csv
import shutil
from datetime import datetime
from pathlib import Path

from core.datapaths import campaign_dir

COLUMNS = (
    "date",
    "symbol",
    "timeframe",
    "direction",
    "family",
    "template",
    "strategy",
    "mother",
    "identity",
    "test",
    "folder",
    "workflow",
)


def place(cell: dict, strategies: list[dict], workflow: Path) -> None:
    """File each finalist in its own folder and add its line to `supervivientes/indice.csv`.

    Args:
        cell: The ledger row; a cell marked `test` is filed under `_pruebas/`, apart from the real ones.
        strategies: The finalists as `freeze` returns them.
        workflow: The workflow's folder under `runs/`.

    A strategy's folder holds `estrategia.sqx` (a copy SQX can load), and links: `archivo` and
    `madre` to the frozen versions with every result, `workflow` to the run it came from.
    """
    root = campaign_dir() / "supervivientes"
    day = datetime.now().strftime("%Y%m%d")
    base = (root / "_pruebas" if cell.get("test") else root).joinpath(
        cell["symbol"],
        cell["timeframe"],
        cell["direction"],
        cell["family"],
        cell["template"],
    )
    index = root / "indice.csv"
    root.mkdir(parents=True, exist_ok=True)
    new = not index.exists()
    with index.open("a", newline="", encoding="utf-8") as out:
        rows = csv.DictWriter(out, COLUMNS)
        if new:
            rows.writeheader()
        for s in strategies:
            folder = base / f"{day}_{s['strategy'].replace(' ', '_')}"
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy(s["sqx"], folder / "estrategia.sqx")
            for name, target in (
                ("archivo", s["archive"]),
                ("madre", s["mother_archive"]),
                ("workflow", workflow),
            ):
                if target:
                    (folder / name).symlink_to(target)
            rows.writerow(
                {
                    **{k: cell[k] for k in COLUMNS[1:6]},
                    "date": day,
                    "strategy": s["strategy"],
                    "mother": s["mother"],
                    "identity": s["identity"],
                    "test": bool(cell.get("test")),
                    "folder": folder,
                    "workflow": workflow,
                }
            )
