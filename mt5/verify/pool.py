#!/usr/bin/env python3
"""The validated pool of step 26: an append-only SQLite register of verdicts, the first verdict per check counts."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.paths import DATA, MT5_DATA
from ledger import study as ledger_study

ROOT = (
    DATA / "pool"
)  # holds `pool.sqlite` (owner, 2026-10-14: SQLite); the format lives behind this module only
RUNS = MT5_DATA / "verify"  # mt5.verify.run's folders, one per check
VALID = "pass"  # judge.firm_result's word for «Validada»
# judge.firm_result's summary: the trade counts, the clock shift and encargo 34's five rows
FIGURES = (
    "sqx_trades",
    "mt5_trades",
    "clock_h",
    "row_1",
    "row_2",
    "row_3a",
    "row_3b",
    "row_4",
    "row_5",
)
COLUMNS = (
    "identity",
    "strategy",
    "project",
    "mother",
    "symbol",
    "timeframe",
    "firm",
    "run",
    "verified_on",
    "window_from",
    "window_to",
    "model",
    "verdict",
    "thresholds_hash",
    "config_hash",
    *FIGURES,
    "file",
    "recorded_on",
)


def path() -> Path:
    """The register's database file."""
    return ROOT / "pool.sqlite"


def connect() -> sqlite3.Connection:
    """The register, created with its one table on first use."""
    path().parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path())
    db.execute(
        f"CREATE TABLE IF NOT EXISTS verdicts ({', '.join(c + ' TEXT' for c in COLUMNS)})"
    )
    return db


def thresholds_hash(meta: dict, firm: str) -> str:
    """The thresholds one firm's verdict was given under, hashed: read off the ledger row the
    check left (`note` ends with the run, `criterion` names the firm), never off today's
    `ledger/thresholds.yaml` — they may have moved since.

    Returns:
        The first 16 hex digits of the sha256 of the thresholds' sorted JSON; "" when no
        ledger row names the run.
    """
    rows = ledger_study.read(
        ledger_study.study_id(meta["asset"], meta["timeframe"], "mt5verify")
    )
    if "note" not in rows:
        return ""
    mine = rows[
        rows["note"].astype(str).str.endswith(meta["run"])
        & rows["criterion"].astype(str).str.contains(f" en {firm} ", regex=False)
    ]
    if mine.empty:
        return ""
    text = json.dumps(mine.iloc[-1]["thresholds"], sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def rows_of(run: Path, project: str = "", finalist: dict | None = None) -> list[dict]:
    """The register rows one finished check gives: one per firm it judged.

    Args:
        run: A folder of `RUNS`, with its `run.json` and `result.json`.
        project: The workflow project the strategy comes from; "" when nobody says.
        finalist: The autopilot's finalist (`mother`), when the check came from it.

    Returns:
        A dict per judged firm, keys `COLUMNS`. Empty for a check that crashed. A firm the
        check refused (no commission, no symbol) is not a verdict and gets no row, nor does
        one without a verdict (`none`: too few SQX trades).
    """
    meta = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if meta["state"] != "done":
        return []
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    now = datetime.now().isoformat(timespec="seconds")
    return [
        {
            "identity": meta["identity"],
            "strategy": meta["strategy"],
            "project": project,
            "mother": (finalist or {}).get("mother", ""),
            "symbol": meta["asset"],
            "timeframe": meta["timeframe"],
            "firm": firm,
            "run": meta["run"],
            "verified_on": meta["ended"],
            "window_from": meta["from"],
            "window_to": meta["to"],
            "model": meta["model"],
            "verdict": s["state"],
            "thresholds_hash": thresholds_hash(meta, firm),
            "config_hash": result["config_hash"],
            **{k: s[k] for k in FIGURES},
            "file": meta["file"],
            "recorded_on": now,
        }
        for firm, s in result["summary"]["firms"].items()
        if s["state"] != "none"
    ]


def record(rows: list[dict]) -> None:
    """Append rows to the register. Nothing is ever rewritten: a second verdict for the same
    strategy is a new line, and `read` keeps the first."""
    with closing(connect()) as db, db:
        db.executemany(
            f"INSERT INTO verdicts VALUES ({','.join('?' * len(COLUMNS))})",
            [[str(r[c]) for c in COLUMNS] for r in rows],
        )


def history(firm: str) -> pd.DataFrame:
    """Every verdict ever recorded for one firm, in the order written; text columns.
    An empty frame for a firm nobody has verified on yet."""
    if not path().exists():
        return pd.DataFrame(columns=list(COLUMNS), dtype=str)  # pyright: ignore[reportArgumentType]  # pandas stubs
    with closing(connect()) as db:
        return pd.read_sql_query(
            "SELECT * FROM verdicts WHERE firm = ? ORDER BY rowid", db, params=[firm]
        )


def firms() -> list[str]:
    """The firms with at least one verdict, sorted; none (and no file made) before the first."""
    if not path().exists():
        return []
    with closing(connect()) as db:
        return [
            r[0] for r in db.execute("SELECT DISTINCT firm FROM verdicts ORDER BY firm")
        ]


def validated() -> dict[str, list[str]]:
    """Identity -> the firms it is validated for (`read` of each): what the portfolio side marks."""
    out: dict[str, list[str]] = {}
    for firm in firms():
        for identity in read(firm)["identity"]:
            out.setdefault(identity, []).append(firm)
    return out


def read(firm: str) -> pd.DataFrame:
    """The strategies validated for one firm — what the portfolio side reads.

    Returns:
        One row per (identity, window, model) whose FIRST verdict (by `verified_on`) is
        `VALID` (owner, 2026-10-11): a rerun stays in `history` but changes nothing here, so
        a strategy cannot be re-rolled until it passes.
    """
    key = ["identity", "window_from", "window_to", "model"]
    first = history(firm).sort_values("verified_on", kind="stable").groupby(key).head(1)
    return first[first["verdict"] == VALID].reset_index(drop=True)  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing


def rebuild(runs: Path | None = None) -> list[dict]:
    """The rows of every finished check on disk, oldest first — nothing written."""
    return [
        row
        for f in sorted((runs or RUNS).glob("*/run.json"))
        for row in rows_of(f.parent)
    ]


def pending(rows: list[dict]) -> list[dict]:
    """Those rows whose (run, firm) the register does not hold yet."""
    held = {firm: set(history(firm)["run"]) for firm in {r["firm"] for r in rows}}
    return [r for r in rows if r["run"] not in held[r["firm"]]]


def main() -> None:
    """Print each firm's validated strategies, or first add the checks on disk not yet in."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild",
        action="store_true",
        help="anota antes las verificaciones de AlgoData/mt5/verify que falten",
    )
    a = ap.parse_args()
    if a.rebuild:
        new = pending(rebuild())
        record(new)
        print(f"{len(new)} filas nuevas en {ROOT}")
    show = [
        "strategy",
        "symbol",
        "timeframe",
        "verified_on",
        "window_from",
        "window_to",
        "model",
        "run",
    ]
    for firm in firms():
        valid = read(firm)
        print(
            f"\n{firm}: {len(valid)} validadas de "
            f"{history(firm)['identity'].nunique()} verificadas"
        )
        if len(valid):
            print(valid[show].to_string(index=False))


if __name__ == "__main__":
    main()
