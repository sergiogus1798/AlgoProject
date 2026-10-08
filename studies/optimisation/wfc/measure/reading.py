"""Every number of one in-sample / out-of-sample composition: the order on gross excess, the level on net."""

import numpy as np

from engines.weekly import flip
from studies.optimisation.wfc.measure import level


def measure(e_is: dict, e_oos: dict, weeks: dict, years: float, cfg: dict,
            straddle: float = 0.0) -> dict:
    """The order, the level and what is annotated beside them, for one composition.

    The order is read before costs: the variants that trade more pay more on both sides, which
    alone ranks them alike inside and outside, and a sign flip turns that cost into a gain
    and loses it from the null. The level is money, so it is read after costs.

    Args:
        e_is: `gross` and `net` -> excess per year of the in-sample window, one per variant
            (two at least).
        e_oos: The same for the out-of-sample window.
        weeks: `gross` and `net` -> the out-of-sample excess, weeks down and variants across,
            each trade whole in the week it closes in; a column sums to `e_oos * years`.
        years: Length of the out-of-sample window.
        cfg: The study's config: `null`, `level` and `annotate`.
        straddle: Share of the out-of-sample trades closed on a Monday or Tuesday after a
            weekend (`engines.weekly.panel.straddle`).

    Returns:
        `n`; `rho`, `p_mas`, `p_menos`, `nulo_p5`, `nulo_p95` (gross, the weekly sign-flip null
        at `null.block_weeks`); `fines_de_semana` (= straddle) and `p_mas_bloque`,
        `p_menos_bloque` (the same rho against blocks of `annotate.block_weeks`; None unless
        `straddle` exceeds `null.straddle_warn`); on net and the first null's very signs:
        `n_top`, `nivel_top`, `nivel_todas` (out-of-sample medians of the in-sample top and of
        every variant), `p_nivel` (share of draws whose top median is at or above the
        observed; `verdict` cuts it at `level.alpha`), `nivel_top_dentro`, `nivel_todas_dentro`,
        `r_sel` with `r_sel_p5` and `r_sel_p95` (all three None when the in-sample premium is
        too small); and the cloud's quadrants on net, `cuadrante_pp` (wins in and out), `_pn`
        (in only), `_np` (out only), `_nn`.
    """
    knobs, gap = cfg["null"], cfg["level"]["r_sel_min_gap"]
    main, wide = np.random.SeedSequence(knobs["seed"]).spawn(2)
    size = len(weeks["gross"])
    signs = flip.signs(main, knobs["draws"], size, knobs["block_weeks"])
    rho = float(flip.spearman(e_is["gross"], e_oos["gross"]))
    blocked = {"p_mas": None, "p_menos": None}
    if straddle > knobs["straddle_warn"]:
        again = flip.signs(wide, knobs["draws"], size, cfg["annotate"]["block_weeks"])
        blocked = flip.tails(rho, flip.spearman(e_is["gross"], again @ weeks["gross"]))
    inside, outside, flat = e_is["net"], e_oos["net"], signs @ weeks["net"] / years
    best = level.top(inside, cfg["level"]["top_share"])
    kept, kept_null = (level.retention(inside, out, best, gap) for out in (outside, flat))
    low, high = (None, None) if kept is None else np.percentile(kept_null, [5, 95])
    win_in, win_out = inside > 0, outside > 0
    return {
        "n": int(inside.size), "rho": rho,
        **flip.tails(rho, flip.spearman(e_is["gross"], signs @ weeks["gross"])),
        "fines_de_semana": float(straddle),
        "p_mas_bloque": blocked["p_mas"], "p_menos_bloque": blocked["p_menos"],
        "n_top": int(best.sum()),
        "nivel_top": float(np.median(outside[best])),
        "p_nivel": level.p_value(flat, best, float(np.median(outside[best]))),
        "nivel_todas": float(np.median(outside)),
        "nivel_top_dentro": float(np.median(inside[best])),
        "nivel_todas_dentro": float(np.median(inside)),
        "r_sel": None if kept is None else float(kept),
        "r_sel_p5": None if kept is None else float(low),
        "r_sel_p95": None if kept is None else float(high),
        "cuadrante_pp": int((win_in & win_out).sum()),
        "cuadrante_pn": int((win_in & ~win_out).sum()),
        "cuadrante_np": int((~win_in & win_out).sum()),
        "cuadrante_nn": int((~win_in & ~win_out).sum())}
