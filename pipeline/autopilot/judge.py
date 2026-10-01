"""One judging step: its facts, the criteria, the dev draw, the verdict.csv and the cut in SQX."""

import random
import sys
from pathlib import Path

import pandas as pd
import yaml

from core.paths import databank_dir
from pipeline.autopilot import criteria, facts
from sqx.curate import apply_verdict
from sqx.projects.crosstfload import SIBLING
from ui.daemon.advance.preflight import by_identity

CRITERIA = Path(__file__).with_name("criteria.yaml")
KEEP = "MANTENER"     # anything but DESCARTAR keeps a strategy (sqx/curate/README.md)


def settings() -> dict:
    """criteria.yaml, parsed. YAML 1.1 reads the key `on:` of `dev` as the boolean True, so it is
    put back under "on" (🔬 2026-10-01: KeyError 'on' at the first judge ever run)."""
    cfg = yaml.safe_load(CRITERIA.read_text(encoding="utf-8"))
    dev = cfg.get("dev") or {}
    if True in dev:
        dev["on"] = dev.pop(True)
    return cfg


def population(project: str, bank: str, role: str) -> pd.DataFrame:
    """The databank being cut, one row per file: `strategy` (its name) and `identity`."""
    files = by_identity(databank_dir(project, bank, apply_verdict.install_of(role)))
    return pd.DataFrame([{"strategy": f.stem, "identity": i}
                         for i, fs in files.items() for f in fs])


def judge(project: str, n: str, role: str, out: Path, cfg: dict) -> dict:
    """Judge step `n` and apply its verdict, worker stopped.

    Args:
        project: Project name.
        n: The judging step, e.g. "8".
        role: The worker holding the project.
        out: This step's folder in the run: hechos.parquet and verdict.csv land here.
        cfg: `settings()`.

    Returns:
        `n`, `hechos` (rows gathered), `corte` (what was done, one line), and when a verdict
        was written `before`, `after`, `limbo`, `seed`. A step with neither rules nor a dev
        draw writes its facts and cuts nothing.
    """
    out.mkdir(parents=True, exist_ok=True)
    found = facts.gather(project, n)
    found.to_parquet(out / "hechos.parquet")
    spec, dev = cfg["steps"].get(n, {}), cfg["dev"]
    rules = spec.get("rules") or []
    sample = dev["sample"] if dev["on"] and n in dev["at"] else None
    if not rules and sample is None:
        return {"n": n, "hechos": len(found), "corte": "ninguno: el paso no tiene criterio"}
    if "cut" not in spec:
        sys.exit(f"paso {n}: tiene reglas y criteria.yaml no dice qué databank cortar (`cut`)")
    pop = population(project, spec["cut"], role)
    ids = set(found["identity"]) - {""}
    pop["who"] = [i if i in ids else s for s, i in zip(pop["strategy"], pop["identity"])]
    # A scaled sibling is a measuring device of step 11, never a candidate: it always goes,
    # and only its mother, on her own timeframe and unscaled, is judged (owner, 2026-10-01).
    sibling = pop["strategy"].map(lambda name: bool(SIBLING.search(name)))
    found["who"] = found["identity"].where(found["identity"] != "", found["strategy"])
    mothers = sorted(set(pop.loc[~sibling, "who"]))
    judged = criteria.outcomes(found[found["who"].isin(mothers)], mothers, rules)
    judged |= {w: ("fail", "hermana escalada: solo sigue la madre") for w in pop.loc[sibling, "who"]}
    alive = sorted({w for w, (state, _) in judged.items() if state != "fail"})
    seed = dev["seed"] if dev["seed"] is not None else random.randrange(2**32)
    keep = set(random.Random(seed).sample(alive, min(sample, len(alive))) if sample else alive)
    pop["outcome"] = [judged[w][0] for w in pop["who"]]
    pop["reason"] = [judged[w][1] or ("fuera del sorteo de desarrollo" if w not in keep else "")
                     for w in pop["who"]]
    pop["verdict"] = [KEEP if w in keep else apply_verdict.DROP for w in pop["who"]]
    csv = out / "verdict.csv"
    pop[["strategy", "verdict", "identity", "outcome", "reason"]].to_csv(csv, index=False)
    drops = int((pop["verdict"] == apply_verdict.DROP).sum())
    cut = apply_verdict.apply(project, spec["cut"], csv, role) if drops else \
        {"before": len(pop), "after": len(pop)}
    limbo = sorted(pop.loc[(pop["outcome"] == "limbo") & (pop["verdict"] != apply_verdict.DROP),
                           "strategy"])
    how = f"sorteo de {sample} (semilla {seed})" if sample else "criterios"
    return {"n": n, "hechos": len(found), "before": cut["before"], "after": cut["after"],
            "limbo": limbo, "seed": seed if sample else None,
            "corte": f"{spec['cut']}: {cut['before']} → {cut['after']} por {how}"
                     + (f", {len(limbo)} en limbo" if limbo else "")}
