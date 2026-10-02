#!/usr/bin/env python3
"""Research memory: the resumen parser, the funnel's outcomes, the ideas index, the queries and the
verdict writer, on small fixture files in a temp dir (nothing of AlgoData is read or written)."""

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.research.memory import attempts, ideas, queries, sources, verdict

RESUMEN_OK = """# Autopiloto · Test_XAUUSD_x_H1 · 20261001-100000

| paso | tipo | s | qué hizo |
|---|---|---|---|
| - | arranque | 30 | sesión GUI del custodio |
| 6+7 | sqx | 700 | CONSTRUCCION: 0 → 300 · OOS: 0 → 300 |
| 8 | judge | 1 | 5849 hechos; OOS: 300 → 5 por sorteo de 5 (semilla 1) |
| 9 | sqx | 80 | Retest Markets - Family: 0 → 5 |
| 11 | sqx | 150 | CrossTF: 0 → 20 |
| 13 | sqx | 900 | MCR 1 Bar: 0 → 5 · MCR 8 Stress: 0 → 4 |
| 15 | sqx | 580 | SPP IS: 0 → 4 · SPP OOS: 0 → 3 |

Total 60.0 min. Se para antes del paso 16.5: nada.
"""
RESUMEN_DIED = RESUMEN_OK.replace("OOS: 300 → 5 por sorteo de 5 (semilla 1)", "OOS: 300 → 0").split("| 9 |")[0]
RESUMEN_DIED += "\nTotal 12.0 min. Se para.\n"
IDEAS = """# Ideas para XAUUSD
## 1. Las tres ideas
### Idea 1 (recomendada) — `atrUp` · H4 · largo
Origen: libro de Katz, cap. 3
### Idea 2 — `atrDown` · H4 · **corto**
texto
## 3. Hipótesis medidas: **24**, todas sobre `build`
"""
REGISTRY = ("name,archetype,shape\natrUp,breakout,market_long\nemaX,trendFollowing,market_long\n"
            "shellS,free,market_short\n")
PROJECTS = ("name,kind,install,created,purpose,symbol,timeframe,template,workflow,retired,archive\n"
            "Test_XAUUSD_x_H1,test,SQX_w2,2026-10-01 10:00,p,XAUUSD,H1,/d/templates/library/atrUp/t.sqx,"
            "yes,,\nTest_XAUUSD_died_H1,test,SQX_w2,2026-10-01 11:00,p,XAUUSD,H1,"
            "/d/templates/library/emaX/t.sqx,yes,,\nTest_MT5Verify_X,test,SQX_w1,2026-10-01 11:00,p,"
            "XAUUSD,H1,/other/s.sqx,no,,\n")
RUNS = ("template,symbol,timeframe,project,date,strategies_built,strategies_kept,verdict,report\n"
        "emaX,USDJPY,H1,Old_Run,2026-09-24,50,50,hand typed,doc.md\n")


def fixture(root: Path) -> Path:
    """Write the fixture tree and point the readers at it; returns the runs.csv."""
    (root / "autopilot/Test_XAUUSD_x_H1/20261001-100000").mkdir(parents=True)
    (root / "autopilot/Test_XAUUSD_x_H1/20261001-100000/resumen.md").write_text(RESUMEN_OK)
    died = root / "autopilot/Test_XAUUSD_died_H1/20261001-110000"
    died.mkdir(parents=True)
    (died / "resumen.md").write_text(RESUMEN_DIED)
    (root / "ideas/XAUUSD").mkdir(parents=True)
    (root / "ideas/XAUUSD/2026-10-01-a.md").write_text(IDEAS)
    for name, text in (("registry.csv", REGISTRY), ("projects.csv", PROJECTS), ("runs.csv", RUNS)):
        (root / name).write_text(text)
    sources.autopilot_runs = lambda: root / "autopilot"
    sources.project_registry = lambda: root / "projects.csv"
    sources.template_registry = lambda: root / "registry.csv"
    sources.template_runs = lambda: root / "runs.csv"
    ideas.ideas_dir = lambda: root / "ideas"
    return root / "runs.csv"


def test_parse() -> None:
    """Parse."""
    got = sources.parse_resumen(RESUMEN_OK)
    assert got["stages"] == {"built": 300, "oos": 300, "gate": 5, "markets": 5, "mcr": 4, "spp": 3}
    assert got["crosstf"] == 20 and got["minutes"] == 60.0 and got["dev_cut"] and not got["failed"]


def test_outcomes(root: Path) -> None:
    """Outcomes."""
    rows = {r["project"]: r for r in attempts.table()}
    ok, died = rows["Test_XAUUSD_x_H1"], rows["Test_XAUUSD_died_H1"]
    assert (ok["outcome"], ok["survivors"], ok["dev_cut"], ok["custodian_hours"]) == ("survivors", 3, "yes", 1.0)
    assert (ok["family"], ok["direction"], ok["asset_class"]) == ("ruptura", "long", "metal")
    assert (died["outcome"], died["died_at"], died["survivors"]) == ("died@gate", "gate", 0)
    assert "Test_MT5Verify_X" not in rows                      # no library template: not an attempt
    old = rows["Old_Run"]
    assert (old["outcome"], old["built"], old["verdict"]) == ("unknown", 50, "hand typed")
    assert attempts.funnel({"built": 9, "oos": 0}, "")["outcome"] == "died@oos"
    assert attempts.funnel({"built": 9, "oos": 0}, "7")["outcome"] == "failed@7"   # zero after a crash
    assert attempts.funnel({}, "")["outcome"] == "unknown"


def test_ideas_and_queries() -> None:
    """Ideas and queries."""
    rows = attempts.table({"atrUp"})
    idea_rows = ideas.index(rows)
    assert [(i["idea"], i["direction"], i["hypotheses_measured"], i["from_book"]) for i in idea_rows] == [
        ("atrUp", "long", 24, "yes"), ("atrDown", "short", 24, "unknown")]
    assert idea_rows[0]["chosen"] == "yes" and idea_rows[0]["attempts"] == 1
    spent = queries.ideas_spent(idea_rows)
    assert {(s["timeframe"], s["direction"], s["family"], s["ideas"], s["hypotheses"]) for s in spent} == {
        ("H4", "long", "ruptura", 1, 24), ("H4", "short", "", 1, 24)}
    shown = {(r["family"], r["asset_class"]): r for r in queries.survivors_by_family(rows)}
    assert shown[("ruptura", "metal")]["closed"] == 0           # a dev run is not evidence by default
    assert shown[("tendencia", "metal")] | {} == {"family": "tendencia", "asset_class": "metal",
        "attempts": 1, "closed": 1, "with_survivors": 0, "survivors": 0}
    assert ("tendencia", "forex") in shown and ("ruptura", "forex") not in shown
    dev = {(r["family"], r["asset_class"]): r for r in queries.survivors_by_family(rows, include_dev=True)}
    assert dev[("ruptura", "metal")]["with_survivors"] == 1 and dev[("ruptura", "metal")]["survivors"] == 3
    assert len(queries.untouched_cells(rows)) == len(queries.grid()) - 3


def test_writer(root: Path) -> None:
    """Writer."""
    copy = root / "copy.csv"
    copy.write_text((root / "runs.csv").read_text())
    run = root / "autopilot/Test_XAUUSD_x_H1/20261001-100000"
    got = verdict.close_run(run, copy)
    assert (got["strategies_built"], got["strategies_kept"], got["template"]) == ("300", "3", "atrUp")
    assert got["verdict"].startswith("auto: embudo built 300 -> oos 300 -> gate 5")
    assert "no es evidencia" in got["verdict"] and "llegaron 3" in got["verdict"]
    rows = list(csv.DictReader(open(copy)))
    assert len(rows) == 2 and rows[0]["verdict"] == "hand typed"      # the other row is untouched
    verdict.close_run(run, copy)                                     # idempotent
    assert len(list(csv.DictReader(open(copy)))) == 2
    died = verdict.close_run(root / "autopilot/Test_XAUUSD_died_H1/20261001-110000", copy)
    assert "murio en el paso 8" in died["verdict"]
    typed = list(csv.DictReader(open(copy)))
    mine = next(r for r in typed if r["project"] == "Test_XAUUSD_x_H1")
    mine["verdict"], mine["strategies_kept"] = "el dueno dice no", "1"
    verdict.write(copy, typed, list(typed[0]))
    kept = verdict.close_run(run, copy)
    assert (kept["verdict"], kept["strategies_kept"]) == ("el dueno dice no", "1")   # typed wins
    assert (root / "runs.csv").read_text() == RUNS                    # the real-shaped source is untouched


def main() -> None:
    """Run every test of this file."""
    test_parse()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture(root)
        test_outcomes(root)
        test_ideas_and_queries()
        test_writer(root)
    print("test_research_memory: ok")


if __name__ == "__main__":
    main()
