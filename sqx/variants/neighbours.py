"""Step 14's T1 draw: which parameters of a mother move, and her neighbours with all of them moved at once."""

import re
import zlib

import numpy as np

from sqx.variants import lengths, manifest, tuples
from sqx.variants.build import rewrite

ENTRY, EXIT = "entry", "exit"
EXIT_USED = "ParamTypeExitUsed"


def classes(portfolio: str, cfg: dict) -> dict[str, str]:
    """The parameters the draw moves, each with the class that sets how far.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        cfg: The `neighbours` block of config.yaml; reads `fixed`.

    Returns:
        Variable name to "entry" or "exit", in declaration order. A parameter is a numeric
        variable SQX gave a `<paramType>` — `MagicNumber` and the signal booleans have none.
        Left out: what SQX types a shift, and any name a `fixed` pattern finds (shifts again,
        by name, and the selectors — an enum is an int like any other to SQX). "exit" is what
        SQX types `ParamTypeExitUsed`; everything else is "entry".

        A coefficient written as a literal inside a formula is no variable and is not here.
    """
    kind = lengths.kinds(portfolio)
    return {
        name: EXIT if kind[name] == EXIT_USED else ENTRY
        for name, typed in rewrite.declared(portfolio).items()
        if typed in manifest.NUMERIC
        and kind[name]
        and kind[name] != lengths.SHIFT
        and not any(re.search(p, name) for p in cfg["fixed"])
    }


def mother(portfolio: str, cfg: dict) -> dict[str, float]:
    """The mother's own tuple over the parameters the draw moves, as her file stores it."""
    stored = rewrite.values(portfolio)
    return {name: float(stored[name]) for name in classes(portfolio, cfg)}


def draw(
    portfolio: str, strategy: str, cfg: dict
) -> tuple[list[dict[str, float]], int]:
    """One mother's neighbours: every moved parameter drawn uniformly around her own value.

    Args:
        portfolio: Text of the mother's `strategy_Portfolio.xml`.
        strategy: Her name; mixed into the seed, so each mother has her own draw.
        cfg: The `neighbours` block: `n`, `entry_pct`, `exit_pct`, `fixed`, `seed`, `int_floor`.

    Returns:
        (tuples, duplicates dropped). Each tuple holds every moved parameter at
        value x (1 + u), u uniform in +/- its class's percent, and holds exactly what the file
        will: an int rounded as `rewrite.set_values` writes it and kept at or above
        `int_floor` (unless the mother herself is below it), a double at the six significant
        digits `%g` keeps. A tuple equal to the mother's or to an earlier one is dropped and
        counted, never redrawn: a period of 3 has one value within 15 %, and `n` is a cap.
    """
    moved, types = classes(portfolio, cfg), rewrite.declared(portfolio)
    own = mother(portfolio, cfg)
    reach = np.array([cfg[f"{moved[name]}_pct"] for name in own]) / 100.0
    rng = np.random.default_rng([cfg["seed"], zlib.crc32(strategy.encode("utf-8"))])
    factors = 1.0 + reach * rng.uniform(-1.0, 1.0, (cfg["n"], len(own)))
    seen, out = {tuples.tuple_hash(own)}, []
    for row in factors:
        drawn = {}
        for (name, value), factor in zip(own.items(), row):
            if types[name] == "int":
                moved_to = float(round(value * factor))
                drawn[name] = (
                    max(moved_to, float(cfg["int_floor"]))
                    if value >= cfg["int_floor"]
                    else moved_to
                )
            else:
                drawn[name] = float(f"{value * factor:g}")
        key = tuples.tuple_hash(drawn)
        if key not in seen:
            seen.add(key)
            out.append(drawn)
    return out, cfg["n"] - len(out)
