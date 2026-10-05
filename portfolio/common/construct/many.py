"""The real path's verdict on a chosen portfolio (M5): oos1 against random portfolios, then oos2 once."""

import time

import numpy as np
import pandas as pd

from . import oos2 as oos2_mod, segment
from .contract import tabs
from .equity import matrix
from .pairs import table as pairs_table
from .search import objective, random_k, trials
from .verdict import decide, decide_real, hold, null

CRITERION = "portfolio/verdict/random_k"


def mask(inputs: dict) -> np.ndarray:
    """The chosen portfolio as a bool [1, N] row over the run's identities."""
    return np.isin(inputs["result"]["identities"], inputs["members"])[None, :]


def oos1(inputs: dict, cfg: dict, rng: np.random.Generator) -> dict:
    """The chosen portfolio's rank score on oos1 among random admissible ones of its size (R6).

    The figure is the search's own: each metric at its worst over the shifted starts, the
    four signed ranks taken once -- here within the draws plus the chosen one.

    Returns:
        `null.bar()`'s dict plus `k`, `n_space`, `n_distinct`, `metrics` (the chosen one's
        four), `sharpe`, `span` and `scores` (every draw's, for the picture).
    """
    r, chosen = inputs["result"], mask(inputs)
    drawn = random_k.draw(r["graph"]["graph"], int(chosen.sum()), cfg["real"]["null_draws"],
                          cfg["real"]["exhaustive_max"], rng)
    if not len(drawn["index"]):
        raise ValueError(f"la cartera elegida no es admisible: ninguna combinación de K={int(chosen.sum())} lo es")
    paths, dates = segment.paths(r["daily"], r["calendar"], r["scale"],
                                   np.vstack([drawn["members"], chosen]), cfg, "oos1")
    table = objective.worst(objective.shifted(paths, dates, cfg))
    index = np.append(drawn["index"], len(drawn["members"]))
    every = {name: values[index] for name, values in table.items()}
    scores = objective.rank_score(every, every)
    share = float((drawn["members"] == chosen).all(axis=1)[drawn["index"]].mean())
    return {**null.bar(scores[-1], scores[:-1], cfg["real"]["null_percentile"], share),
            "k": int(chosen.sum()), "n_space": drawn["n_space"], "n_distinct": len(drawn["members"]),
            "metrics": {name: float(table[name][-1]) for name in objective.metrics.NAMES},
            "sharpe": float(table["sharpe"][-1]), "scores": scores[:-1],
            "span": (str(dates[0].date()), str(dates[-1].date()))}


def held(inputs: dict, segments: list[str], cfg: dict) -> dict:
    """`hold.held()` of the chosen members over the segments the verdict opened."""
    r, members = inputs["result"], inputs["members"]
    if len(members) < 2:
        return hold.held(pd.DataFrame(), members, cfg)
    daily = pd.concat([matrix.segment(r["daily"][members], r["calendar"], s) for s in segments])
    return hold.held(pairs_table.table(daily, matrix.monthly(daily), cfg), members, cfg)


def judge(inputs: dict, cfg: dict, rng: np.random.Generator) -> dict:
    """oos1, then oos2 only if oos1 passed; a ledger row per segment opened (PLAN §6).

    Returns:
        `verdict.decide.verdict()`'s dict, or `{"pass": None, "label", "reason"}` when the
        pool has no day of oos1 to read.
    """
    r, members = inputs["result"], inputs["members"]
    meta = {m: r["members_meta"][m] for m in members}
    days = {s: len(matrix.segment(r["daily"].iloc[:, :0], r["calendar"], s))
            for s in ("oos1", "oos2") if s in r["calendar"]}
    if not days.get("oos1"):
        return {"pass": None, "label": "SIN VEREDICTO (el pool no tiene días en oos1)"}
    note = f"relaxed={cfg['relaxed'] or 'no'}"
    trials.admit(meta, ["oos1"])
    first = oos1(inputs, cfg, rng)
    passed = {"pass": True, "fail": False}.get(first["state"])
    trials.record_look(inputs["pool"], meta, "oos1", CRITERION, "report", passed,
                       f"{first['state']}: puntuacion {first['value']:.3f} vs p{first['quantile']:.0f} "
                       f"{first['bar']:.3f} de {first['n']} al azar de K={first['k']} "
                       f"({first['n_space']} distintas posibles); {note}")
    second = decide.UNOPENED
    if passed and not days.get("oos2"):
        second = {"state": "not_opened", "reason": "el pool no tiene días en oos2"}
    elif passed:
        second = oos2_mod.read(
            lambda: segment.paths(r["daily"], r["calendar"], r["scale"], mask(inputs), cfg, "oos2")[0][0],
            members, inputs["pool"], meta, CRITERION, "report", note)
    segments = ["oos1"] + ["oos2"] * (second["state"] in ("pass", "fail"))
    cost = {"n_pool": len(r["identities"]), "n_scored": len(inputs["table"]), "segments": segments}
    return decide.verdict({"members": members}, first, second, held(inputs, segments, cfg), cost)


def run(inputs: dict, cfg: dict, rng: np.random.Generator | None = None) -> dict:
    """A portfolio run judged and drawn: the population result of the contract.

    Args:
        inputs: `report.load()`'s dict -- `result` (`real.build()`'s), `members` (the chosen
            identities), `pool` (the declared pool), `table` (the run's `search.parquet`).
        cfg: The construct config.
        rng: Fresh entropy when None; its root is recorded.

    Returns:
        `verdict` (`judge()`'s), `sentence` (Spanish), `root_seed`, and `population` (the
        contract dict, `core.study.result.envelope`).
    """
    started = time.time()
    root_seed = int(np.random.default_rng().integers(0, 2**63 - 1))
    v = judge(inputs, cfg, rng or np.random.default_rng(root_seed))
    text = decide_real.sentence(v) if "oos1" in v else f"Veredicto: {v['label']}."
    return {"verdict": v, "sentence": text, "root_seed": None if rng else root_seed,
            "population": tabs.population(inputs, v, text, cfg, started)}
