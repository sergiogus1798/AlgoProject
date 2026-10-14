"""Encargo 33 §4 as data: per plan and re-buy policy the best risk per phase at the deciding haircut, the monkey, the curve EV(h), and each add-on set's ΔEV."""

import itertools
from collections.abc import Callable
from typing import TypedDict, cast

import numpy as np

from portfolio.funded.rules import catalog
from portfolio.funded.sim import bank, haircut, measures, plans
from portfolio.funded.sim.plans import Cash, Terms


class Built(TypedDict):
    """The bank searched: one row per chosen plan variant and policy, the add-on table and every configuration tried."""

    rows: list[dict]
    addons: list[dict]
    search: list[dict]


def variants(cfg: dict) -> tuple[list[Terms], list[str], dict[str, list[str]]]:
    """Every plan of the universe with every add-on set the simulation can tell apart.

    Returns:
        `(plans, gaps, skipped)`: `plans.terms()` dicts, the bare plan before its add-on sets;
        one Spanish line per catalogue gap nobody filled (then `plans` is incomplete); and per
        plan the add-on sets left out because nothing the simulation reads changes with them.
    """
    out, gaps, skipped = [], {}, {}
    for key in catalog.plans(cfg["universe"]["max_size"], cfg["universe"]["ccy"]):
        sets, skipped[key] = plans.addon_sets(key, cfg["addons"]["max_set"])
        for options in sets:
            try:
                out.append(plans.terms(key, options, cfg["gaps"]))
            except plans.Gap as gap:
                gaps.update(
                    {key: f"gaps.{key} — {what}" for key, what in gap.missing.items()}
                )
    return out, list(gaps.values()), skipped


def _multipliers(
    plan: Terms, risk: dict[str, float], unit_risk: float
) -> dict[str, float]:
    """Risk fractions of the initial balance as the multipliers of a unit-risk path."""
    return {stage: r * plan["size"] / unit_risk for stage, r in risk.items()}


def build(
    paths: dict[str, np.ndarray],
    zero: dict[str, np.ndarray],
    meta: dict,
    cfg: dict,
    variants_: list[Terms],
    hazards: tuple[np.ndarray, np.ndarray],
    progress: Callable[[int, str], None] = lambda percent, state: None,
) -> Built:
    """Search the risk per phase of every plan variant under every re-buy policy, then read the chosen ones in full.

    Args:
        paths: The portfolio's path set, unit risk (`inputs.paths`).
        zero: The monkey's path set, same shape.
        meta: `unit_risk`, `days_per_year` of the path set.
        cfg: The config, owner inputs complete.
        variants_: `variants()`'s plans.
        hazards: `bank.hazards()`'s `(close_day, deny)`, shared by every configuration.
        progress: Called with a percentage and a Spanish state.

    Returns:
        `rows` (one per bare plan × policy of `owner.rebuy`, ordered by EV at the deciding
        haircut, best first), `addons` (one per add-on set × policy: its EV at its own best risk
        and `delta_ev` against the bare plan under the same policy — already net of the add-on's
        price, which the bank pays at every purchase) and `search` (every configuration scored:
        plan, options, rebuy, risk per phase, `ev` — the policy is a searched dimension).
    """
    owner, dpy = cfg["owner"], meta["days_per_year"]
    horizon = paths["closed"].shape[1]
    hs, decides = owner["haircuts"], owner["haircut_decides"]
    cut = {h: haircut.apply(paths, h) for h in hs}

    def run(data: dict, plan: Terms, risk: dict, cash: Cash) -> np.ndarray:
        """One configuration's draws."""
        return bank.simulate(
            data,
            plan,
            _multipliers(plan, risk, meta["unit_risk"]),
            cash,
            *hazards,
            threads=cfg["compute"]["threads"],
        )[0]

    search, rows, addons, base_ev = [], [], [], {}
    cells: list[tuple[Terms, str]] = list(
        itertools.product(variants_, cast(list[str], owner["rebuy"]))
    )
    for i, (plan, rebuy) in enumerate(cells):
        progress(
            int(100 * i / len(cells)), f"{plan['plan_key']} {plan['options']} {rebuy}"
        )
        cash, key = plans.cash(plan, owner, dpy, rebuy), (plan["plan_key"], rebuy)
        grid = plans.risk_grid(plan, cfg["risk"]["challenge"], cfg["risk"]["funded"])
        outs = [run(cut[decides], plan, risk, cash) for risk in grid]
        evs = [measures.ev(out) for out in outs]
        search += [
            {
                "plan": plan["plan_key"],
                "options": plan["options"],
                "rebuy": rebuy,
                "ev": e,
                **{f"risk_{s}": r for s, r in risk.items()},
            }
            for risk, e in zip(grid, evs)
        ]
        best = int(np.argmax(evs))
        risk = grid[best]
        head = {
            "plan": plan["plan_key"],
            "options": plan["options"],
            "rebuy": rebuy,
            "price_usd": cash["price"],
            **{
                f"risk_{s}": risk.get(s)
                for s in ("phase1", "phase2", "phase3", "funded")
            },
        }
        if plan["options"]:
            addons.append(
                {**head, "ev": evs[best], "delta_ev": evs[best] - base_ev[key]}
            )
            continue
        base_ev[key] = evs[best]
        curve = [
            evs[best] if h == decides else measures.ev(run(cut[h], plan, risk, cash))
            for h in hs
        ]
        monkey = max(measures.ev(run(zero, plan, r, cash)) for r in grid)
        rows.append(
            {
                **head,
                **measures.summary(outs[best], horizon, dpy),
                "budget_usd": cash["budget"],
                "ev_monkey": monkey,
                "advantage": evs[best] - monkey,
                **{f"ev_h{round(100 * h)}": e for h, e in zip(hs, curve)},
                "breakeven_h": haircut.breakeven(hs, curve),
                "flags": ", ".join(f["rule_key"] for f in plan["flags"]),
            }
        )
    return {
        "rows": sorted(rows, key=lambda r: -r["ev"]),
        "addons": addons,
        "search": search,
    }
