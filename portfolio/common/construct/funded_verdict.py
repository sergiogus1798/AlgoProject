"""The funded verdict (F4, Q11 d): stage B's winner on oos1 against the selected null, then oos2 once."""

import numpy as np
import pandas as pd

from . import oos2 as oos2_mod, segment
from .equity import matrix
from .inputs import pool as pool_mod
from .pairs import table as pairs_table
from .search import stageb, stageb_data, stageb_run, trials
from .verdict import decide, hold, null as null_mod

JUDGE = ("oos1", "oos2")


def prepare(world: dict, members: list[str], span: tuple, cfg: dict) -> dict:
    """`stageb_data.prepare` for some members of the world on one stretch of server days."""
    return stageb_data.prepare({m: world["sources"][m] for m in members}, world["bars"],
                               world["universe"]["days"][world["firm"]],
                               cfg["equity"]["firm_clocks"][world["firm"]], span, world["factors"],
                               world["min_size"], cfg)


def union(frames: list[pd.DataFrame]) -> list[str]:
    """Every identity some combination of the frames holds."""
    return sorted({m for f in frames for members in f["members"] for m in members.split("+")})


def segments(world: dict) -> list[str]:
    """The judging segments the firm's day table has days in, in judging order."""
    table = world["universe"]["days"][world["firm"]]
    return [s for s in JUDGE if s in world["calendar"]
            and table["day"].between(*world["calendar"][s]).any()]


def judge(world: dict, cfg: dict, rng: np.random.Generator, stage_b: dict, n_shortlist: int,
          null_winners: list[dict], n_candidates: int) -> dict:
    """The winner and each null search's winner on oos1; oos2 only if the winner passed there.

    oos1 and oos2 are judged separately and in that order (Council 2026-10-04, `DECISIONS.md`
    #11): on oos1 the measure named by `verdict.pass_measure` against its percentile in the
    null; on oos2 the chosen portfolio's deflated Sharpe, one read per pool (`oos2.read`).
    Each segment opened is asked of the one-way door first and leaves a ledger row.

    Args:
        world: `funded_b.load()`'s; `pool` (the declared pool) is read from disk when absent.
        stage_b: `stageb_run.run()` on the real shortlist, its `winner` with `p_fresh`.
        n_shortlist: Combinations in that shortlist.
        null_winners: Each null search's stage-B winner.
        n_candidates: Combinations each null search drew.

    Returns:
        `judged` (`stageb_run.judged()` of the winner on oos1), `nulls` (each null winner's
        members and measures there) and `verdict` (`verdict.decide.verdict()`).
    """
    plan, calendar, winner = world["plan"], world["calendar"], stage_b["winner"]
    chosen = winner["members"].split("+")
    meta = {m: world["meta"][m] for m in chosen}
    pool = world.get("pool") or pool_mod.declared(world["pool_name"], world["base"])
    criterion = f"portfolio/funded_verdict/{plan['plan_key']}"
    note = f"relaxed={cfg.get('relaxed') or 'no'}"
    risk = stageb_run.risk_of(winner, plan)

    trials.admit(meta, ["oos1"])
    later = prepare(world, union([pd.DataFrame([winner, *null_winners])]), calendar["oos1"], cfg)
    judged = stageb_run.judged(later, winner["members"], plan, cfg, risk, rng)
    nulls = []
    for w in null_winners:
        got = stageb_run.judged(later, w["members"], plan, cfg, stageb_run.risk_of(w, plan), rng)
        nulls.append({"members": w["members"], "selector_p": w["p"],
                      **{k: got[k] for k in decide.MEASURES}})
    same = sum(n["members"] == winner["members"] for n in nulls)
    first = decide.funded_oos1(null_mod.read({k: judged[k] for k in decide.MEASURES}, nulls), same, cfg)
    passed = {"pass": True, "fail": False}.get(first["state"])
    trials.record_look(pool, meta, "oos1", criterion, "funded_b", passed,
                       f"{first['state']}: nulo seleccionado de {len(nulls)} busquedas x "
                       f"{n_candidates} combinaciones, {same} eligieron la misma; {note}")

    ids = world["identities"]
    daily = world["universe"]["daily"][ids]
    second = decide.UNOPENED
    if passed and "oos2" not in segments(world):
        second = {"state": "not_opened", "reason": "el pool no tiene días en oos2"}
    elif passed:
        scale = np.array([world["factors"][i] for i in ids])
        second = oos2_mod.read(
            lambda: segment.paths(daily, calendar, scale, np.isin(ids, chosen)[None, :], cfg, "oos2")[0][0],
            chosen, pool, meta, criterion, "funded_b", note)
    opened = ["oos1"] + ["oos2"] * (second["state"] in ("pass", "fail"))
    read = pd.concat([matrix.segment(daily[chosen], calendar, s) for s in opened])
    held = hold.held(pairs_table.table(read, matrix.monthly(read), cfg) if len(chosen) > 1
                     else pd.DataFrame(), chosen, cfg)
    cost = {"n_pool": len(ids), "n_stage_a": len(world["search"]), "n_shortlist": n_shortlist,
            "n_settings": stage_b["n_settings"], "null_draws": len(nulls),
            "null_candidates": n_candidates, "segments": opened}
    return {"judged": judged, "nulls": nulls, "verdict": decide.verdict(
        {"members": chosen, "build_p": winner["p_fresh"], "selector_p": winner["p"],
         "risk": dict(zip(stageb.judge.stage_names(plan), risk[0].tolist()))},
        first, second, held, cost)}
