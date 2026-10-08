"""Step 18's facts and its state: the real CSCV read against its null, and the cut of the proposal."""

from engines.weekly import flip

NULLS = ("nulo", "nulo_bruto")      # the kinds of draw that plant nothing
PASS, LIMBO, FAIL = "pasa", "limbo", "no_pasa"


def state(facts: dict, cfg: dict) -> str:
    """The step's state from its facts (proposal, section 6.1).

    Args:
        facts: What facts() returned.
        cfg: The study's config: `state.p_perdida_fail` is the cut of the probability of loss
            and `panel.min_variants` the fewest variants worth judging.

    Returns:
        `no_pasa` when the pick loses out of sample in `p_perdida_fail` of the partitions or
        more, or the PBO reaches its own null's p95; `limbo` when it loses more often than
        the p95 of its own null does (owner, 2026-10-08), or fewer than `min_variants` are
        left; else `pasa`.
    """
    if facts["n"] < cfg["panel"]["min_variants"]:
        return LIMBO
    if facts["p_perdida"] >= cfg["state"]["p_perdida_fail"] or facts["pbo_sobre_p95"]:
        return FAIL
    return LIMBO if facts["p_perdida_sobre_p95"] else PASS


def facts(read: dict, draws: dict, counts: dict, cfg: dict) -> dict:
    """Everything step 18 annotates of one mother, as numbers and one word.

    Args:
        read: The real panel's readings: `real` and `bruto` (`outputs.summary` on net and on
            gross cells), `seleccion` (`outputs.selection`) and `madre` (`outputs.mother`, or
            None when she is not in the panel).
        draws: Kind -> one row of `outputs.summary` per draw: `nulo`, `nulo_bruto`, and one
            `dNN` per planted Sharpe.
        counts: What `inputs.batch.screen` counted.
        cfg: The study's config.

    Returns:
        The facts of the plan's contract: `p_perdida`, `pbo_sobre_p95` and
        `p_perdida_sobre_p95` decide; `pbo_p` is the share of the null's draws at or under the
        real PBO, the real one counted (`pbo_p_mas`: at or above); `nulo.*` the null's own
        numbers, `nulo.p_perdida_p95` the `state.p_perdida_null_pct` percentile of its
        probability of loss; `p_perdida_sobre_p95` is strict, so a pick that never loses is
        not over a null that never loses either; `bruto.*` the same PBO on
        gross cells; `orden_estable` 1 when the PBO is at or under its null's p5 on both;
        `potencia.dNN` the share of draws with that annual Sharpe planted whose PBO falls
        under the null's p5; `madre.*`, `dominancia.*`, `seleccion.*`; and `estado`.
    """
    real, bruto, null = read["real"], read["bruto"], draws["nulo"]
    pbo = flip.tails(real["pbo"], null["pbo"].to_numpy())
    beta = flip.tails(real["beta"], null["beta"].to_numpy())
    gross = flip.tails(bruto["pbo"], draws["nulo_bruto"]["pbo"].to_numpy())
    middle = float(null["pbo"].median())
    lost_top = float(null["p_perdida"].quantile(cfg["state"]["p_perdida_null_pct"] / 100))
    out = {
        "n": counts["quedan"], "duplicados_pct": counts["duplicados_pct"],
        "p_perdida": real["p_perdida"], "pbo": real["pbo"], "pbo_p": pbo["p_menos"],
        "pbo_p_mas": pbo["p_mas"], "pbo_sobre_p95": int(real["pbo"] >= pbo["nulo_p95"]),
        "p_perdida_sobre_p95": int(real["p_perdida"] > lost_top),
        "beta": real["beta"], "beta_p": beta["p_menos"], "r2": real["r2"], "hc": real["hc"],
        "nulo": {"pbo_p5": pbo["nulo_p5"], "pbo_p95": pbo["nulo_p95"], "pbo_mediana": middle,
                 "pbo_desv": float(null["pbo"].std()),
                 "p_perdida": float(null["p_perdida"].median()), "p_perdida_p95": lost_top,
                 "beta_p5": beta["nulo_p5"], "beta_p95": beta["nulo_p95"],
                 "beta_mediana": float(null["beta"].median()),
                 "r2_mediana": float(null["r2"].median()),
                 "hc_mediana": float(null["hc"].median()), "sorteos": len(null),
                 "mediana_en_banda": int(cfg["null"]["median_low"] <= middle
                                         <= cfg["null"]["median_high"])},
        "bruto": {"pbo": bruto["pbo"], "pbo_p": gross["p_menos"], "nulo_p5": gross["nulo_p5"],
                  "nulo_p95": gross["nulo_p95"], "p_perdida": bruto["p_perdida"]},
        "potencia": {kind: float((rows["pbo"] < pbo["nulo_p5"]).mean())
                     for kind, rows in draws.items() if kind not in NULLS},
        "dominancia": {"primer_orden": int(real["primer_orden"]),
                       "segundo_orden": int(real["segundo_orden"]), "brecha": real["brecha"],
                       "nulo_primer_orden": float(null["primer_orden"].mean()),
                       "nulo_segundo_orden": float(null["segundo_orden"].mean())},
        "seleccion": {"distintas": read["seleccion"]["distintas"],
                      "peso": read["seleccion"]["peso"]}}
    out["orden_estable"] = int(real["pbo"] <= pbo["nulo_p5"] and bruto["pbo"] <= gross["nulo_p5"])
    if read["madre"]:
        out["madre"] = {k: int(v) if isinstance(v, bool) else v for k, v in read["madre"].items()}
    return out | {"estado": state(out, cfg)}


def no_data(counts: dict) -> dict:
    """The facts of a batch with too few variants left: nothing measured, LIMBO."""
    return {"n": counts["quedan"], "duplicados_pct": counts["duplicados_pct"], "estado": LIMBO}
