"""Synthetic families of variants whose answer is known: one common factor, own noise, a planted edge."""

import numpy as np

YEAR = 52                     # weeks in a year: the family is drawn week by week, as the null flips it
EXPOSURE = (0.5, 1.5)         # a variant's loading on the common factor, uniform between these
NONE, FLAT, ORDER = "sin_ventaja", "ventaja_sin_orden", "ventaja_con_orden"


def family(mean: float, spread: float, carry: int, variants: int, weeks_in: int, weeks_out: int,
           rng: np.random.Generator, own: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One family as step 17 measures it.

    Every variant's week is its own mean plus its exposure to one common factor plus noise of
    its own, so the variants are dependent as a batch's are: a bad week is bad for all of them.
    It carries no cost: its gross excess is its net.

    Args:
        mean: Weekly excess every variant expects, in units of the common factor's deviation.
        spread: Deviation of that mean across variants (the skill that can be ordered).
        carry: +1 the same variants are good outside, -1 the best inside are the worst outside.
        variants, weeks_in, weeks_out: The size of the family and of its two windows.
        rng: The generator.
        own: Deviation of each variant's own weekly noise; smaller makes the variants more alike.

    Returns:
        (e_is, e_oos, the out-of-sample weeks): excess per year inside and outside, one per
        variant, and the weekly excess outside, weeks down, variants across.
    """
    skill = spread * rng.normal(size=(variants, 1))
    exposure = rng.uniform(*EXPOSURE, (variants, 1))
    inside = (mean + skill + exposure * rng.normal(size=weeks_in)
              + own * rng.normal(size=(variants, weeks_in)))
    outside = (mean + carry * skill + exposure * rng.normal(size=weeks_out)
               + own * rng.normal(size=(variants, weeks_out)))
    return (inside.sum(axis=1) / (weeks_in / YEAR), outside.sum(axis=1) / (weeks_out / YEAR),
            outside.T)


def weekly(sharpe: float, own: float) -> float:
    """The weekly mean that is this annualised Sharpe against the variants' root-mean-square deviation.

    A variant's own Sharpe runs from about 0.7 to 1.7 times it, by its loading on the factor.
    """
    low, high = EXPOSURE
    return sharpe * np.sqrt((low * low + low * high + high * high) / 3 + own * own) / np.sqrt(YEAR)


def specs(cfg: dict) -> list[dict]:
    """Every scenario the calibration measures.

    Args:
        cfg: The calibration's config: `grid`, `family`, `reference`, `sensitivity`.

    Returns:
        One dict per scenario: `bloque` (`rejilla`, or `sensibilidad` for the reference cells
        at another dependence), `tipo` (NONE, FLAT or ORDER), `sharpe` (the planted mean as
        annualised Sharpe; negative is a cost), `anos_fuera` and `ruido_propio`.
    """
    grid, ref, own = cfg["grid"], cfg["reference"], cfg["family"]["own_noise"]
    kinds = ([(NONE, s) for s in [0.0, *grid["costs"]]]
             + [(kind, s) for kind in (FLAT, ORDER) for s in grid["edges"]])
    main = [{"bloque": "rejilla", "tipo": kind, "sharpe": s, "anos_fuera": years,
             "ruido_propio": own} for years in grid["years_out"] for kind, s in kinds]
    side = [{"bloque": "sensibilidad", "tipo": kind, "sharpe": s, "anos_fuera": ref["years_out"],
             "ruido_propio": other} for other in cfg["sensitivity"]["own_noise"]
            for kind, s in ((NONE, 0.0), (FLAT, ref["edge"]), (ORDER, ref["edge"]))]
    return main + side


def draw(spec: dict, cfg: dict, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One family of a scenario of specs(): what family() returns."""
    shape = cfg["family"]
    mean = weekly(spec["sharpe"], spec["ruido_propio"])
    spread = shape["order_spread"] * mean if spec["tipo"] == ORDER else 0.0
    return family(mean, spread, 1, shape["variants"], round(shape["years_in"] * YEAR),
                  round(spec["anos_fuera"] * YEAR), rng, spec["ruido_propio"])
