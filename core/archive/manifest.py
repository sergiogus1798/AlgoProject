"""What the archive freezes beside the results: the project's registry row, the asset card, the ledger count."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

from core import assetdata
from core.datapaths import project_registry
from core.paths import ASSETS
from ledger import spend, study, trials


def sha256(path: Path) -> str:
    """The file's SHA-256, hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry(project: str) -> dict:
    """The project's row of `AlgoData/projects/registry.csv`, the newest when it was built twice.

    Args:
        project: SQX project name.

    Returns:
        The row: symbol, timeframe, template, install... Raises when the builder never
        recorded the project, since the asset and the ledger study hang off that row.
    """
    with project_registry().open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["name"] == project]
    if not rows:
        raise KeyError(f"{project} no está en {project_registry()}: sin su fila no se sabe "
                       "el activo ni el timeframe que congelar")
    return rows[-1]


def asset(symbol: str, out: Path) -> dict:
    """Freeze the asset's cost card as it is today.

    Args:
        symbol: Asset as `assets/symbols/` spells it.
        out: `<version>/asset/`.

    Returns:
        The file copied with its sha256, and `card.json`: the card resolved against the
        shared policy (`core.assetdata.load`), which is what a backtest was configured from.
        `assets/` keeps no history, so this is the card on the day of archiving, not
        necessarily the one each backtest ran with.
    """
    out.mkdir()
    source = ASSETS / "symbols" / f"{symbol}.yaml"
    shutil.copy2(source, out / source.name)
    (out / "card.json").write_text(json.dumps(assetdata.load(symbol), indent=1, default=str),
                                   encoding="utf-8")
    return {"symbol": symbol, "file": f"asset/{source.name}", "sha256": sha256(source),
            "card": "asset/card.json"}


def ledger(symbol: str, timeframe: str, family: str) -> dict:
    """The study's search count at archive time: what deflates this strategy's Sharpe later.

    Args:
        symbol: The asset.
        timeframe: The grid the strategies were built on.
        family: The template family, the third part of the study's id.

    Returns:
        `study`, `searches` (ledger rows), `trials` (`trials.accumulated`: n, sigma, mean,
        unit), `segments` (`spend.virgin`: reads per segment) and the ledger file's sha256,
        None when the study has no ledger yet — which then counts nothing.
    """
    sid = study.study_id(symbol, timeframe, family)
    frame = study.read(sid)
    file = study.path(sid)
    return {"study": sid, "searches": len(frame), "trials": trials.accumulated(frame),
            "segments": spend.virgin(frame, symbol),
            "sha256": sha256(file) if file.exists() else None}
