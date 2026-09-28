"""The archive as PORTFOLIOS lists it: one row per strategy with its versions, one version in full."""

import json
import math

from core.archive import read
from core.paths import archive_dir
from ui.daemon.results import catalogue


def _manifest(identity: str, version: str) -> dict:
    """One version's `manifest.json`."""
    return json.loads((archive_dir() / identity / version / "manifest.json").read_text(encoding="utf-8"))


def _ledger(doc: dict) -> dict:
    """The ledger count frozen that day: searches, strategies tried (N) and their Sharpe σ."""
    held = doc["ledger"]
    trials = held["trials"]
    sigma = trials.get("sigma")
    return {"study": held["study"], "searches": held["searches"], "n": trials["n"],
            "sigma": None if sigma is None or math.isnan(sigma) else sigma}


def _version(row: dict, doc: dict) -> dict:
    """One version as the list shows it: stamp, when, at which step, the owner's note."""
    return {"version": row["version"], "archived_at": row["archived_at"], "step": row["step"],
            "note": row["note"], "databank": row["databank"], "ledger": _ledger(doc)}


def strategies() -> list[dict]:
    """Every archived strategy, newest archive first.

    Returns:
        One dict per identity: `identity`, `strategy` (its name in the databank), `project`,
        `symbol`, `timeframe` (the project's registry row), `step`, `archived_at` and
        `ledger` of its newest version, and `versions` oldest first.
    """
    by_id: dict[str, list] = {}
    for row in read.listing():
        by_id.setdefault(row["identity"], []).append(
            (row, _manifest(row["identity"], row["version"])))
    out = []
    for identity, held in by_id.items():
        row, doc = held[-1]
        registry = doc.get("registry") or {}
        out.append({"identity": identity, "strategy": row["strategy"], "project": row["project"],
                    "symbol": registry.get("symbol") or doc["asset"]["symbol"],
                    "timeframe": registry.get("timeframe"), "step": row["step"],
                    "archived_at": row["archived_at"], "ledger": _ledger(doc),
                    "versions": [_version(r, d) for r, d in held]})
    return sorted(out, key=lambda r: r["archived_at"], reverse=True)


def show(identity: str, version: str = "") -> dict:
    """One archived version in full: what it froze, what it could not, and its provenance.

    Args:
        identity: The strategy's identity.
        version: A version folder name; "" for the newest.

    Returns:
        The header fields of `strategies`, plus `version`, `note`, `databank`,
        `code_version`, `held` ({databank: [{study, title, family, step, config_hash,
        day}]} — the per-strategy results the Estrategia page will show), `skipped`
        ([{path, reason}], absent before that key existed), `loose`, `asset`
        ({symbol, sha256}) and `sqx` ({by_hand}); raises FileNotFoundError without one.
    """
    got = read.load(identity, version or None)
    doc = got["manifest"]
    hashes = {(s["databank"], s["study"]): s for s in doc["studies"]}
    held = {}
    for databank, studies in got["results"].items():
        held[databank] = [
            {"study": k, "title": catalogue.STUDIES[k][2], "family": catalogue.STUDIES[k][0],
             "step": catalogue.STUDIES[k][3],
             "config_hash": hashes.get((databank, k), {}).get("config_hash"),
             "day": hashes.get((databank, k), {}).get("day")}
            for k in catalogue.ordered() if k in studies]
    registry = doc.get("registry") or {}
    tear = got["tearsheet"]
    return {"identity": identity, "version": got["version"],
            "strategy": tear["strategy"] if isinstance(tear, dict) else None,
            "project": doc["project"], "databank": doc["databank"], "step": doc["step"],
            "note": doc["note"], "archived_at": doc["archived_at"],
            "symbol": registry.get("symbol") or doc["asset"]["symbol"],
            "timeframe": registry.get("timeframe"), "code_version": doc["code_version"],
            "ledger": _ledger(doc), "held": held, "skipped": doc.get("skipped"),
            "loose": doc.get("loose", []),
            "asset": {"symbol": doc["asset"]["symbol"], "sha256": doc["asset"]["sha256"]},
            "sqx": {"by_hand": bool(doc["sqx"].get("by_hand"))}}
