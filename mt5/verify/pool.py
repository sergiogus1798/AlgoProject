#!/usr/bin/env python3
"""The validated pool of step 26: an append-only register per prop firm, the first verdict per check counts."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.paths import DATA, MT5_DATA
from ledger import study as ledger_study

ROOT = DATA / "pool"            # one <firm>.csv each; the format lives behind this module only
RUNS = MT5_DATA / "verify"      # mt5.verify.run's folders, one per check
VALID = "pass"                  # judge.firm_result's word for «Validada»
# judge.firm_result's summary: the trade counts, the clock shift and encargo 34's five rows
FIGURES = ("sqx_trades", "mt5_trades", "clock_h", "row_1", "row_2", "row_3a", "row_3b", "row_4",
           "row_5")
COLUMNS = ("identity", "strategy", "project", "mother", "symbol", "timeframe", "firm", "run",
           "verified_on", "window_from", "window_to", "model", "verdict", "thresholds_hash",
           "config_hash", *FIGURES, "stop_percentile", "stop_x", "file", "recorded_on")


def path(firm: str) -> Path:
    """One firm's register file."""
    return ROOT / f"{firm}.csv"


def thresholds_hash(meta: dict, firm: str) -> str:
    """The thresholds one firm's verdict was given under, hashed: read off the ledger row the
    check left (`note` ends with the run, `criterion` names the firm), never off today's
    `ledger/thresholds.yaml` — they may have moved since.

    Returns:
        The first 16 hex digits of the sha256 of the thresholds' sorted JSON; "" when no
        ledger row names the run.
    """
    rows = ledger_study.read(ledger_study.study_id(meta["asset"], meta["timeframe"], "mt5verify"))
    if "note" not in rows:
        return ""
    mine = rows[rows["note"].astype(str).str.endswith(meta["run"])
                & rows["criterion"].astype(str).str.contains(f" en {firm} ", regex=False)]
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
    return [{"identity": meta["identity"], "strategy": meta["strategy"], "project": project,
             "mother": (finalist or {}).get("mother", ""), "symbol": meta["asset"],
             "timeframe": meta["timeframe"], "firm": firm, "run": meta["run"],
             "verified_on": meta["ended"], "window_from": meta["from"],
             "window_to": meta["to"], "model": meta["model"], "verdict": s["state"],
             "thresholds_hash": thresholds_hash(meta, firm),
             "config_hash": result["config_hash"],
             **{k: s[k] for k in FIGURES},
             "stop_percentile": "", "stop_x": "",     # legacy columns of the append-only registers (step 24 is gone)
             "file": meta["file"], "recorded_on": now}
            for firm, s in result["summary"]["firms"].items() if s["state"] != "none"]


def record(rows: list[dict]) -> None:
    """Append rows to their firms' registers. Nothing is ever rewritten: a second verdict
    for the same strategy is a new line, and `read` keeps the first."""
    for firm, mine in pd.DataFrame(rows, columns=list(COLUMNS)).groupby("firm", sort=False):
        out = path(firm)
        out.parent.mkdir(parents=True, exist_ok=True)
        mine.to_csv(out, mode="a", header=not out.exists(), index=False)


def history(firm: str) -> pd.DataFrame:
    """Every verdict ever recorded for one firm, in the order written; text columns.
    An empty frame for a firm nobody has verified on yet."""
    if not path(firm).exists():
        return pd.DataFrame(columns=list(COLUMNS), dtype=str)
    return pd.read_csv(path(firm), dtype=str, keep_default_na=False)


def read(firm: str) -> pd.DataFrame:
    """The strategies validated for one firm — what the portfolio side reads.

    Returns:
        One row per (identity, window, model) whose FIRST verdict (by `verified_on`) is
        `VALID` (owner, 2026-10-11): a rerun stays in `history` but changes nothing here, so
        a strategy cannot be re-rolled until it passes.
    """
    key = ["identity", "window_from", "window_to", "model"]
    first = history(firm).sort_values("verified_on", kind="stable").groupby(key).head(1)
    return first[first["verdict"] == VALID].reset_index(drop=True)


def rebuild(runs: Path | None = None) -> list[dict]:
    """The rows of every finished check on disk, oldest first — nothing written."""
    return [row for f in sorted((runs or RUNS).glob("*/run.json")) for row in rows_of(f.parent)]


def pending(rows: list[dict]) -> list[dict]:
    """Those rows whose (run, firm) the register does not hold yet."""
    held = {firm: set(history(firm)["run"]) for firm in {r["firm"] for r in rows}}
    return [r for r in rows if r["run"] not in held[r["firm"]]]


def main() -> None:
    """Print each firm's validated strategies, or first add the checks on disk not yet in."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild", action="store_true",
                    help="anota antes las verificaciones de AlgoData/mt5/verify que falten")
    a = ap.parse_args()
    if a.rebuild:
        new = pending(rebuild())
        record(new)
        print(f"{len(new)} filas nuevas en {ROOT}")
    show = ["strategy", "symbol", "timeframe", "verified_on", "window_from", "window_to",
            "model", "run"]
    for file in sorted(ROOT.glob("*.csv")):
        valid = read(file.stem)
        print(f"\n{file.stem}: {len(valid)} validadas de "
              f"{history(file.stem)['identity'].nunique()} verificadas")
        if len(valid):
            print(valid[show].to_string(index=False))


if __name__ == "__main__":
    main()
