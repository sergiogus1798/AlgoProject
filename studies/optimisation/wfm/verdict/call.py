"""Given the correlation and the drift, does re-optimising this strategy buy anything?"""

PREDICTS, BLIND, PERVERSE = "predicts", "blind", "perverse"


def call(pooled: dict, drift: dict, settings: dict) -> dict:
    """The verdict on one strategy's walk-forward behaviour.

    Args:
        pooled: Output of `measure.correlation.pooled` for that strategy.
        drift: That strategy's row of `measure.drift.summary`, as a dict.
        settings: The `verdict` block of `config.yaml`.

    Returns:
        The call, the evidence behind it, and the warnings that qualify it.

        Three outcomes, and the middle one is the common one:

        - `predicts` -- the interval sits above zero. Re-optimising picks configurations
          that go on to do better, which is what walk-forward optimisation assumes.
        - `blind` -- the interval straddles zero. The in-sample ranking carries no
          information about what follows. Re-optimising is not harmful, it is pointless,
          and the cost of running it is real.
        - `perverse` -- the interval sits **below** zero. What optimises better goes on to
          do worse. This is the one that matters: it says the procedure is not merely
          uninformative but actively selecting for what will fail, and no amount of extra
          history fixes it.

        High drift alongside `blind` or `perverse` is the coherent picture, not a second
        finding: a surface with no out-of-sample signal has nothing to hold the optimiser
        in place, so it re-picks freely.
    """
    low, high = pooled["low"], pooled["high"]
    if low > settings["zero_band"]:
        verdict = PREDICTS
    elif high < -settings["zero_band"]:
        verdict = PERVERSE
    else:
        verdict = BLIND
    return {"verdict": verdict, "rho": pooled["rho"], "low": low, "high": high,
            "cells": pooled["cells"], "steps": pooled["steps"],
            "share_negative": pooled["share_negative"],
            "share_changed": drift["share_changed_median"],
            "drift_high": drift["share_changed_median"] >= settings["drift_high"]}


def sentence(result: dict, warning: str) -> str:
    """The verdict as one paragraph a human reads first.

    Args:
        result: Output of `call`.
        warning: Output of `model.windows.length_warning`, possibly empty.

    Returns:
        Spanish, because the manual's reader is the owner.
    """
    text = {
        PREDICTS: "lo que optimiza mejor **sí** predice lo que va mejor después",
        BLIND: "lo que optimiza mejor **no dice nada** sobre lo que va después",
        PERVERSE: "lo que optimiza mejor va **peor** después — la reoptimización está "
                  "seleccionando lo que va a fallar"}[result["verdict"]]
    lines = [f"ρ = {result['rho']:+.3f} (IC 95 % {result['low']:+.3f} a "
             f"{result['high']:+.3f}, sobre {result['cells']} celdas y "
             f"{result['steps']} tramos): {text}.",
             f"El optimizador cambia el {result['share_changed']:.1%} de los parámetros "
             f"de un tramo al siguiente."]
    if result["drift_high"]:
        lines.append("Esa deriva es alta: cada reoptimización elige una estrategia "
                     "sustancialmente distinta.")
    if warning:
        lines.append(warning)
    return " ".join(lines)
