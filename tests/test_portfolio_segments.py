#!/usr/bin/env python3
"""The segment discipline of the rank search (PLAN §8.4): it reads build and nothing later."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import portfolio.common.construct.real as real
import portfolio.common.construct.search.choose as choose
from portfolio_planted import CALENDAR, NAMES, planted_cfg, planted_pool

FAILURES = []
CONSTRUCT = Path(real.__file__).parent


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def search(daily: pd.DataFrame, cfg: dict) -> dict:
    """The command's own route from the universe's daily table to the chosen combination."""
    got = real.on_build(daily, CALENDAR, np.ones(len(NAMES)), cfg)
    found = choose.choose(got["unit"], got["dates"], got["graph"]["graph"], cfg, np.random.default_rng(0))
    return {**found, "graph": got["graph"]["graph"],
            "names": [NAMES[i] for i in np.flatnonzero(found["members"][found["best"]])]}


def test_later_rows_change_nothing() -> None:
    """(a) NaN in every oos1/oos2 row gives the very same search; the build-best wins, not the oos-best."""
    cfg = planted_cfg()
    full = planted_pool()
    blind = full.copy()
    blind.loc[CALENDAR["oos1"][0]:] = np.nan
    seen, unseen = search(full, cfg), search(blind, cfg)
    check("same graph, same combinations, same scores with oos1 and oos2 blanked",
          np.array_equal(seen["graph"], unseen["graph"]) and np.array_equal(seen["members"], unseen["members"])
          and seen["score"].tobytes() == unseen["score"].tobytes()
          and all(seen["table"][k].tobytes() == unseen["table"][k].tobytes() for k in seen["table"]))

    late = full.loc[CALENDAR["oos1"][0]:]
    later = choose.choose(late.to_numpy().T, late.index, seen["graph"], cfg, np.random.default_rng(0))
    oos_best = [NAMES[i] for i in np.flatnonzero(later["members"][later["best"]])]
    check("the pool's oos-best combination is another one (no A, no B) ...",
          not {"A", "B"} & set(oos_best) and len(oos_best) >= 1)
    check("... and the search returns the build-best {A, B}", seen["names"] == ["A", "B"])
    print(f"       build: {seen['names']} · oos1+oos2: {oos_best}")


def test_sources_name_no_later_segment() -> None:
    """(b) No module the search is made of names oos1 or oos2; the command cuts build once."""
    for folder in ("search", "pairs", "weights"):
        named = [p.name for p in sorted((CONSTRUCT / folder).glob("*.py"))
                 if re.search(r"oos[12]", p.read_text(encoding="utf-8"))]
        check(f"{folder}/: no module names oos1 or oos2 {named or ''}", not named)
    command = (CONSTRUCT / "real.py").read_text(encoding="utf-8")
    cuts = re.findall(r"matrix\.segment\([^)]*\)", command)
    check("real.py cuts the universe once, to build, and hands the search only that",
          len(cuts) == 1 and '"build"' in cuts[0] and command.count("choose.choose(") == 1)
    code = re.sub(r'f?"[^"\n]*"', "", command)        # the Spanish summary names the later segments, in words
    check("real.py's code (strings aside) names no later segment", not re.search(r"oos[12]", code))


def test_handoff_weights_are_the_judged_ones() -> None:
    """(c) The weights handed off are the build-segment, scaled ones the verdict used (D18)."""
    import tempfile

    from portfolio.common.construct import report
    cfg = planted_cfg()
    cfg["weights"]["method"] = "risk_parity"
    full = planted_pool()
    scale = np.linspace(1.0, 3.0, len(NAMES))
    seen = []
    report.handoff.write = lambda *a, **k: seen.append(a[4])     # the weights argument
    report.output.population = lambda *a, **k: None
    for segment in ("oos2", "oos1"):
        for frame in (full, full.copy()):
            if frame is not full:
                lo, hi = CALENDAR[segment]
                frame.loc[lo:hi] = frame.loc[lo:hi] * 7 + 3
            with tempfile.TemporaryDirectory() as tmp:
                run = Path(tmp)
                (run / "manifest.json").write_text("{}", encoding="utf-8")
                result = {"daily": frame, "calendar": CALENDAR, "scale": scale, "identities": NAMES,
                          "pool_name": "p"}
                report.write({"run": run, "result": result, "members": NAMES[:4], "pool": None},
                             {"verdict": {"label": "x", "pass": True}, "sentence": "", "root_seed": 1,
                              "population": None}, cfg)
    check("risk_parity weights do not move when oos1 or oos2 daily P&L is perturbed",
          len(seen) == 4 and all(seen[0] == w for w in seen[1:]))


def main() -> None:
    """Run every case; exit non-zero on any failure."""
    test_later_rows_change_nothing()
    test_sources_name_no_later_segment()
    test_handoff_weights_are_the_judged_ones()
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
