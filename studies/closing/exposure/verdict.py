"""Given those numbers, is the market time this strategy spends worth what it brings back."""

REASONS = {
    "few_trades": "{n} operaciones: por debajo de {min}, ninguna tasa es legible",
    "short_window": "{days} dias de ventana: por debajo de {min}, el CAGR es una ficcion",
    "loses": "pierde dinero en la ventana; la eficiencia por hora no se interpreta",
    "bench_loses": "el buy and hold pierde en esta ventana, asi que batirlo no dice nada "
                   "por si solo: lee `return_pct` y el drawdown, no la eficiencia",
    "inefficient": "eficiencia {eff:.2f}x, por debajo de {min:.2f}x: por hora expuesta no "
                   "rinde mas que tener el activo",
    "timing": "capturo el {cap:.1%} del movimiento del mercado estando dentro el "
              "{share:.1%} del tiempo, y alineado solo el {ali:.1%}: se parece mas a estar "
              "presente en los tramos buenos que a una ventaja propia",
}


def judge(strategy: dict, bench: dict, exposure: dict, trade_off: dict, presence: dict,
          n: int, days: int, cfg: dict) -> dict:
    """The verdict on the trade-off, and every reason not to trust it.

    Args:
        strategy: What `compare.stats` returned for the strategy.
        bench: The same for the headline benchmark convention.
        exposure: What `occupancy.measure` returned.
        trade_off: What `compare.dichotomy` returned.
        presence: What `occupancy.presence` returned.
        n: Trades in the window.
        days: Days the window spans.
        cfg: What `inputs.config` returned.

    Returns:
        `verdict` -- "worth_it" or "not_worth_it" -- and `reasons`, the lines that decided
        it or that say why it cannot be read. A strategy is worth it when it earns more per
        hour of exposure than the benchmark does per hour of its own, by the multiple the
        config asks for. Returning less in absolute terms than buy and hold is not a
        failure here and never fires a reason: that is the whole point of the study.
    """
    gate = cfg["gate"]
    unreadable = []
    if n < gate["min_trades"]:
        unreadable.append(REASONS["few_trades"].format(n=n, min=gate["min_trades"]))
    if days < gate["min_days"]:
        unreadable.append(REASONS["short_window"].format(days=days, min=gate["min_days"]))
    if strategy["net"] <= 0:
        unreadable.append(REASONS["loses"])
    if bench["return_pct"] <= 0:
        unreadable.append(REASONS["bench_loses"])

    reasons = list(unreadable)
    passes = trade_off["efficiency"] >= gate["min_efficiency"]
    if not passes:
        reasons.append(REASONS["inefficient"].format(eff=trade_off["efficiency"],
                                                     min=gate["min_efficiency"]))
    if presence["captured"] > exposure["share"] * 2 and presence["aligned"] <= 0:
        reasons.append(REASONS["timing"].format(cap=presence["captured"],
                                                share=exposure["share"],
                                                ali=presence["aligned"]))
    return {"verdict": "worth_it" if passes and not unreadable else "not_worth_it",
            "reasons": reasons}
