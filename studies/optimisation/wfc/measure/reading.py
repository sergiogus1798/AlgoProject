"""Every number of one in-sample / out-of-sample composition: the order on gross excess, the level on net."""

import numpy as np

from core.study import draws
from engines.weekly import flip
from studies.optimisation.wfc.measure import level

# Draws per block: draws x variants is never held whole (4 GB at 1 M draws), only a block of it.
BLOCK = 20_000


def _spearman(fixed: np.ndarray, flips: np.ndarray, panel: np.ndarray) -> np.ndarray:
    """flip.spearman of `fixed` against every draw of `flips @ panel`, a block of draws at a time."""
    return np.concatenate([flip.spearman(fixed, part @ panel) for part in flip.chunks(flips, BLOCK)])


def measure(e_is: dict, e_oos: dict, weeks: dict, years: float, cfg: dict,
            straddle: float = 0.0, name: str = "", comp: str = "",
            record: list | None = None) -> dict:
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
        name, comp: The mother's batch and the composition, kept in the recorded draws.
        record: A list that receives the null behind `p_mas`, `p_nivel` and `p_mas_bloque` as
            `core.study.draws` rows; None keeps nothing.

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
    spread = _spearman(e_is["gross"], signs, weeks["gross"])
    where = {"strategy": name, "seed": knobs["seed"], "comp": comp}
    recs = [draws.record("wfc", "p_mas", rho, spread, **where, p="flip.tails",
                         unit="rho de Spearman en el nulo de signos semanal")]
    blocked = {"p_mas": None, "p_menos": None}
    if straddle > knobs["straddle_warn"]:
        again = flip.signs(wide, knobs["draws"], size, cfg["annotate"]["block_weeks"])
        wider = _spearman(e_is["gross"], again, weeks["gross"])
        blocked = flip.tails(rho, wider)
        recs.append(draws.record("wfc", "p_mas_bloque", rho, wider, **where, p="flip.tails",
                                 unit="rho de Spearman con bloques de semanas"))
    inside, outside = e_is["net"], e_oos["net"]
    best = level.top(inside, cfg["level"]["top_share"])
    kept = level.retention(inside, outside, best, gap)
    tops, kept_null = [], []
    for part in flip.chunks(signs, BLOCK):
        flat = part @ weeks["net"] / years
        tops.append(np.median(flat[:, best], axis=1))
        if kept is not None:
            kept_null.append(level.retention(inside, flat, best, gap))
    tops = np.concatenate(tops)
    recs.append(draws.record("wfc", "p_nivel", float(np.median(outside[best])),
                             tops, **where, p="level.p_value",
                             unit="mediana fuera del top, exceso por año"))
    low, high = (None, None) if kept is None else np.percentile(np.concatenate(kept_null), [5, 95])
    win_in, win_out = inside > 0, outside > 0
    if record is not None:
        record.extend(recs)
    return {
        "n": int(inside.size), "rho": rho,
        **flip.tails(rho, spread),
        "fines_de_semana": float(straddle),
        "p_mas_bloque": blocked["p_mas"], "p_menos_bloque": blocked["p_menos"],
        "n_top": int(best.sum()),
        "nivel_top": float(np.median(outside[best])),
        "p_nivel": level.p_value(tops, float(np.median(outside[best]))),
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
