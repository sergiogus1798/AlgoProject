"""The stored reports of one databank: which days hold a study, one result read, and slim cached rows."""

import csv
import json
from collections.abc import Callable
from pathlib import Path

from core.paths import report_dir

# A study's own verdict words (verdict.csv, for /curate) on the contract's five-state scale,
# for a report that wrote no per-strategy JSON. Each row copies the study's own STATE map.
WORDS = {
    "pass": "pass", "fail": "fail", "watch": "watch", "info": "info", "none": "none",
    "MANTENER": "pass", "DESCARTAR": "fail", "DUDOSA": "watch",               # curate, decay
    "STRONG": "pass", "ACCEPTABLE": "pass", "MARGINAL": "watch",              # mcRetest
    "FAIL": "fail", "INCONCLUSIVE": "none",
    "worth_it": "pass", "not_worth_it": "fail",                               # exposure
    "predicts": "pass", "blind": "watch", "perverse": "fail",                 # wfm
    "survives": "pass", "inherited": "watch", "fails": "fail",                # crossTF
    "control_failed": "watch", "silent": "none", "unusable": "none",
}

# (path, mtime) -> what was read. A report is written once and never edited, so a file's
# mtime is its version; the matrix of a 5,000-strategy databank parses each JSON once.
_CACHE: dict[tuple[str, float], object] = {}


def bank(project: str, databank: str) -> Path:
    """The folder holding every day of one databank's reports.

    Args:
        project: SQX project name.
        databank: Databank name, with spaces as SQX spells it or underscores as the folder does.

    Returns:
        reports/<project>/<databank>/, spelled by `core.paths.report_dir`.
    """
    return report_dir(project, databank, "day").parent


def days(project: str, databank: str, study: str) -> list[str]:
    """The days one study wrote a report for one databank.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key, which is also its report folder's name.

    Returns:
        YYYY-MM-DD strings, newest first.
    """
    return sorted((d.parent.name for d in bank(project, databank).glob(f"*/{study}")
                   if d.is_dir()), reverse=True)


def load(path: Path) -> tuple[dict | None, str | None]:
    """One stored result, if it is a contract result.

    Args:
        path: A `<study>.json` or `estrategias/<name>.json`.

    Returns:
        (result, None), or (None, the reason in Spanish) for a missing file, a file that is
        not JSON or JSON that predates the contract — older reports are data here, not errors.
    """
    if not path.is_file():
        return None, "no hay resultado guardado"
    try:
        got = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return None, f"no es JSON legible: {e}"
    if not isinstance(got, dict) or "tabs" not in got or "config_hash" not in got:
        return None, "informe anterior al contrato de estudios (sin tabs ni config_hash)"
    return got, None


def _cached(path: Path, read: Callable[[Path], object]) -> object:
    """What `read(path)` gave the last time this version of the file was read.

    Args:
        path: The file.
        read: A function of the path.

    Returns:
        Its result, computed once per (path, mtime).
    """
    key = (str(path), path.stat().st_mtime)
    if key not in _CACHE:
        _CACHE[key] = read(path)
    return _CACHE[key]


def _slim(path: Path) -> dict | None:
    """The handful of fields a matrix cell or a history row needs from one result file.

    Args:
        path: A result JSON.

    Returns:
        strategy, identity, config_hash, computed_at, state, label — or None when the
        file is not a contract result.
    """
    got, _ = load(path)
    if got is None:
        return None
    said = got.get("verdict") or {}
    return {"strategy": got.get("strategy"), "identity": got.get("identity"),
            "config_hash": got["config_hash"], "computed_at": got.get("computed_at"),
            "state": said.get("state", "info"), "label": said.get("label", "descriptivo")}


def slim(path: Path) -> dict | None:
    """`_slim`, cached by the file's version.

    Args:
        path: A result JSON that exists.

    Returns:
        As `_slim`.
    """
    return _cached(path, _slim)


def _verdicts(path: Path) -> dict[str, dict] | None:
    """A verdict.csv as name -> identity and verdict word.

    Args:
        path: The CSV.

    Returns:
        name -> {identity, word}; None when the table lacks a `strategy` or `verdict`
        column (the Monte Carlo's older tables carry a tier instead).
    """
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or not {"strategy", "verdict"} <= rows[0].keys():
        return None
    return {r["strategy"]: {"identity": r.get("identity") or None, "word": r["verdict"]}
            for r in rows}


def verdicts(folder: Path) -> dict[str, dict] | None:
    """The study folder's verdict.csv, cached by the file's version.

    Args:
        folder: reports/<P>/<D>/<day>/<study>/.

    Returns:
        As `_verdicts`, or None when the folder wrote no verdict.csv.
    """
    path = folder / "verdict.csv"
    return _cached(path, _verdicts) if path.is_file() else None
