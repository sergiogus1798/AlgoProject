"""Results kept on disk so switching strategy is instant and re-running is a decision."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np

from core.paths import DATA

ROOT = DATA / "derived" / "montecarlo"


def fingerprint(cfg: dict, asset: dict) -> str:
    """A short hash of the configuration and cost basis a result was computed under.

    Args:
        cfg: What config.load() returned.
        asset: What costs.load() returned, possibly with the panel's per-run overrides.

    Returns:
        Twelve hex characters. Every tunable is inside, so changing one — a threshold, the
        simulation count, the volatility model, or a cost override typed into the panel —
        makes every stored result declare itself out of date instead of quietly answering a
        question nobody asked.
    """
    text = json.dumps({"cfg": cfg, "asset": asset}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def plain(value: object) -> object:
    """The same structure with numpy types turned into things JSON can hold.

    Args:
        value: Any part of a result.

    Returns:
        Lists, dicts, floats, ints, strings and None. NaN is written as NaN and read back
        as NaN: it means "this window had too few trades to resample", and turning it into
        null would make every comparison against it quietly true.
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


def _key(k: str) -> object:
    """One dict key, as a number again if it was one before json.dumps() flattened it.

    Args:
        k: A dict key coming back from json.loads() — always a string.

    Returns:
        int if the whole string is digits, float if it also parses as one (a quantile like
        "0.05"), otherwise the string unchanged.
    """
    if k.lstrip("-").isdigit():
        return int(k)
    try:
        return float(k)
    except ValueError:
        return k


def restore(value: object) -> object:
    """The same structure with the numeric keys JSON had to flatten turned back.

    Args:
        value: Anything json.loads() returned.

    Returns:
        The same, with dict keys that were numbers turned back into int or float. JSON has
        no numeric keys, so a percentile set written as {5: ...} comes back as {"5": ...}
        and a quantile set written as {0.05: ...} comes back as {"0.05": ...} — every
        renderer that asks for either by number would miss it.
    """
    if isinstance(value, dict):
        return {_key(k): restore(v) for k, v in value.items()}
    if isinstance(value, list):
        return [restore(v) for v in value]
    return value


def where(project: str, databank: str, strategy: str) -> Path:
    """Where one strategy's stored result lives.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.

    Returns:
        Path under the data root. Nothing computed is ever written into the repo.
    """
    return ROOT / project / databank.replace(" ", "_") / f"{strategy}.json"


def save(project: str, databank: str, strategy: str, body: dict, cfg: dict,
        asset: dict) -> Path:
    """Store one strategy's whole analysis.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.
        body: What the panel needs to redraw everything: result, verdict and the fan.
        cfg: The configuration it was computed under.
        asset: The cost basis it was computed under — the panel's per-run overrides
            included, since a spread or commission typed into the panel changes every
            Family C number as much as a config threshold would.

    Returns:
        Path written.
    """
    path = where(project, databank, strategy)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"saved": datetime.now().isoformat(timespec="seconds"),
                                "fingerprint": fingerprint(cfg, asset),
                                "n_sims": cfg["global"]["n_sims"],
                                "body": plain(body)}, indent=1), encoding="utf-8")
    return path


def load(project: str, databank: str, strategy: str, cfg: dict, asset: dict) -> dict | None:
    """Read one strategy's stored analysis, if there is one.

    Args:
        project: Project name.
        databank: Databank name.
        strategy: Strategy name.
        cfg: The configuration in force now.
        asset: The cost basis in force now.

    Returns:
        The record with a `stale` flag saying whether it was computed under a different
        configuration or cost basis, or None when nothing is stored. A stale result is
        shown and labelled, never silently used as if it were current.
    """
    path = where(project, databank, strategy)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    record["body"] = restore(record["body"])
    record["stale"] = record.get("fingerprint") != fingerprint(cfg, asset)
    return record


def clear(project: str, databank: str) -> None:
    """Wipe every stored result for one databank.

    Args:
        project: Project name.
        databank: Databank name.

    Returns:
        Nothing. Called once, at panel start-up: the panel opens with nothing analysed
        rather than showing a previous session's strategies as already done, which read as
        current results rather than the leftovers they are.
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
