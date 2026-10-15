"""One strategy's whole SPP reading: what moves it, what is dead, and whether it is worth more."""

from pathlib import Path
from typing import TypedDict

import pandas as pd

from core.surface import dedupe
from studies.breakage.spp.inputs import export
from studies.breakage.spp.model import influence, mapa, profile
from studies.breakage.spp.model.profile import Plateau
from studies.breakage.spp.verdict import noise
from studies.breakage.spp.verdict.noise import NoiseCheck, Shape


class Profile(TypedDict):
    """One parameter's curve and the plateau read from it."""

    curve: pd.DataFrame
    plateau: Plateau


class Read(TypedDict):
    """`read`: the grid's shape, eta-squared, duplicate test, profiles, noise call and original tuple."""

    strategy: str
    source: str
    metric: str
    parameters: list[str]
    grid: pd.DataFrame
    profile_metric: str
    eta2: pd.DataFrame
    duplicates: pd.DataFrame
    profiles: dict[str, Profile]
    noise: NoiseCheck
    shape: Shape
    original: dict[str, float]


PlateauSpan = TypedDict("PlateauSpan", {"from": float, "to": float})
Live = TypedDict(
    "Live",
    {
        "name": str,
        "eta2": float,
        "inert": bool,
        "center": float,
        "center_rule": str,
        "class": str,
        "plateau": PlateauSpan,
        "levels": list[float],
        "original": float,
        "argmax_is": float,
        "plateau_width": int,
        "spike": bool,
        "is_shift": bool,
    },
)
Frozen = TypedDict(
    "Frozen", {"name": str, "value": float, "reason": str, "class": str, "groups": int}
)


class Brief(TypedDict):
    """`brief`: the design_brief.json contract the variant factory reads."""

    strategy: str
    source: str
    verdict: str
    metric: str
    profile_metric: str
    n_eff: int
    noise_max: float
    observed_max: float
    excess: float
    parameters: list[Live]
    frozen: list[Frozen]


def read(directory: Path, strategy: str, settings: dict) -> Read:
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

    # The profile reads the floored grid (no shift rows, no thin permutations) on its own metric.
    pmetric = settings["profile"]["metric"]
    marginal_grid, _ = mapa.floored(
        export.grid(directory, strategy), names, settings["grid"]
    )
    if marginal_grid.empty:
        marginal_grid = export.without_original(grid)
    profiles: dict[str, Profile] = {}
    for name in names:
        curve = profile.marginal(marginal_grid, name, pmetric)
        shape = profile.plateau(curve, design["plateau_share"])
        profiles[name] = {"curve": curve, "plateau": shape}

    return {
        "strategy": strategy,
        "source": str(directory),
        "metric": metric,
        "parameters": names,
        "grid": grid,
        "profile_metric": pmetric,
        "eta2": influence.eta_squared(grid, names, metrics),
        "duplicates": influence.duplicate_test(grid, names),
        "profiles": profiles,
        "noise": noise.noise_check(grid, metric, settings["verdict"]["margin"]),
        "shape": noise.shape(grid, metric),
        "original": export.original(directory, strategy),
    }


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


def brief(result: Read, settings: dict) -> Brief:
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
    eta2, dup = result["eta2"][metric].to_dict(), result["duplicates"]
    frozen = [n for n in result["parameters"] if bool(dup.loc[n, "inert"])]
    live = [n for n in result["parameters"] if n not in frozen]
    shares = [float(eta2[n]) for n in live]

    parameters: list[Live] = []
    for name in live:
        curve, shape = (
            result["profiles"][name]["curve"],
            result["profiles"][name]["plateau"],
        )
        count = levels_for(float(eta2[name]), shares, design)
        shift = mapa.is_fixed(name, settings["grid"]["fixed"])
        parameters.append(
            {
                "name": name,
                "eta2": float(eta2[name]),
                "inert": bool(dup.loc[name, "inert"]),
                "center": shape["center"],
                "center_rule": "plateau_midpoint",
                # A shift stays where it was built (owner, 2026-09-26): it changes which bar the
                # rule reads, not how sensitive the rule is.
                # `class` and `plateau` are what the variant factory's Latin hypercube reads
                # (encargo 48 F): a live parameter moves inside [from, to], a shift never moves.
                "class": "shift" if shift else "live",
                "plateau": {"from": shape["from"], "to": shape["to"]},
                "levels": (
                    [float(result["original"][name])]
                    if shift
                    else profile.design_levels(
                        curve,
                        shape,
                        result["original"][name],
                        count,
                        design["min_span"],
                    )
                ),
                "original": float(result["original"][name]),
                "argmax_is": shape["argmax"],
                "plateau_width": shape["width"],
                # Width 1 means there is no plateau on this axis: the "centre" is the argmax
                # wearing another name, and a deployment sitting on it has no margin either
                # side. The fabrication stage must not read that centre as stable.
                "spike": shape["width"] == 1,
                "is_shift": shift,
            }
        )

    return {
        "strategy": result["strategy"],
        "source": result["source"],
        "verdict": result["noise"]["verdict"],
        "metric": metric,
        "profile_metric": result["profile_metric"],
        "n_eff": result["noise"]["n_eff"],
        "noise_max": result["noise"]["noise_max"],
        "observed_max": result["noise"]["observed_max"],
        "excess": result["noise"]["excess"],
        "parameters": parameters,
        "frozen": [
            {
                "name": n,
                "value": result["original"][n],
                "reason": "exact_duplicates",
                "class": "frozen",
                "groups": int(dup.loc[n, "groups"]),
            }
            for n in frozen
        ],
    }
