"""The verdict of both paths (Q11 d): oos1 first, oos2 only if it passed, and the funded sentence."""

from typing import Any, TypedDict

from .hold import Held

Judgement = TypedDict("Judgement", {"pass": bool | None, "label": str})

LABELS = {"start_p": "P(aprobar) en el camino real, desde cada día de inicio",
          "mc_p": "P(aprobar) del Monte Carlo más pesimista"}
MEASURES = tuple(LABELS)
UNOPENED = {"state": "not_opened", "reason": "oos1 no se ha pasado: oos2 no se abre"}


def grouped(n: float) -> str:
    """A count as the owner reads it, thousands split by a space: «10 000», never the English «10,000»."""
    return f"{n:,.0f}".replace(",", " ")


def funded_oos1(read: dict, same: int, cfg: dict) -> dict[str, Any]:
    """The funded path's oos1 reading: the named measure's percentile in the null against the bar.

    Args:
        read: `null.read()` on oos1 (measure -> value, percentile, ...).
        same: How many null searches chose the chosen combination itself.
        cfg: The construct config: `verdict.pass_measure` and `verdict.pass_percentile`.

    Returns:
        `measures`, `measure`, `bar`, `same`, `n` (null searches) and `state`: "sin_criterio"
        with the missing `knob` while either is unset -- never a silent None --, else
        "no_discrimina" when the chosen one is itself at least the null's top `1 - bar`,
        else "pass" or "fail".
    """
    measure, level = cfg["verdict"]["pass_measure"], cfg["verdict"]["pass_percentile"]
    n = next(iter(read.values()))["n"]
    out = {"measures": read, "measure": measure, "bar": level, "same": int(same), "n": n}
    missing = [f"verdict.{k}" for k, v in (("pass_measure", measure), ("pass_percentile", level))
               if v is None]
    if missing or measure not in read:
        return {**out, "state": "sin_criterio",
                "knob": " y ".join(missing) or f"verdict.pass_measure ∈ {list(read)}"}
    if same / n + 1e-12 >= 1 - level:
        return {**out, "state": "no_discrimina"}
    return {**out, "state": "pass" if read[measure]["percentile"] >= level else "fail"}


def combine(oos1: dict, oos2: dict) -> Judgement:
    """What the two readings decide together.

    Returns:
        `pass` (True, False, or None when nothing could be decided) and `label`, the Spanish
        words that say which -- a None always carries its reason.
    """
    first = oos1["state"]
    if first == "sin_criterio":
        return {"pass": None, "label": f"SIN CRITERIO (falta {oos1['knob']})"}
    if first == "no_discrimina":
        return {"pass": None, "label": "NO SE PUEDE JUZGAR (el azar repite la cartera elegida)"}
    if first == "fail":
        return {"pass": False, "label": "NO PASA (oos1)"}
    if oos2["state"] in ("pass", "fail"):
        passed = oos2["state"] == "pass"
        return {"pass": passed, "label": "PASA" if passed else "NO PASA (oos2)"}
    return {"pass": None, "label": f"SIN VEREDICTO: oos1 pasado, oos2 sin leer ({oos2['reason']})"}


def oos2_line(oos2: dict) -> str:
    """The oos2 reading in Spanish, or why there is none."""
    if oos2["state"] not in ("pass", "fail"):
        return f"  oos2: no se lee — {oos2['reason']}"
    again = (f" Lectura guardada del {oos2['read_on'][:10]}, no se ha vuelto a calcular."
             if oos2["stored"] else " Leído una vez: el segmento queda gastado para este pool.")
    return (f"  oos2: Sharpe diario {oos2['sharpe']:.4f} menos el máximo que da el azar "
            f"{oos2['benchmark']:.4f} (N = {grouped(oos2['n'])} pruebas de todo el proyecto, σ = "
            f"{oos2['sigma']:.4f}) = {oos2['excess']:+.4f} en {oos2['n_days']} días; DSR "
            f"{oos2['dsr']:.2f} → {'PASA' if oos2['state'] == 'pass' else 'NO PASA'}.{again}")


def hold_line(hold: dict, segments: list[str]) -> str:
    """«Did the diversification hold» in one Spanish line."""
    return (f"  diversificación en {'+'.join(segments)}: {hold['n_pairs_over']} de "
            f"{hold['n_pairs']} parejas pasan de algún umbral, {len(hold['short'])} sin el "
            "solape mínimo para juzgarlas (se informa, no decide)")


def verdict(chosen: dict, oos1: dict, oos2: dict, hold: Held, cost: dict) -> dict[str, Any]:
    """Assemble a verdict of either path.

    Args:
        chosen: The winner: `members` and what the path knows of it -- funded: `risk`
            ({phase: r}), `build_p`, `selector_p`.
        oos1: `funded_oos1()`'s reading, or the real path's (`null.bar()`).
        oos2: `oos2.read()`'s reading, or `UNOPENED`.
        hold: `hold.held()` on the segments opened.
        cost: What it cost to get here, and `segments` (the ones opened).

    Returns:
        Those five, plus `pass` and `label` (`combine()`).
    """
    return {"chosen": chosen, "oos1": oos1, "oos2": oos2, "hold": hold, "cost": cost,
            **combine(oos1, oos2)}


def sentence(v: dict) -> str:
    """The funded decision in Spanish, its cost next to its gain."""
    c, cost, first = v["chosen"], v["cost"], v["oos1"]
    risk = " / ".join(f"{r:.1%}" for r in c["risk"].values())
    lines = [f"La cartera de {len(c['members'])} estrategias (de {cost['n_pool']} admisibles; "
             f"{cost['n_stage_a']} combinaciones probadas en la etapa A, {cost['n_shortlist']} "
             f"finalistas × {cost['n_settings']} riesgos en la etapa B), a riesgo {risk} por "
             f"fase, leída en oos1 contra {cost['null_draws']} búsquedas al azar de "
             f"{cost['null_candidates']} combinaciones cada una:"]
    for name, m in first["measures"].items():
        lines.append(f"  oos1 · {LABELS.get(name, name)}: {m['value']:.3f} — percentil "
                     f"{m['percentile']:.0%} del nulo seleccionado (mediana nula "
                     f"{m['null_median']:.3f}, p95 {m['null_p95']:.3f})"
                     + (" ← la que decide" if name == first["measure"] else ""))
    lines.append(f"  {first['same']} de las {first['n']} búsquedas al azar eligieron esta misma cartera"
                 + (": el pool es tan pequeño que el nulo la repite y su percentil no dice nada"
                    if first["state"] == "no_discrimina" else ""))
    lines += [oos2_line(v["oos2"]), hold_line(v["hold"], cost["segments"])]
    tail = {True: "se compra el plan con esta cartera",
            False: "no se compra el plan con esta cartera",
            None: "no se aprueba ni se descarta nada"}[v["pass"]]
    if first["state"] in ("pass", "fail"):
        tail += (f" ({first['measure']} en el percentil "
                 f"{first['measures'][first['measure']]['percentile']:.0%} en oos1, listón "
                 f"{first['bar']:.0%})")
    lines.append(f"Veredicto: {v['label']} — {tail}.")
    return "\n".join(lines)
