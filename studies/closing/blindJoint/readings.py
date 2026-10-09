"""The readings of "passes step 20" the spec leaves open, one entry each, for the owner to choose."""

import pandas as pd

from studies.closing.blindJoint.pieces import PIECES

# How the four pieces combine into "survives the pieces". Each takes the four states of one
# mother and says pass or fail. Adding a reading is one function and one row.
#
# | reading    | holds fixed                     | tolerates                           |
# |------------|---------------------------------|-------------------------------------|
# | unanimidad | every piece in `pass`           | nothing                             |
# | sin_fallo  | no piece in `fail`              | `watch`: indeciso, ciego, a medias, |
# |            |                                 | and the WFC's LIMBO (`pieces.WFC`)  |
# | ninguna    | nothing: the pieces are context | everything; the StepM decides alone |
# | peor       | no piece in `fail`              | nothing silently: the mother's call |
# |            |                                 | is her WORST piece (`worst`), and   |
# |            |                                 | the StepM is shown and decides none |
#
# `peor` is PROVISIONAL (owner, 2026-10-07), until step 20 is redesigned: «the worst state wins»
# over the four states of 17, 18, 18.5 and 19 — any fail DESCARTAR, else any watch REVISAR, else
# MANTENER. It is the one reading whose call has three values and does not wait for the StepM.
WORST = "peor"


def worst(states: list[str]) -> str:
    """The worst of a mother's piece states: fail, else pass when every one passes, else watch."""
    return "fail" if "fail" in states else "pass" if all(s == "pass" for s in states) else "watch"


COMBINE = {
    "unanimidad": lambda states: all(s == "pass" for s in states),
    "sin_fallo": lambda states: not any(s == "fail" for s in states),
    "ninguna": lambda states: True,
    WORST: lambda states: worst(states) != "fail",
}

# Over whom the StepM counts its search (encargo 10 §3, "una K que no es la K real").
# | population      | K                                           |
# |-----------------|---------------------------------------------|
# | supervivientes  | the mothers the pieces kept (encargo, literal) |
# | entrantes       | every complete mother that reached step 20  |
POPULATIONS = ("supervivientes", "entrantes")


def names() -> list[tuple[str, str]]:
    """Every distinct reading, as (pieces, population).

    Returns:
        The product, minus `ninguna` and `peor` with `supervivientes`: when the pieces keep
        everyone the two populations are the same one, and `peor` does not read the StepM.
    """
    return [(c, p) for c in COMBINE for p in POPULATIONS
            if not (c in ("ninguna", WORST) and p == "supervivientes")]


def label(reading: tuple[str, str]) -> str:
    """How a reading is written in tables and in the ledger's criterion."""
    return f"{reading[0]}+{reading[1]}"


def kept(states: pd.DataFrame, combine: str) -> list[str]:
    """The mothers that survive the pieces under one way of combining them.

    Args:
        states: One row per complete mother, one column per piece, each a state word.
        combine: A key of COMBINE.

    Returns:
        Their names, in the frame's order.
    """
    return [m for m, row in states.iterrows() if COMBINE[combine](row[list(PIECES)].tolist())]


def verdicts(states: pd.DataFrame, named: dict[str, list[str]]) -> pd.DataFrame:
    """Every complete mother's call under every reading.

    Args:
        states: As kept() takes it.
        named: {population label: what the StepM named over it}, keyed by label() of the
            reading, or None where the StepM was not run (the policy refused oos2).

    Returns:
        Mothers down, readings across, each cell `pass`, `fail` or `none` (the StepM half
        of the call could not be read). A mother passes a reading when the pieces keep it
        AND the StepM names it over that reading's population. Under `peor` the cell is her
        worst piece — `pass`, `watch` or `fail` — whatever the StepM named.
    """
    table = {}
    for reading in names():
        if reading[0] == WORST:
            table[label(reading)] = [worst(row[list(PIECES)].tolist())
                                     for _, row in states.iterrows()]
            continue
        survivors = set(kept(states, reading[0]))
        chosen = named[label(reading)]
        table[label(reading)] = [
            "fail" if m not in survivors else "none" if chosen is None
            else "pass" if m in chosen else "fail" for m in states.index]
    return pd.DataFrame(table, index=states.index)
