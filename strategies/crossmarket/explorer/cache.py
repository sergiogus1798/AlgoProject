"""Results kept on disk so switching strategy is instant and re-running is a decision."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np

from core.paths import DATA

ROOT = DATA / "derived" / "crossmarket"


def fingerprint(cfg: dict) -> str:
    """A short hash of the run configuration a result was computed under.

    Args:
        cfg: The panel's configuration drawer values — draws, models, alpha, min_trades,
            min_on_open, min_markets, correlated, bootstrap_block, bootstrap_draws,
            cost_multiples, bar_shift, slippage_fractions.

    Returns:
        Twelve hex characters. Changing any of these makes a stored result declare itself
        out of date instead of quietly answering a different question.
    """
    text = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def plain(value: object) -> object:
    """The same structure with numpy types turned into things JSON can hold.

    Args:
        value: Any part of a result.

    Returns:
        Lists, dicts, floats, ints, strings and None. Infinity round-trips through Python's
        json module as the bare token `Infinity`: a trade with MFE = 0 makes its capture
        ratio genuinely undefined, and turning that into null would make every comparison
        against it quietly true.
    """
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return [plain(v) for v in value.tolist()]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (str, type(None))):
        return value
    return str(value)


def where(project: str, databank: str, strategy: str) -> Path:
    """Where one strategy's stored analysis lives.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.

    Returns:
        Path under the data root. Nothing computed is ever written into the repo.
    """
    return ROOT / project / databank.replace(" ", "_") / f"{strategy}.json"


def save(project: str, databank: str, strategy: str, body: dict, cfg: dict) -> Path:
    """Store one strategy's whole cross-market analysis.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.
        body: Everything the panel needs to redraw every tab.
        cfg: The run configuration it was computed under.

    Returns:
        Path written.
    """
    path = where(project, databank, strategy)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"saved": datetime.now().isoformat(timespec="seconds"),
                                "fingerprint": fingerprint(cfg), "body": plain(body)},
                               indent=1), encoding="utf-8")
    return path


def load(project: str, databank: str, strategy: str, cfg: dict) -> dict | None:
    """Read one strategy's stored analysis, if there is one.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.
        cfg: The run configuration in force now.

    Returns:
        The record with a `stale` flag saying whether it was computed under a different
        configuration, or None when nothing is stored. A stale result is shown and
        labelled, never silently used as if it were current.
    """
    path = where(project, databank, strategy)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    record["stale"] = record.get("fingerprint") != fingerprint(cfg)
    return record


def clear(project: str, databank: str) -> None:
    """Wipe every stored result for one databank.

    Args:
        project: Project name.
        databank: Databank name.

    Returns:
        Nothing. Called once, at panel start-up, so the panel opens with nothing analysed
        rather than showing a previous session's strategies as if they were current.
    """
    folder = ROOT / project / databank.replace(" ", "_")
    if folder.exists():
        shutil.rmtree(folder)


def stored(project: str, databank: str) -> dict[str, str]:
    """Which strategies already have a result, and when it was computed.

    Args:
        project: Project name.
        databank: Databank name.

    Returns:
        {strategy: timestamp}. Used to mark the dropdown, so the cost of a click is visible
        before it is paid.
    """
    folder = ROOT / project / databank.replace(" ", "_")
    if not folder.exists():
        return {}
    return {f.stem: json.loads(f.read_text(encoding="utf-8"))["saved"]
            for f in sorted(folder.glob("*.json"))}
