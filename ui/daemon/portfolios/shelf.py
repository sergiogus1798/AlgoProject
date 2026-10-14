"""What exists under the portfolio folder: pools, runs, universes, bank tables — listed, never computed."""

import json
import os
from pathlib import Path
from typing import Any, TypedDict

from core.paths import portfolio_dir
from portfolio.common.construct.inputs import pool as pool_mod
from ui.daemon.archive import shelf as archive

ROOT = portfolio_dir()

RunRow = TypedDict(
    "RunRow",
    {
        "id": str,
        "pool": str,
        "kind": str,
        "plan": str,
        "firm": str,
        "members": list[str],
        "k": int,
        "score": float | None,
        "label": str,
        "pass": bool | None,
        "relaxed": dict[str, Any],
        "forced": str,
        "stage_b": bool,
        "handoff": bool,
    },
)
RunRow.__doc__ = "One run folder as the «Carteras» tab lists it."


def test_root() -> str:
    """The test root this daemon runs under («RAÍZ DE PRUEBA»), "" on the real root."""
    return os.environ.get("ALGO_DATA_ROOT", "")


def short(identity: str) -> str:
    """An identity as the commands print it: its first eight characters."""
    return identity[:8]


def load(path: Path) -> dict[str, Any]:
    """One JSON file of a run folder."""
    return json.loads(path.read_text(encoding="utf-8"))


def names() -> dict[str, dict]:
    """Identity → the archived strategy's row (`strategy`, `symbol`, `timeframe`…)."""
    return {r["identity"]: r for r in archive.strategies()}


def label(identity: str, known: dict[str, dict]) -> str:
    """What a member is called on screen: its strategy name and its short identity."""
    name = known.get(identity, {}).get("strategy")
    return f"{name} · {short(identity)}" if name else short(identity)


def pools() -> list[dict]:
    """Every declared pool: `name`, `hash`, `members` (identities), newest file first."""
    out = []
    files = sorted(
        (ROOT / "pools").glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    for file in files:
        got = pool_mod.read(file.stem, None)
        out.append(
            {
                "name": file.stem,
                "hash": got["hash"],
                "members": [m["identity"] for m in got["members"]],
            }
        )
    return out


def folder(kind: str, name: str) -> Path:
    """A named folder under `runs`, `bank`, `weights_wf`…, refused unless it is a plain name there."""
    path = ROOT / kind / name
    if not name or Path(name).name != name or not path.is_dir():
        raise FileNotFoundError(f"No existe {kind}/{name} en {ROOT}.")
    return path


def run(path: Path) -> RunRow:
    """One run folder as the «Carteras» tab lists it."""
    m = load(path / "manifest.json")
    v = load(path / "verdict.json") if (path / "verdict.json").exists() else {}
    funded = "plan" in m
    judged = (v.get("verdict") or {}) if funded else v
    best = m.get("best") or {}
    members = (judged.get("chosen") or {}).get("members") or m.get("best_members") or []
    return {
        "id": path.name,
        "pool": m["pool"],
        "kind": "funded" if funded else "real",
        "plan": m.get("plan", ""),
        "firm": m.get("firm") or "",
        "members": members,
        "k": len(members),
        "score": m.get("best_score") if funded else best.get("score"),
        "label": judged.get("label")
        or (m.get("verdict") or {}).get("label")
        or ("solo etapa A" if funded else "sin juzgar"),
        "pass": judged.get("pass"),
        "relaxed": m.get("relaxed") or {},
        "forced": m.get("forced", ""),
        "stage_b": (path / "stageb.parquet").exists(),
        "handoff": (path / "handoff" / "daily.parquet").exists(),
    }


def runs() -> list[RunRow]:
    """Every run with a manifest, newest first."""
    found = sorted((ROOT / "runs").glob("*/manifest.json"), reverse=True)
    return [run(m.parent) for m in found]


def universes(pool_hash: str) -> list[Path]:
    """A pool's universe folders the pair screen ran on (`pairs.parquet`), newest screen first.

    `real` and `funded` build universes too, under their own config's fingerprint, without
    writing the pair table: those hold nothing «Correlación» can paint.
    """
    found = list((ROOT / "universe").glob(f"{pool_hash}-*/pairs.parquet"))
    return [
        m.parent for m in sorted(found, key=lambda m: m.stat().st_mtime, reverse=True)
    ]
