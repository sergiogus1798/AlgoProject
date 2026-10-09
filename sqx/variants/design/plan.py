"""Turn one design brief into the list of tuples to fabricate. Pure maths; touches no file."""

import math

import pandas as pd

from sqx.variants import tuples
from sqx.variants.design import canaries, levels, lhs

CONTROLS = ("origin", "canary", "inert")


def size(live: int, cfg: dict) -> tuple[int, bool]:
    """How many variants a mother gets: `min(n_max, max(n_min, per_coefficient * p))`.

    Args:
        live: How many parameters move (`k`).
        cfg: The `size` block of `config.yaml`: `n_min`, `n_max`, `per_coefficient`.

    Returns:
        The count and whether the cap cut it: `p = 1 + 2k + k(k-1)/2` coefficients of the
        quadratic map, and fewer than `per_coefficient` variants per coefficient past the cap.
    """
    p = 1 + 2 * live + live * (live - 1) // 2
    want = cfg["per_coefficient"] * p
    return min(cfg["n_max"], max(cfg["n_min"], want)), want > cfg["n_max"]


def build(design: dict, settings: dict, table: pd.DataFrame,
          banned: dict[str, set] | None = None) -> tuple[pd.DataFrame, dict]:
    """The whole batch: which tuples, in which stratum, under which identifier.

    Args:
        design: A parsed brief, contract C1.
        settings: The parsed `config.yaml`, ledger numbers filled in.
        table: Output of `inputs.known`, the source of the canary expectations.
        banned: `design.pilot.decide`'s first return value, or `None` when the pilot did
            not run. A live parameter's dropped levels are removed from what the draw may
            land on -- never the whole parameter, never one that would leave fewer than two
            levels, and never the origin's own value.

    Returns:
        The plan and a report of how it was filled. `n` variants of stratum `lhs` PLUS the
        controls (origin `P00000`, canaries, inert pairs), which no study analyses.

        `n` is a cap, never a quota. A tuple is never repeated to reach it: duplicates after
        rounding are dropped and counted in `shortfall`, and a plateau with fewer distinct
        tuples than `n` just gives fewer (the report says so). Frozen parameters and shifts
        sit at the mother's value in every `lhs` row.
    """
    live = levels.live(design)
    origin = levels.origin(design)
    kept, pilot_dropped = dict(live), {}
    for name, bad in (banned or {}).items():
        if name not in live:
            continue
        keep = [v for v in live[name] if v not in bad - {origin.get(name)}]
        if len(keep) >= 2 and len(keep) < len(live[name]):
            pilot_dropped[name] = sorted(set(live[name]) - set(keep))
            kept[name] = keep
    everything = {**live, **levels.frozen(design, settings["design"]["frozen"])}

    rows, seen = [], set()
    for control in canaries.rows(design, everything, origin, table, settings["canaries"]):
        digest = tuples.tuple_hash(control["values"])
        if digest not in seen:
            seen.add(digest)
            rows.append({**control, "tuple_hash": digest})
    controls = len(rows)

    asked, capped = size(len(live), settings["size"])
    fixed = {name: value for name, value in origin.items() if name not in live}
    for values in lhs.draw(live, kept, asked, settings["design"]["seed"]):
        complete = {**fixed, **values}
        digest = tuples.tuple_hash(complete)
        if digest in seen:
            continue
        seen.add(digest)
        rows.append({"values": complete, "stratum": "lhs", "origin": False,
                     "expect_netprofit": None, "expect_trades": None,
                     "expect_same_as": None, "tuple_hash": digest})

    return _frame(rows), {
        "controls": controls, "live": len(live), "asked": asked, "capped": capped,
        "live_space": math.prod(len(v) for v in live.values()), "n": len(rows),
        "kept": len(rows) - controls, "shortfall": asked - (len(rows) - controls),
        "pilot_dropped": pilot_dropped}


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
