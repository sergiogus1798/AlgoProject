"""What each pair's two numbers mean, and whether the mother's region travels to the other markets."""

import pandas as pd


def pair_state(row: pd.Series, floor: float) -> str:
    """One pair's reading as a state word.

    Args:
        row: One row of `measure.pairs.matrix`.
        floor: The rho the whole interval must clear.

    Returns:
        `pass` when the interval sits above the floor AND the top deciles overlap beyond
        what independent rankings produce; `fail` when the interval sits below the floor;
        `watch` otherwise. Both numbers are asked for because they fail differently: a
        rho can be carried by the bottom of the surface agreeing (both markets hate the
        same corner) while the tops share nothing, and that is not a shared good region.

        **The decision is on `rho_neutral`, not the raw `rho`** (owner, OPEN.md §48,
        2026-09-29): net profit is partly time-in-market times drift, so two markets that
        merely drifted apart can carry a raw rho that is not the region travelling. The raw
        rho and its own interval are still returned for display, never for this call.
    """
    if row["rho_neutral_lo"] > floor and row["j"] > row["j_hi"]:
        return "pass"
    if row["rho_neutral_hi"] < floor:
        return "fail"
    return "watch"


def against_main(pairs: pd.DataFrame, main: str, floor: float) -> pd.DataFrame:
    """The main market against each declared one, per segment, with its state.

    Args:
        pairs: `measure.pairs.matrix` of every segment, with a `segment` column.
        main: The main feed.
        floor: What `pair_state` needs.

    Returns:
        One row per (segment, market), the main market's own diagonal excluded.
    """
    rows = pairs[(pairs["a"] == main) & (pairs["b"] != main)].copy()
    rows["state"] = rows.apply(pair_state, axis=1, floor=floor)
    return rows.rename(columns={"b": "market"}).drop(columns="a")


def mother(rows: pd.DataFrame, declared: int, min_share: float) -> dict:
    """The one call the step-20 read receives from this study.

    Args:
        rows: What `against_main` returned.
        declared: How many markets `_markets.yaml` fixed — the denominator, always. A
            declared market the batch lacks counts as not passing, never as absent.
        min_share: The share of them that must pass in every segment read.

    Returns:
        label, state, the passing count per segment and the sentence that explains it.
        `pass` when every segment reaches the share, `fail` when none does, `watch` when
        the segments disagree — the region travelled in one stretch of history only.
    """
    passed = {s: int((g["state"] == "pass").sum()) for s, g in rows.groupby("segment", sort=False)}
    reach = [n / declared >= min_share for n in passed.values()]
    counts = ", ".join(f"{n} de {declared} en {s}" for s, n in passed.items())
    if all(reach):
        return {"label": "la región viaja", "state": "pass", "passed": passed,
                "meaning": f"La misma región de parámetros es la buena en {counts}: una "
                           f"coincidencia así no la produce el azar de un backtest."}
    if not any(reach):
        return {"label": "la región no viaja", "state": "fail", "passed": passed,
                "meaning": f"Sólo {counts} ordenan las variantes como el mercado principal "
                           f"con el decil superior compartido: lo que es bueno aquí no lo es "
                           f"allí. Ganar en otro mercado, si gana, no es la misma región."}
    return {"label": "la región viaja a medias", "state": "watch", "passed": passed,
            "meaning": f"{counts}: la región viaja en un tramo de la historia y no en otro."}
