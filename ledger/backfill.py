#!/usr/bin/env python3
"""Rebuild a study's ledger backwards from the artefacts a run already left on disk."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core.paths import ROOT
from ledger import record, study as studymod

GATE_CONFIG = ROOT / "gate" / "config.yaml"
SCORE = "Sharpe Ratio [OOS]"   # what counts as a candidate's score, in SQX's own units


def thresholds_of(screen: str) -> dict:
    """What the gate's config says that screen was judged on.

    Args:
        screen: A screen name as `funnel.csv` spells it.

    Returns:
        Its row of `studies/screening/gate/config.yaml` minus the prose, so a funnel row carries the numbers
        it was produced under. A funnel read without its thresholds says nothing.
    """
    screens = yaml.safe_load(GATE_CONFIG.read_text(encoding="utf-8"))["screens"]
    row = next(s for s in screens if s["name"] == screen)
    return {k: v for k, v in row.items() if k not in ("name", "kind", "why")}


def scores_of(source: dict, column: str) -> np.ndarray:
    """The scores of every candidate the gate judged, from the harvest it read.

    Args:
        source: The `source` block of the gate manifest, which names its harvest.
        column: Which metric counts as the score, e.g. "Sharpe Ratio [OOS]".

    Returns:
        One value per strategy that entered. ⚠️ **SQX stores annualised Sharpes**, so the
        row records `score_unit: annualised` and whoever feeds a deflated Sharpe converts.
        Mixing the two units is the failure `trials.accumulated` refuses to commit.
    """
    metrics = pd.read_parquet(Path(source["harvest"]) / "metrics.parquet")
    return metrics[column].to_numpy(float)


def from_gate(folder: Path, study: str, symbol: str, timeframe: str) -> list[dict]:
    """One ledger row per screen of a gate run that already happened.

    Args:
        folder: A `reports/<project>/<databank>/<date>/gate/` directory.
        study: What `study.study_id` returned.
        symbol: The asset.
        timeframe: The grid the population was built on.

    Returns:
        The rows, oldest first, **not yet written**. Each screen is a search: it looked at
        data and reduced a population, which is the definition this ledger uses.

        The timestamp is the report's own date, not now, and every row is marked
        `backfill` in its note. A reconstructed row is weaker evidence than a recorded one
        -- it knows what the funnel counted and not what else was tried and discarded --
        and the note is what stops the two being confused later.
    """
    funnel = pd.read_csv(folder / "funnel.csv")
    source = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for screen in funnel.itertuples():
        # A soft screen informs and removes nobody, so recording its `passed` as the
        # population that came out would say the study ended with nothing left. The count
        # it reported goes in the note instead, where it cannot be read as a funnel.
        soft = screen.kind == "soft"
        rows.append({"study": study, "ts": source["date"], "step": 8,
                     "launched_by": source["command"], "symbol": symbol,
                     "timeframe": timeframe, "segment": "oos1",
                     "n_in": int(screen.entered),
                     "n_out": int(screen.entered if soft else screen.passed),
                     "criterion": f"studies/screening/gate/{screen.screen}",
                     "thresholds": thresholds_of(screen.screen),
                     "window_from": source["source"]["split"],
                     "window_to": source["source"]["end"],
                     "note": (f"backfill · {screen.kind} · {source['source']['project']}"
                              + (f" · informó {int(screen.passed)}" if soft else ""))})
    rows[0]["scores"] = scores_of(source["source"], SCORE)
    rows[0]["score_unit"] = "annualised"
    return rows


def main() -> None:
    """Reconstruct one study's ledger from a gate report and append it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", required=True, type=Path,
                    help="a reports/<project>/<databank>/<date>/gate/ directory")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--family", required=True, help="template or family the population came from")
    ap.add_argument("--write", action="store_true", help="append; without it, only print")
    a = ap.parse_args()

    study = studymod.study_id(a.symbol, a.timeframe, a.family)
    rows = from_gate(a.gate, study, a.symbol, a.timeframe)
    frame = pd.DataFrame(rows)[["criterion", "n_in", "n_out"]]
    print(f"{study}: {len(rows)} búsquedas reconstruidas de {a.gate}")
    print(frame.to_string(index=False))
    print(f"embudo: {rows[0]['n_in']} -> {rows[-1]['n_out']}")
    if not a.write:
        print("\n(sin --write no se ha escrito nada)")
        return
    for row in rows:
        scores = row.pop("scores", None)
        record.append(study, record.search(study, row, scores))
    print(f"\nescritas en {studymod.path(study)}")


if __name__ == "__main__":
    main()
