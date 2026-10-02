"""Write mt5.verify.run's result.json (the study contract) and its run.json, and mark a crash."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.study import result as study_result
from mt5.verify import firms

MODULE = "mt5.verify"


def finish(work: Path, meta: dict, cfg: dict, started: float, summaries: dict, refused: dict,
          why: str, tabs: list | None = None) -> None:
    """Write result.json in the study contract, and the run's state beside it."""
    tabs = list(tabs or [])
    rows = [{"empresa": firms.label(f), "veredicto": "Validada" if s["state"] == "pass" else
            "No validada", "reloj (h)": s["clock_h"], "operaciones SQX": s["sqx_trades"],
             "operaciones MT5": s["mt5_trades"]} for f, s in summaries.items()]
    rows += [{"empresa": firms.label(f), "veredicto": "No se pudo verificar", "reloj (h)": None,
              "operaciones SQX": None, "operaciones MT5": None} for f in refused]
    states = [s["state"] for s in summaries.values()]
    # Each firm is judged alone: one that validates is amber, never the red of none (📓 2026-09-30)
    overall = ("pass" if states and all(s == "pass" for s in states) else
               "watch" if "pass" in states else "fail" if states else "none")
    head = {"name": "resumen", "title": "Resumen",
            "note": (f"{meta['strategy']} · {meta['asset']} {meta['timeframe']} · "
                     f"{meta['from']} → {meta['to']} · modelo del tester «{meta['model']}». "
                     + " ".join(f"{firms.label(f)}: {w}" for f, w in refused.items())),
            "blocks": [study_result.blocks.table(
                "Cada empresa", pd.DataFrame(rows, columns=["empresa", "veredicto", "reloj (h)",
                                                            "operaciones SQX", "operaciones MT5"]),
                "una estrategia puede valer para una empresa y no para otra")]}
    good = [firms.label(f) for f, s in summaries.items() if s["state"] == "pass"]
    bad = [firms.label(f) for f, s in summaries.items() if s["state"] != "pass"]
    meaning = why or (
        (f"Validada en {', '.join(good)}: SQX reproduce su cuenta y su histórico largo vale para "
         "ella. " if good else "") +
        (f"No validada en {', '.join(bad)}: SQX no reproduce lo que el EA hace en su cuenta; la "
         "pestaña de cada una dice qué fila falla. " if bad else "") +
        "Cada empresa se juzga por separado.")
    verdict = study_result.blocks.verdict(
        {"pass": "Validada", "watch": f"Validada en {', '.join(good)}", "fail": "No validada",
         "none": "Sin verificar"}[overall], overall, meaning)
    out = study_result.envelope(MODULE, meta["strategy"], meta["identity"], cfg, started,
                                [head, *tabs], verdict, summary={"firms": summaries,
                                                                  "refused": refused})
    (work / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    meta.update({"state": "done" if summaries else "failed", "verdict": overall,
                 "firms": {f: s["state"] for f, s in summaries.items()}, "refused": refused,
                 "ended": datetime.now().isoformat(timespec="seconds")})
    (work / "run.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False),
                                   encoding="utf-8")


def failed(runs_dir: Path, error: str) -> None:
    """A run that stopped half-way says so in its run.json, so the window never shows it running."""
    for f in sorted(runs_dir.glob("*/run.json"), reverse=True)[:1]:
        meta = json.loads(f.read_text(encoding="utf-8"))
        if meta.get("state") == "running":
            meta.update({"state": "failed", "error": error,
                         "ended": datetime.now().isoformat(timespec="seconds")})
            f.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
