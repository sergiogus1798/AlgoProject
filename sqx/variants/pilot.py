#!/usr/bin/env python3
"""The pilot: fabricate and retest a few hundred sampled tuples before the full batch exists."""

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from sqx.variants import execute, inputs, legs as legmod, livexec, tuples, united
from sqx.variants.build import fabricate
from sqx.variants.design import levels, pilot as designpilot

COLLISION = re.compile(r"\(\d+\)$")   # the collision suffix SQX appends to a duplicate on reload


def run(design: dict, settings: dict, live: dict[str, list[float]], work: Path, project: str,
       say: Callable[[int, str], None]) -> tuple[dict, dict]:
    """Score a few hundred sampled tuples on trade count, on the mother's own project.

    Args:
        design: A parsed brief.
        settings: The parsed `config.yaml`.
        live: Output of `design.levels.live` -- the space the pilot samples.
        work: The strategy's work directory; the pilot writes into `work/pilot/`.
        project: The custom project already retesting this mother's batch (never a stock
            one). The pilot piggybacks on it rather than creating anything of its own: same
            install, same per-task costs, same `execute.awake`/`load`/`run`/`synced` the
            full batch retest uses -- it is a smaller load into the same databanks, cleared
            by the very next `execute.load` either way.
        say: Called with a percentage and a status line.

    Returns:
        `(banned, report)`: `design.pilot.decide`'s two return values, with `tested` and
        `project` folded into the report for the manifest.

    Raises:
        SystemExit: `project` is a stock project (hard rule 10).
    """
    if project in execute.STOCK:
        raise SystemExit(f"{project} es un proyecto de serie: regla dura 10, el piloto necesita "
                         "el mismo proyecto custom del lote, nunca Builder o Retester.")
    cfg = dict(settings["execute"], project=project)
    pcfg = settings["pilot"]
    parent = inputs.source(design)
    table = designpilot.sample(live, pcfg)
    folder = work / "pilot" / "sqx"
    say(2, f"fabricando el piloto: {len(table)} tuplas")
    param_names = [c for c in table.columns if c != "pilot_id"]
    plan_rows = table.rename(columns={"pilot_id": "variant_id",
                                      **{n: tuples.PREFIX + n for n in param_names}})
    fabricate.batch(plan_rows, parent, design["strategy"], folder, "minimal")

    legs = legmod.legs()
    be = livexec.backend(cfg)
    ours = be.awake(cfg)
    try:
        say(5, f"cargando el piloto en {project}/{legmod.source()}")
        be.load(folder, cfg)
        done = be.run(len(table) * len(legs), cfg,
                           lambda p, line: say(5 + p * 80 // 100, line)) // len(legs)
        bank, _ = be.synced(done, cfg, legs[0]["databank"])
        rows = united.per_result(bank, legs[0]["segment"], lambda *_a: None)
    finally:
        if ours:
            worker.stop(cfg["role"])

    main_rows = rows[rows["market"] == legmod.MAIN].copy()
    main_rows["variant_id"] = main_rows["variant_id"].str.replace(COLLISION, "", regex=True)
    counts = dict(zip(main_rows["variant_id"], main_rows["NumberOfTrades"]))
    banned, report = designpilot.decide(table, counts, pcfg["min_trades"], pcfg["min_support"])
    return banned, {**report, "tested": done, "project": project, "segment": legs[0]["segment"]}


def main() -> None:
    """Run the pilot on its own, for a brief that already exists -- mostly for a dry look."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--brief", required=True, type=Path)
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    design = inputs.brief(a.brief)
    settings = inputs.load()
    live = levels.live(design, settings["minimum"])
    banned, report = run(design, settings, live, a.out, a.project,
                         lambda pct, line: print(f"PROGRESS {pct} {line}", flush=True))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "pilot.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    dropped = sum(len(v) for v in banned.values())
    print(f"\n{report['tested']} reteseadas, {dropped} niveles descartados en "
          f"{len(banned)} parametros (< {report['min_trades']} operaciones en "
          f"{report['segment']})")
    print(f"-> {a.out / 'pilot.json'}")


if __name__ == "__main__":
    main()
