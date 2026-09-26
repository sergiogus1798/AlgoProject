"""One strategy's whole SPP reading: what moves it, what is dead, and whether it is worth more."""

from pathlib import Path

from core.surface import dedupe
from studies.breakage.spp.inputs import export
from studies.breakage.spp.model import influence, profile
from studies.breakage.spp.verdict import noise


def read(directory: Path, strategy: str, settings: dict) -> dict:
    """Everything the reconnaissance concludes about one strategy.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy.
        settings: The parsed `config.yaml`.

    Returns:
        The grid's shape, the eta-squared table, the duplicate test, one profile per
        parameter, the noise verdict, and the original tuple. `report` renders it and
        `brief` turns it into the design; neither recomputes anything.
    """
    read_cfg, design = settings["read"], settings["design"]
    metric = read_cfg["metric"]
    names = export.parameters(directory, strategy)
    grid = dedupe.drop_sentinels(export.grid(directory, strategy))
    metrics = [metric] + [m for m in read_cfg["companion_metrics"] if m != metric]

    profiles = {}
    for name in names:
        curve = profile.marginal(grid, name, metric)
        shape = profile.plateau(curve, design["plateau_share"])
        profiles[name] = {"curve": curve, "plateau": shape}

    return {"strategy": strategy, "source": str(directory), "metric": metric,
            "parameters": names, "grid": grid,
            "eta2": influence.eta_squared(grid, names, metrics),
            "duplicates": influence.duplicate_test(grid, names),
            "profiles": profiles,
            "noise": noise.noise_check(grid, metric, settings["verdict"]["margin"]),
            "shape": noise.shape(grid, metric),
            "original": export.original(directory, strategy)}


def levels_for(eta2: float, live: list[float], design: dict) -> int:
    """How many levels this parameter earns in the variant grid.

    Args:
        eta2: Its variance share on the verdict metric.
        live: The same figure for every parameter that is not frozen.
        design: The `design` block of `config.yaml`.

    Returns:
        A count between `min_levels` and `max_levels`, allocated in proportion to variance
        explained. A flat split would spend the same budget resolving a parameter that
        does nothing as one that decides the result, and the budget is what limits how
        finely the plateau can be seen.
    """
    lo, hi = design["min_levels"], design["max_levels"]
    span = max(live) - min(live)
    if span == 0:
        return lo
    return int(round(lo + (hi - lo) * (eta2 - min(live)) / span))


def brief(result: dict, settings: dict) -> dict:
    """The design the fabrication stage consumes, derived from the reading.

    Args:
        result: Output of `read`.
        settings: The parsed `config.yaml`.

    Returns:
        The `design_brief.json` contract: which parameters are frozen and why, and for
        each live one its centre, its levels, and the original and argmax values the span
        had to contain.

        **A parameter is frozen on the duplicate test alone, never on eta-squared.** The
        two answer different questions and only one of them is proof. Measured 2026-09-20
        on `Strategy 17.9.39`: `CBlock_SqzMmnInt21` gave 217 groups and all 217 identical
        -- it provably never moved a backtest -- yet its eta-squared on Ret/DD is 0.0173,
        above any sensible freezing threshold. An SPP samples unbalanced, so each level of
        an inert parameter met a different mix of the others, and the spread between group
        means is confounding rather than effect. Eta-squared of an inert parameter is not
        zero, it is biased upward. The reverse also fails: `IsBars1` scores 0.0016 and is
        demonstrably live, with 1 of 188 groups identical.

        So eta-squared does the job it is good at -- **allocating levels** among the live
        parameters -- and the duplicate test decides who is in the design at all.
    """
    design, metric = settings["design"], result["metric"]
    eta2, dup = result["eta2"][metric], result["duplicates"]
    frozen = [n for n in result["parameters"] if bool(dup.loc[n, "inert"])]
    live = [n for n in result["parameters"] if n not in frozen]
    shares = [float(eta2[n]) for n in live]

    parameters = []
    for name in live:
        curve, shape = result["profiles"][name]["curve"], result["profiles"][name]["plateau"]
        count = levels_for(float(eta2[name]), shares, design)
        parameters.append({
            "name": name, "eta2": float(eta2[name]), "inert": bool(dup.loc[name, "inert"]),
            "center": shape["center"], "center_rule": "plateau_midpoint",
            # A shift stays where it was built (owner, 2026-09-26): it changes which bar the
            # rule reads, not how sensitive the rule is.
            "levels": ([float(result["original"][name])] if name.lower().endswith("shift1") else
                       profile.design_levels(curve, shape, result["original"][name], count,
                                             design["min_span"])),
            "original": float(result["original"][name]), "argmax_is": shape["argmax"],
            "plateau_width": shape["width"],
            # Width 1 means there is no plateau on this axis: the "centre" is the argmax
            # wearing another name, and a deployment sitting on it has no margin either
            # side. The fabrication stage must not read that centre as stable.
            "spike": shape["width"] == 1,
            "is_shift": name.lower().endswith("shift1")})

    return {"strategy": result["strategy"], "source": result["source"],
            "verdict": result["noise"]["verdict"], "metric": metric,
            "n_eff": result["noise"]["n_eff"], "noise_max": result["noise"]["noise_max"],
            "observed_max": result["noise"]["observed_max"],
            "parameters": parameters,
            "frozen": [{"name": n, "value": result["original"][n],
                        "reason": "exact_duplicates",
                        "groups": int(dup.loc[n, "groups"])} for n in frozen],
            "strata": design["strata"], "n_target": design["n_target"]}
