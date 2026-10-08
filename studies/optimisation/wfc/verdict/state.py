"""The call of step 17: the order's class, the «strong» label and PASA / LIMBO / NO PASA."""

import numpy as np

# The owner's table (proposal of step 17, section 6, with the level's null of encargo 48,
# decisions 5 and 6; owner, 2026-10-07, confirmed 2026-10-08), the deciding composition only.
# «Beats its null»: `p_nivel` <= `level.alpha`, one-sided, the order's very sign draws.
#
# | order \ top's median | > 0 and beats its null | > 0, does not beat it | <= 0    |
# |----------------------|------------------------|-----------------------|---------|
# | positivo / neutro    | pasa                   | limbo                 | no_pasa |
# | perverso             | limbo                  | limbo                 | no_pasa |
# | sin_dato             | limbo                  | limbo                 | limbo   |
NO_DATA = "sin_dato"


def classify(rho: float, p_mas: float, p_menos: float, alpha: float) -> str:
    """The class of the in-sample order out of sample.

    Args:
        rho: The observed Spearman.
        p_mas, p_menos: Its two tails in the sign-flip null.
        alpha: The cut on each tail.

    Returns:
        `positivo` (the best inside tend to be the best outside, beyond noise), `perverso`
        (they tend to be the worst), `neutro`, or `sin_dato` when rho does not exist.
    """
    if not np.isfinite(rho):
        return NO_DATA
    return "positivo" if p_mas <= alpha else "perverso" if p_menos <= alpha else "neutro"


def state(order: str, level: float, n: int, min_variants: int, p_nivel: float,
          level_alpha: float) -> str:
    """PASA, LIMBO or NO PASA, by the table above.

    Args:
        order: What classify() returned.
        level: Out-of-sample median excess of the in-sample top.
        n: Variants measured, after the filters.
        min_variants: Under this many there is no call.
        p_nivel: The top's median against the sign-flip null (upper tail).
        level_alpha: The cut on `p_nivel`: `level.alpha`. A cut of 1 asks nothing of the
            level, which is the calibration's comparison column and not the criterion.

    Returns:
        `pasa`, `limbo` or `no_pasa`. A top at or under zero is `no_pasa`, however far under
        (no lower tail is read); one above zero that does not beat its null, or that has a
        perverse order, is `limbo`.
    """
    if order == NO_DATA or n < min_variants:
        return "limbo"
    if not level > 0:
        return "no_pasa"
    return "limbo" if order == "perverso" or p_nivel > level_alpha else "pasa"


def judge(measured: dict, cfg: dict) -> dict:
    """The words of one composition from its measured numbers.

    Args:
        measured: What `measure.reading.measure` returned.
        cfg: The study's config: `null.alpha`, `level.alpha`, `order.rho_strong`,
            `panel.min_variants`.

    Returns:
        `orden`, `fuerte` (a positive order with rho at or above `rho_strong`; a label, it
        moves no state), `estado`, and `orden_bloque` when the null was drawn again in wider
        blocks: the class the order would take there, annotated.
    """
    alpha = cfg["null"]["alpha"]
    found = classify(measured["rho"], measured["p_mas"], measured["p_menos"], alpha)
    said = {"orden": found,
            "fuerte": found == "positivo" and measured["rho"] >= cfg["order"]["rho_strong"],
            "estado": state(found, measured["nivel_top"], measured["n"],
                            cfg["panel"]["min_variants"], measured["p_nivel"],
                            cfg["level"]["alpha"])}
    if measured.get("p_mas_bloque") is not None:
        said["orden_bloque"] = classify(measured["rho"], measured["p_mas_bloque"],
                                        measured["p_menos_bloque"], alpha)
    return said
