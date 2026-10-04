"""The funded verdict: every measure with its percentile in the null, and the sentence that says it."""

LABELS = {"start_p": "P(aprobar) en el camino real, desde cada día de inicio",
          "mc_p": "P(aprobar) del Monte Carlo más pesimista"}


def verdict(chosen: dict, null: dict, hold: dict, cost: dict, cfg: dict) -> dict:
    """Assemble the verdict; it passes or fails only when the owner's criterion exists.

    Args:
        chosen: The winner: `members` (list), `risk` ({phase: r}), `build_p` (stage B's
            deciding P(pass) re-drawn on fresh paths) and `selector_p` (the figure that
            chose it: the best of many noisy ones, so it reads high).
        null: `null.read()` output (measure -> value, percentile, ...).
        hold: `hold.held()` output.
        cost: `n_pool` (admissible strategies), `n_stage_a` (combinations the search
            evaluated), `n_shortlist`, `n_settings` (risk settings per combination),
            `null_draws`, `null_candidates`, `segments` (read to judge).
        cfg: The construct config; `verdict.pass_measure` and `verdict.pass_percentile` are
            the criterion's hook — both empty until the owner sets them (Q11).

    Returns:
        `chosen`, `measures`, `hold`, `cost`, `criterion` (the two knobs, or None) and `pass`
        (None while there is no criterion; else whether the named measure's percentile reaches
        the bar).
    """
    measure, bar = cfg["verdict"]["pass_measure"], cfg["verdict"]["pass_percentile"]
    criterion = None if measure is None or bar is None else {"measure": measure, "percentile": bar}
    passed = None if criterion is None else bool(null[measure]["percentile"] >= bar)
    return {"chosen": chosen, "measures": null, "hold": hold, "cost": cost,
            "criterion": criterion, "pass": passed}


def sentence(v: dict) -> str:
    """The decision in Spanish, its cost next to its gain, or plainly that no criterion exists."""
    c, cost = v["chosen"], v["cost"]
    risk = " / ".join(f"{r:.1%}" for r in c["risk"].values())
    lines = [f"La cartera de {len(c['members'])} estrategias (de {cost['n_pool']} admisibles; "
             f"{cost['n_stage_a']} combinaciones probadas en la etapa A, {cost['n_shortlist']} "
             f"finalistas × {cost['n_settings']} riesgos en la etapa B), a riesgo {risk} por "
             f"fase, leída en {'+'.join(cost['segments'])} contra {cost['null_draws']} búsquedas "
             f"al azar de {cost['null_candidates']} combinaciones cada una:"]
    for name, m in v["measures"].items():
        lines.append(f"  {LABELS.get(name, name)}: {m['value']:.3f} — percentil "
                     f"{m['percentile']:.0%} del nulo seleccionado (mediana nula "
                     f"{m['null_median']:.3f}, p95 {m['null_p95']:.3f})")
    h = v["hold"]
    lines.append(f"  diversificación fuera de muestra: {h['n_pairs_over']} de {h['n_pairs']} "
                 f"parejas pasan de algún umbral, {len(h['short'])} sin el solape mínimo para "
                 "juzgarlas")
    if v["pass"] is None:
        lines.append("Veredicto: SIN CRITERIO. Nadie ha fijado qué percentil aprueba (Q11, tuya): "
                     "con estas cifras decides tú si se compra el plan; no se descarta ni se "
                     "aprueba nada.")
    else:
        k = v["criterion"]
        word = "PASA: se compra el plan con esta cartera" if v["pass"] else \
            "NO PASA: no se compra el plan con esta cartera"
        lines.append(f"Veredicto: {word} ({k['measure']} en el percentil "
                     f"{v['measures'][k['measure']]['percentile']:.0%}, listón {k['percentile']:.0%}).")
    return "\n".join(lines)
