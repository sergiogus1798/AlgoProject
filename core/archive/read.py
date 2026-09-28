"""Read an archived strategy back in the shapes the daemon serves a live one — files only, nothing run."""

import json
from pathlib import Path

import pandas as pd

from core.paths import archive_dir


def versions(identity: str) -> list[str]:
    """The versions archived for one identity, oldest first.

    Args:
        identity: SHA-256 of the strategy's normalised XML.

    Returns:
        Version folder names (`YYYY-MM-DDTHHMM`); a half-built `.…partial` is not one.
    """
    folder = archive_dir() / identity
    return sorted(p.name for p in folder.iterdir()
                  if p.is_dir() and not p.name.startswith(".")) if folder.is_dir() else []


def listing() -> list[dict]:
    """Every archived strategy, one row per version.

    Returns:
        identity, version, strategy name, project, databank, step, archived_at and note,
        oldest identity first.
    """
    root = archive_dir()
    out = []
    for identity in sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        for version in versions(identity):
            doc = json.loads((root / identity / version / "manifest.json").read_text(encoding="utf-8"))
            view = json.loads((root / identity / version / "view.json").read_text(encoding="utf-8"))
            tear = view["tearsheet"]
            out.append({"identity": identity, "version": version,
                        "strategy": tear["strategy"] if isinstance(tear, dict) else None,
                        **{k: doc[k] for k in ("project", "databank", "step", "archived_at", "note")}})
    return out


def load(identity: str, version: str | None = None) -> dict:
    """One archived strategy, as the window would be served it live.

    Args:
        identity: SHA-256 of the strategy's normalised XML.
        version: A version folder name; None for the newest.

    Returns:
        `results`, `populations` ({databank: {study: what /api/result serves}}), `cells`
        ({databank: the matrix row}), `tearsheet` (what `harvest.read` returns, frames
        included, or its Spanish refusal), `gate` (`report` and `strategy` as the gate zone
        serves them, or None), plus `manifest`, `version`, `folder`, `sqx` (the frozen file)
        and `meta` (front E2's fields, or None). Each `meta.stale` is as of the day of
        archiving: judging it today would mean loading the study's config, which this
        reader never does.
    """
    held = versions(identity)
    if not held:
        raise FileNotFoundError(f"No hay ninguna versión archivada de {identity[:12]}… en {archive_dir()}")
    folder = archive_dir() / identity / (version or held[-1])
    shown = json.loads((folder / "view.json").read_text(encoding="utf-8"))
    if isinstance(shown["tearsheet"], dict):
        shown["tearsheet"]["equity"] = pd.read_parquet(folder / "tearsheet" / "equity.parquet")
        shown["tearsheet"]["trades"] = pd.read_parquet(folder / "tearsheet" / "trades.parquet")
    meta = folder / "meta.json"
    return {**shown, "manifest": json.loads((folder / "manifest.json").read_text(encoding="utf-8")),
            "version": folder.name, "folder": str(folder), "sqx": str(folder / "strategy.sqx"),
            "meta": json.loads(meta.read_text(encoding="utf-8")) if meta.is_file() else None}
