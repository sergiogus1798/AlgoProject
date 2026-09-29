"""Turn one design brief into the list of tuples to fabricate. Pure maths; touches no file."""

import math

import numpy as np
import pandas as pd

from sqx.variants import tuples
from sqx.variants.design import canaries, levels, strata

ORDER = ["neighbourhood", "factorial", "coverage"]
CONTROLS = ("origin", "canary")
OVERDRAW = 2


def _context(name: str, design: dict, settings: dict, live: dict) -> dict:
    """Everything one stratum needs beyond its levels and its budget.

    Args:
        name: Which stratum.
        design: A parsed brief.
        settings: The `design` block of `config.yaml`.
        live: Levels of the live parameters.

    Returns:
        The context dict that stratum reads. They share one signature, so the extras go
        here rather than into three different argument lists.
    """
    return {"centre": levels.centre(design, live), "radius": settings["neighbourhood"]["radius"],
            "weights": levels.weights(design), "min_levels": settings["factorial"]["min_levels"],
            "seed": settings["seed"],
            # Per stratum and not per run: str.__hash__ is salted, so a seed built from the
            # name would give a different design on every interpreter.
            "rng": np.random.default_rng(settings["seed"] + ORDER.index(name))}


def build(design: dict, settings: dict, table: pd.DataFrame,
         banned: dict[str, set] | None = None) -> tuple[pd.DataFrame, dict]:
    """The whole batch: which tuples, in which stratum, under which identifier.

    Args:
        design: A parsed brief, contract C1.
        settings: The parsed `config.yaml`.
        table: Output of `inputs.known`, the source of the canary expectations.
        banned: `design.pilot.decide`'s first return value, or `None` when the pilot did
            not run. A live parameter's dropped levels are removed from what every stratum
            samples from -- never the whole parameter, and never applied if it would leave
            fewer than two levels, which mirrors `pilot.decide`'s own floor so the two
            never disagree about how much of a parameter survives.

    Returns:
        The plan and a report of how it was filled. `report["pilot_dropped"]` names every
        level actually removed by `banned`, so a batch fabricated after the pilot always
        says in its own manifest what changed and why -- never a silent difference from one
        fabricated without it.

        `n_target` is a **cap, never a quota**. A tuple is never repeated to reach it: the
        controls go in first and count against the target, then each stratum takes its
        share of what is left, and a stratum that cannot fill its share hands the
        remainder to the next one. When the
        whole design space is smaller than the target the factory builds all of it and the
        report says so, which is the honest answer and also the common one -- the brief for
        `Strategy 17.9.39` spans 3,888 live tuples against a target of 5,000.

        Deduplication is over the tuple, across strata and controls alike, and the first
        stratum to produce a tuple keeps it. Two identical `.sqx` in one databank are one
        strategy after SQX is done with them, so a duplicate is not a wasted slot, it is a
        row of the manifest with no file behind it.
    """
    live = levels.live(design, settings["minimum"])
    origin_values = levels.origin(design)
    pilot_dropped = {}
    for name, bad in (banned or {}).items():
        if name not in live:
            continue
        # The origin tuple is already proven to trade -- the pilot never gets to remove it,
        # whatever region its own value happened to sample into.
        bad = bad - {origin_values.get(name)}
        kept = [v for v in live[name] if v not in bad]
        if len(kept) < 2:
            continue
        removed = sorted(set(live[name]) - set(kept))
        if removed:
            pilot_dropped[name] = removed
            live[name] = kept
    fixed = levels.frozen(design, settings["design"]["frozen"])
    everything = {**live, **fixed}
    origin = origin_values
    frozen_values = {f["name"]: float(f["value"]) for f in design["frozen"]}

    rows, seen = [], set()
    for control in canaries.rows(design, everything, origin, table, settings["canaries"]):
        digest = tuples.tuple_hash(control["values"])
        if digest in seen:
            continue
        seen.add(digest)
        rows.append({**control, "tuple_hash": digest})

    report = {"controls": len(rows), "live_space": math.prod(len(v) for v in live.values()),
              "full_space": math.prod(len(v) for v in everything.values()), "strata": {}}
    carry, room = 0, design["n_target"] - len(rows)
    for name in ORDER:
        budget = int(round(design["strata"][name] * room)) + carry
        pool = everything if name == "coverage" else live
        asked = budget * OVERDRAW if name == "coverage" else budget
        kept = 0
        for values in strata.STRATA[name](pool, asked, _context(name, design, settings["design"], live)):
            if kept == budget:
                break
            complete = values if name == "coverage" else {**values, **frozen_values}
            digest = tuples.tuple_hash(complete)
            if digest in seen:
                continue
            seen.add(digest)
            kept += 1
            rows.append({"values": complete, "stratum": name, "origin": False,
                         "expect_netprofit": None, "expect_trades": None,
                         "expect_same_as": None, "tuple_hash": digest})
        report["strata"][name] = {"budget": budget, "kept": kept}
        carry = budget - kept

    report["n"] = len(rows)
    report["shortfall"] = design["n_target"] - len(rows)
    report["pilot_dropped"] = pilot_dropped
    return _frame(rows), report


def _frame(rows: list[dict]) -> pd.DataFrame:
    """The plan as a table, identifiers assigned.

    Args:
        rows: Controls first, then one entry per sampled tuple.

    Returns:
        Contract C2 minus the columns only the disk can answer -- `sqx_name` is what SQX
        gives the file back as, and the manifest reads it off the file rather than
        predicting it. `P00000` is the origin, because the order here is the order the
        controls were built in and the origin is always first.
    """
    ids = [f"P{i:05d}" for i in range(len(rows))]
    origin_id = next(i for i, r in zip(ids, rows) if r["origin"])
    frame = pd.DataFrame([{
        "variant_id": vid, "stratum": row["stratum"], "origin": row["origin"],
        **tuples.columns(row["values"]), "tuple_hash": row["tuple_hash"],
        "canary_expect_netprofit": row["expect_netprofit"],
        "canary_expect_trades": row["expect_trades"],
        "canary_expect_same_as": origin_id if row["expect_same_as"] else None}
        for vid, row in zip(ids, rows)])
    frame["canary_expect_trades"] = frame["canary_expect_trades"].astype("Int64")
    return frame


def spread(table: pd.DataFrame, n: int) -> pd.DataFrame:
    """N rows taken across the whole plan rather than off the top of it.

    Args:
        table: What `build` returned, controls first.
        n: How many rows to keep.

    Returns:
        Every control, then evenly spaced picks from what is left.

        `head(n)` is the wrong sample for a small batch and it is wrong in a way that looks
        right: the plan is ordered controls-first and then stratum by stratum, so the first
        eleven rows are five controls plus a dense neighbourhood cluster one level step
        apart. Retested, most of those return the same number, and a correlation over them
        measures the clustering rather than the surface. Spacing the picks is what makes a
        small batch a miniature of the design instead of a corner of it.
    """
    controls = table[table["stratum"].isin(CONTROLS)]
    rest = table[~table["stratum"].isin(CONTROLS)]
    room = n - len(controls)
    if room <= 0:
        return controls.head(n)
    step = max(1, len(rest) // room)
    return pd.concat([controls, rest.iloc[::step].head(room)], ignore_index=True)
