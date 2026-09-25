"""The verdict tab: the call and why, what failed, the backtest at a glance, and the sub-scores."""

import pandas as pd

from core.study import blocks, result as envelope
from portfolio.common.monteCarlo.contract import words
from portfolio.common.monteCarlo.contract.shapes import TIER_STATE, scale
from portfolio.common.monteCarlo.verdict import confidence, gates, scoring

GLANCE = ("net", "sharpe", "dd_pct", "ret_dd", "losing_run")


def _family_state(verdict: dict, family: str) -> str:
    """fail if a gate of this family fired, watch if only a warning did, pass otherwise."""
    fired = [f for f in verdict["flags"] if f["family"] == family]
    return "fail" if any(f["gate"] for f in fired) else "watch" if fired else "pass"


def verdict_block(result: dict, verdict: dict) -> dict:
    """The tier, the composite, the sentence naming what decided it, one part per family."""
    return blocks.verdict(
        verdict["tier"], TIER_STATE[verdict["tier"]], words.rationale(result, verdict),
        verdict["composite"],
        [{"label": f"Familia {k}", "state": _family_state(verdict, k), "value": v,
          "note": scoring.BUILT_FROM[k]} for k, v in verdict["subscores"].items()])


def fired(verdict: dict, family: str | None = None) -> dict:
    """Every check that fired, vetoes first, as a table; one family's only when named."""
    rows = [["VETO" if f["gate"] else "aviso", f["family"], words.title(f), words.sentence(f)]
            for f in sorted(verdict["flags"], key=lambda f: not f["gate"])
            if family is None or f["family"] == family]
    note = "" if rows else "Ninguna prueba falló ni levantó aviso."
    return blocks.table("Lo que falló" if family is None else f"Lo que falló en la familia "
                        f"{family}", pd.DataFrame(rows, columns=["tipo", "familia", "prueba",
                                                                 "qué dice"]), note)


def glance(result: dict, verdict: dict) -> dict:
    """The backtest against the median simulation, each row with its sample confidence."""
    runs = result["B"]["runs"]
    base = runs[next(iter(runs))]
    rows = [[words.LABELS[k], base[k]["observed"] * scale(k), base[k]["median"] * scale(k),
             base[k]["p"][5] * scale(k), base[k]["rank"],
             confidence.percentile(result["n_trades"], 5)] for k in GLANCE]
    rows += [["Inflación del drawdown", result["A"]["inflation"], None, None, None,
              verdict["tiers"]["dd_95"]],
             ["PSR", result["E"]["psr"], None, None, None,
              confidence.average(result["n_trades"])]]
    return blocks.table("De un vistazo", pd.DataFrame(
        rows, columns=["", "backtest", "mediana simulada", "percentil 5",
                       "rango del backtest", "confianza"]),
        "El backtest contra la mediana de las simulaciones. «Rango» es la fracción de "
        "simulaciones por debajo del backtest: cerca de 1 es un backtest afortunado.")


def scores(verdict: dict, cfg: dict) -> dict:
    """The five sub-scores as bars, the acceptable tier as the reference line."""
    return {"kind": "bars", "title": "Sub-scores por familia", "unit": "sobre 100",
            "reference": float(cfg["scoring"]["tiers"][1]),
            "items": [{"label": f"Familia {k}", "value": v, "error": None,
                       "state": _family_state(verdict, k)}
                      for k, v in verdict["subscores"].items()],
            "note": "La línea es el corte de ACCEPTABLE. Cada familia puntúa sobre lo que "
                    "dice su propia pestaña."}


def tab(result: dict, verdict: dict, cfg: dict) -> dict:
    """The tab the result opens on."""
    return envelope.tab("veredicto", "Veredicto",
                        [fired(verdict), glance(result, verdict), scores(verdict, cfg)],
                        note="Robustez de una estrategia ya aceptada: cuánto de este "
                             "resultado es suerte, y de qué tipo. Primero lo que falló, "
                             "después los números.")


def summary(result: dict, verdict: dict) -> dict:
    """The flat row the databank table and verdict.csv carry for this strategy."""
    return {"trades": result["n_trades"], "tier": verdict["tier"],
            "composite": verdict["composite"],
            **{f"score_{k}": v for k, v in verdict["subscores"].items()},
            "net": result["observed"]["net"], "dd_pct": result["observed"]["dd_pct"],
            "ret_dd": result["observed"]["ret_dd"],
            "dd_pct_95": result["A"]["dd_pct_95"], "dd_pct_99": result["A"]["dd_pct_99"],
            "inflation": result["A"]["inflation"], "net_5": result["B"]["net_5"],
            "pf_5": result["B"]["pf_5"], "oos_ratio": result["B"]["oos_ratio"],
            "outlier_share": result["B"]["outlier"]["share"],
            "windows_ok": gates.passing(result["D"]["overlapping"]),
            "high_vol_net": result["D"]["regime"]["buckets"]["high"]["median_net"],
            "stitched_dd_pct": result["D"]["stitch"][0.05]["dd_pct"],
            "psr": result["E"]["psr"],
            "gates": sum(1 for f in verdict["flags"] if f["gate"]),
            "flags": sum(1 for f in verdict["flags"] if not f["gate"]),
            "confidence": verdict["tiers"]["worst"],
            "fired": [{k: f[k] for k in ("family", "test", "value", "limit", "gate")}
                      for f in verdict["flags"]]}
