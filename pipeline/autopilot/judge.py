"""One judging step: its facts, the criteria, the medoid cut, the verdict.csv and the cut in SQX."""

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

from core import assetdata
from core.paths import databank_dir
from ledger import record, study as studymod
from pipeline.autopilot import criteria, facts, survivors
from sqx.curate import apply_verdict
from sqx.projects import registry
from sqx.projects.crosstfload import SIBLING
from ui.daemon.advance.preflight import by_identity

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


def resolve(pop: pd.DataFrame, found: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """The key each file of the cut databank and each fact is judged under: the one lookup.

    Args:
        pop: The databank being cut: `strategy` (file name) and `identity`, one row per file.
        found: The facts: `strategy` and `identity` ("" when a study files by name only).

    Returns:
        (`who` of every row of `pop`, `who` of every row of `found`). A file is its identity
        when any fact carries it, else its name; a fact is its identity, or its strategy name
        when it has none. A fact filed under an identity the cut databank does NOT hold — the
        gate, spread and edgeCost key by the BUILD's, which a retest can change (🔬 2026-10-06:
        1,557 of 10,000 failed presence for it, 29 of them alive on their own numbers) — is the
        file of the same name: a name is unique inside one databank. A fact without identity
        keeps its key, so nothing moves for a strategy whose identity held.
    """
    ids = set(found["identity"]) - {""}
    who = pd.Series([i if i in ids else s for s, i in zip(pop["strategy"], pop["identity"])],
                    index=pop.index, dtype=object)
    theirs = found["identity"].where(found["identity"] != "", found["strategy"])
    named = found["strategy"].map(dict(zip(pop["strategy"], who)))
    held = found["identity"].isin(set(pop["identity"]) | {""})
    return who, theirs.where(held | named.isna(), named)


def fallen(project: str, pop: pd.DataFrame) -> dict[str, str]:
    """Why the gate's cascade dropped each strategy it dropped: `who` → its first failed rule.

    The gate stops computing at a strategy's first Fail, so every rule of a later level reads
    «sin dato» for it: the reason is the one rule the scorecard names (`cayo_nivel`,
    `cayo_regla`), which is text and so not among the facts.
    """
    found = [r for r in facts.sources.results(project, "gate", None) if r["path"].is_dir()]
    if not found:
        return {}
    card = pd.read_parquet(found[0]["path"] / "scorecard.parquet").reset_index()
    if "cayo_regla" not in card:        # a scorecard written before the gate ran by levels
        return {}
    card = card[card["strategy"].notna() & card["cayo_regla"].notna()]
    _, who = resolve(pop, card)
    return {w: f"fail: {rule} (nivel {level})"
            for w, level, rule in zip(who, card["cayo_nivel"], card["cayo_regla"])}


def largest(card: pd.DataFrame, top: int) -> pd.DataFrame:
    """The scorecard rows of the medoids of the `top` largest groups: size (`redundancia_value`,
    counted among the same survivors) descending, tie by `redundancia_grupo` ascending."""
    mine = card[card["medoide"].fillna(False).astype(bool)]
    return mine.sort_values(["redundancia_value", "redundancia_grupo"],
                            ascending=[False, True]).head(top)


def medoids(project: str, pop: pd.DataFrame, top: int) -> set[str]:
    """`who` of the medoids of the `top` largest groups the gate marked in its scorecard."""
    found = [r for r in facts.sources.results(project, "gate", None) if r["path"].is_dir()]
    card = pd.read_parquet(found[0]["path"] / "scorecard.parquet").reset_index() if found else None
    if card is None or "medoide" not in card:
        sys.exit("paso con `medoids`: el scorecard de la puerta no trae la columna `medoide`")
    _, who = resolve(pop, largest(card[card["strategy"].notna()], top))
    return set(who)


def siblings(pop: pd.DataFrame, is_sibling: pd.Series, judged: dict, follow: bool) -> dict:
    """What happens to the scaled siblings of the databank being cut.

    Args:
        pop: The databank being cut, with `strategy` and `who`.
        is_sibling: Which rows of `pop` are scaled siblings.
        judged: The mothers' outcomes, `who` → (state, why).
        follow: `siblings: follow` in the step's criteria — step 11.5, whose databank feeds
            11.7 and still needs them: a sibling leaves only with its mother. Otherwise (step
            12, as always) every sibling goes: only the mother is a candidate.

    Returns:
        `who` of every sibling → (state, why).
    """
    mine = pop[is_sibling]
    if not follow:
        return {w: ("fail", "hermana escalada: solo sigue la madre") for w in mine["who"]}
    by_name = dict(zip(pop["strategy"], pop["who"]))
    return {w: judged.get(by_name.get(SIBLING.sub("", name)),
                          ("fail", "hermana sin su madre en el databank"))
            for name, w in zip(mine["strategy"], mine["who"])}


def ledger_row(project: str, n: str, spec: dict, before: int, after: int, segment: str | None = None) -> None:
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
                     "config_hash": hashlib.sha256(CRITERIA.read_bytes()).hexdigest()})


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
    rules = criteria.resolved(spec.get("rules") or [], tags(project))
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
    pop["who"], found["who"] = resolve(pop, found)
    # A scaled sibling is a measuring device of step 11, never a candidate: it always goes,
    # and only its mother, on her own timeframe and unscaled, is judged (owner, 2026-10-01).
    sibling = pop["strategy"].map(lambda name: bool(SIBLING.search(name)))
    mothers = sorted(set(pop.loc[~sibling, "who"]))
    judged = criteria.outcomes(found[found["who"].isin(mothers)], mothers, rules)
    if "gate" in facts.BY_N[n]["studies"]:
        judged |= {w: ("fail", why) for w, why in fallen(project, pop).items()
                   if w in judged and judged[w][0] == "fail"}
    judged |= siblings(pop, sibling, judged, spec.get("siblings") == "follow")
    alive = sorted({w for w, (state, _) in judged.items() if state != "fail"})
    keep = set(alive)
    if spec.get("medoids") and not note:
        keep &= medoids(project, pop, spec["medoids"])
    pop["outcome"] = [judged[w][0] for w in pop["who"]]
    pop["reason"] = [judged[w][1] or ("no es la medoide de su grupo" if w not in keep else "")
                     for w in pop["who"]]
    pop["verdict"] = [KEEP if note or w in keep else apply_verdict.DROP for w in pop["who"]]
    csv = out / "verdict.csv"
    pop[["strategy", "verdict", "identity", "outcome", "reason"]].to_csv(csv, index=False)
    drops = int((pop["verdict"] == apply_verdict.DROP).sum())
    cut = apply_verdict.apply(project, bank, csv, role) if drops else \
        {"before": len(pop), "after": len(pop)}
    ledger_row(project, n, spec, cut["before"], cut["after"], segment)
    kept = (pop["outcome"] == "limbo") & (pop["verdict"] != apply_verdict.DROP) & ~sibling
    limbo = sorted(pop.loc[kept, "strategy"])
    how = "medoides" if len(keep) < len(alive) else "criterios"
    return {"n": n, "hechos": len(found), "before": cut["before"], "after": cut["after"],
            "limbo": limbo, "seed": None,
            "corte": f"{bank}: {cut['before']} → {cut['after']} por {how}" + (" (anota, no corta)" if note else "")
                     + (f", {len(limbo)} en limbo" if limbo else "")}
