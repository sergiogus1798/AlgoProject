"""One judging step: its facts, the criteria, the medoid cut, the verdict.csv and the cut in SQX."""

import hashlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import yaml

from core import assetdata
from core.paths import databank_dir, export_dir, harvest_dir, metrics_export
from ledger import cells, record, study as studymod
from pipeline.autopilot import criteria, facts, selection, survivors, trim
from sqx.curate import apply_verdict
from sqx.projects import registry
from sqx.projects.crosstfload import SIBLING
from ui.daemon.advance.preflight import by_identity
from ui.daemon.loader import find, state
from ui.daemon.loader.fingerprint import fingerprint

CRITERIA = Path(__file__).with_name("criteria.yaml")
KEEP = "MANTENER"     # anything but DESCARTAR keeps a strategy (sqx/curate/README.md)
# A functional test of the chain (`run --smoke`, Test_ projects only): only the rules that say a
# strategy can be read at all are kept, so the medoid cut always has someone to keep (🔬 2026-10-04,
# 1,000 built, 0 alive at step 8: the run ended there and tested nothing after it).
SMOKE = "ALGO_SMOKE"
SMOKE_MARK = "smoke"     # an empty file in the run's folder: the run judged in smoke mode
READABLE = {"gate.scorecard." + fact for fact in (     # the gate's level 0
    "presencia_passed", "sanidad_passed", "sanidad_value", "estaticas_value",
    "is_trades_per_year")}


def settings() -> dict:
    """criteria.yaml, parsed."""
    cfg = yaml.load(CRITERIA.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    if os.environ.get(SMOKE) == "1":
        for step in cfg["steps"].values():
            step["rules"] = [r for r in step.get("rules") or [] if r.get("fact") in READABLE]
    return cfg


def smoke(project: str, on: bool) -> None:
    """Turn the smoke mode on (`--smoke`) for this run and its subprocesses; Test_ only."""
    if not on:
        return
    if not project.startswith("Test_"):
        sys.exit("--smoke es solo para proyectos Test_: en los demás juzgan todas las reglas")
    os.environ[SMOKE] = "1"


def tags(project: str) -> set[str]:
    """What a rule's `by` may name for this project: its timeframe, its symbol and the asset's
    class (`forex`, `no_forex`), from the project registry; empty for an unregistered one."""
    row = next((r for r in reversed(registry.rows()) if r["name"] == project), None)
    if row is None or row["symbol"] not in assetdata.symbols():
        return {row["timeframe"]} if row else set()
    return {row["timeframe"], row["symbol"], assetdata.load(row["symbol"])["class"]}


def population(project: str, bank: str, role: str) -> pd.DataFrame:
    """The databank being cut, one row per file: `strategy` (its name) and `identity`."""
    files = by_identity(databank_dir(project, bank, apply_verdict.install_of(role)))
    return pd.DataFrame([{"strategy": f.stem, "identity": i}
                         for i, fs in files.items() for f in fs])


def per_cell(rules: list[dict], project: str) -> tuple[list[dict], dict]:
    """The rules with each per-cell line (`alpha:`) computed from B, and what to sign in the ledger.

    Returns:
        (rules, `thresholds`): `{"batches_screened": B, "alpha": ..., "z_min": ...}` for the
        first per-cell rule, `{}` when the step has none (B is not even read then).
    """
    mine = criteria.per_cell(rules)
    if not mine:
        return rules, {}
    b = cells.batches_for(project)
    return criteria.thresholded(rules, b), {"batches_screened": b, "alpha": mine[0]["alpha"],
                                            "z_min": criteria.threshold(mine[0]["alpha"], b)}


def ledger_row(project: str, n: str, spec: dict, before: int, after: int, segment: str | None = None,
               thresholds: dict | None = None) -> None:
    """Sign this cut in the ledger: one row, with the sha256 of criteria.yaml (OPEN 1.3 item 2).

    `segment:` of the step in criteria.yaml declares what the cut read; oos1 when it does not (steps 8, 10, 11.5, 12, 14, 16 and 20 declare it; others default to oos1)
    (a question for the owner: only step 8 declares it). `segment` overrides it (18.5's second
    judgement, read with oos2).
    """
    who = survivors.about(project)
    sid = studymod.study_id(who["symbol"], who["timeframe"], who["family"])
    record.log(sid, {"step": float(n), "launched_by": "autopilot", "symbol": who["symbol"],
                     "timeframe": who["timeframe"], "segment": segment or spec.get("segment", "oos1"),
                     "n_in": before, "n_out": after, "criterion": f"criteria.yaml paso {n}",
                     "config_hash": hashlib.sha256(CRITERIA.read_bytes()).hexdigest(),
                     "thresholds": thresholds or None})


def _full_harvest(project: str) -> set[str] | None:
    """Identities of the newest `Results` harvest on disk; None when there is none."""
    path = state.newest(harvest_dir(project, trim.BANK, "x").parent, "metrics.parquet")
    return None if path is None else set(pd.read_parquet(path, columns=[]).index)


def _seal(project: str) -> Callable[[], None]:
    """Remember which `Results` exports are fresh; the returned call signs them fresh again after the trim.

    The pre-trim export is the whole build (`studies/research/memory/sheet.py` reads it); without
    this the next stop sees the cut files as newer and rewrites it with the survivors alone.
    """
    bank = trim.BANK
    fresh = [k for k, v in state.status(project, bank).get("pieces", {}).items() if v["state"] == "fresh"]

    def resign() -> None:
        """Write the `.sources.sig` of each export that was fresh, over the files as the cut left them."""
        top = find.install_of(project, bank)[1]
        own = find.files(top, project, bank)
        other = find.partner(top, project, bank)
        marks = {"metrics": (metrics_export(project, bank) / "manifest.json", own),
                 "trades": (state.newest(export_dir(project, bank, "x").parent, "manifest.json"), own),
                 "harvest": (state.newest(harvest_dir(project, bank, "x").parent, "manifest.json"),
                             own + (find.files(top, project, other) if other else []))}
        for piece in fresh:
            done, sources = marks[piece]
            (done.parent / f"{done.name}.sources.sig").write_text(fingerprint(sources))
    return resign


def trades_fresh(project: str, bank: str) -> bool:
    """Whether the bank's trade export matches its files now (`aftercut.refilter` needs it before a cut)."""
    return state.status(project, bank).get("pieces", {}).get("trades", {}).get("state") == "fresh"


def judge(project: str, n: str, role: str, out: Path, cfg: dict, segment: str | None = None) -> dict:
    """Judge step `n` and apply its verdict, worker stopped.

    Args:
        project: Project name.
        n: The judging step, e.g. "8".
        role: The worker holding the project.
        out: This step's folder in the run: hechos.parquet and verdict.csv land here.
        cfg: `settings()`.
        segment: Ledger segment overriding the step's own `segment:`; None keeps it.

    Returns:
        `n`, `hechos` (rows gathered), `corte` (what was done, one line), and when a verdict
        was written `before`, `after`, `limbo`, `seed`. A step with neither rules nor medoids
        writes its facts and cuts nothing.
    """
    out.mkdir(parents=True, exist_ok=True)
    found = facts.gather(project, n)
    found.to_parquet(out / "hechos.parquet")
    spec = cfg["steps"].get(n, {})
    rules, signed = per_cell(criteria.resolved(spec.get("rules") or [], tags(project)), project)
    if not rules and not spec.get("medoids"):
        return {"n": n, "hechos": len(found), "corte": "ninguno: el paso no tiene criterio"}
    if "cut" not in spec:
        sys.exit(f"paso {n}: tiene reglas y criteria.yaml no dice qué databank cortar (`cut`)")
    note = spec["cut"] is None       # `cut: null`: judged and written, nothing deleted (step 17)
    bank = survivors.bank(cfg, n) if note else spec["cut"]
    pop = population(project, bank, role)
    if pop.empty:                    # nothing to judge: zero survivors, which `run` ends cleanly
        return {"n": n, "hechos": len(found), "before": 0, "after": 0, "limbo": [], "seed": None,
                "corte": f"{bank}: vacío, nada que juzgar"}
    pop["who"], found["who"] = selection.resolve(pop, found)
    # A scaled sibling is a measuring device of step 11, never a candidate: it always goes,
    # and only its mother, on her own timeframe and unscaled, is judged (owner, 2026-10-01).
    sibling = pop["strategy"].map(lambda name: bool(SIBLING.search(name)))
    mothers = sorted(set(pop.loc[~sibling, "who"]))
    judged = criteria.outcomes(found[found["who"].isin(mothers)], mothers, rules)
    if "gate" in facts.BY_N[n]["studies"]:
        judged |= {w: ("fail", why) for w, why in selection.fallen(project, pop).items()
                   if w in judged and judged[w][0] == "fail"}
    judged |= selection.siblings(pop, sibling, judged, spec.get("siblings") == "follow")
    alive = sorted({w for w, (state, _) in judged.items() if state != "fail"})
    keep = set(alive)
    if spec.get("medoids") and not note:
        keep &= selection.medoids(project, pop, spec["medoids"])
    pop["outcome"] = [judged[w][0] for w in pop["who"]]
    pop["reason"] = [judged[w][1] or ("no es la medoide de su grupo" if w not in keep else "")
                     for w in pop["who"]]
    pop["verdict"] = [KEEP if note or w in keep else apply_verdict.DROP for w in pop["who"]]
    csv = out / "verdict.csv"
    pop[["strategy", "verdict", "identity", "outcome", "reason"]].to_csv(csv, index=False)
    drops = int((pop["verdict"] == apply_verdict.DROP).sum())
    fresh = trades_fresh(project, bank) if drops else False
    cut = apply_verdict.apply(project, bank, csv, role, **({"trades_fresh": True} if fresh else {})) if drops else \
        {"before": len(pop), "after": len(pop)}
    if fresh:
        trades_fresh(project, bank)      # seen fresh once more: the loader signs it (`state.age`)
    ledger_row(project, n, spec, cut["before"], cut["after"], segment, signed)
    if n == "8":                     # the per-cell counter: this batch was screened on oos1
        cells.note(project, len(pop))
        cut["results"] = trim.results(project, role, pop, population(project, trim.BANK, role), out,
                                    lambda: _full_harvest(project), lambda: _seal(project))      # save first, then cut `Results`
    kept = (pop["outcome"] == "limbo") & (pop["verdict"] != apply_verdict.DROP) & ~sibling
    limbo = sorted(pop.loc[kept, "strategy"])
    how = "medoides" if len(keep) < len(alive) else "criterios"
    return {"n": n, "hechos": len(found), "before": cut["before"], "after": cut["after"],
            "limbo": limbo, "seed": None,
            "corte": f"{bank}: {cut['before']} → {cut['after']} por {how}" + (" (anota, no corta)" if note else "")
                     + (f", {len(limbo)} en limbo" if limbo else "") + (f"; {cut['results']}" if "results" in cut else "")}
