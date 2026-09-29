"""One strategy against its monkeys, as the contract's data: where it landed, where its edge came from."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, identity, output, result as envelope
from engines.nulls import simulate, verdict

MODULE = "nulls"
RUNGS_ES = {"timing": "cuándo entra",
            "timing_holds": "cuándo entra y cuánto aguanta",
            "timing_sizing": "cuándo entra y el tamaño por volatilidad",
            "free": "cuándo, cuánto y cuánto tamaño: sólo quedan el número de operaciones y "
                    "el coste"}
GLOSSARY = [
    {"term": "Mono", "text": "Una versión al azar de la estrategia con su mismo conjunto de "
     "oportunidades: mismas velas, misma ventana, mismos costes, misma huella."},
    {"term": "Peldaño", "text": "Lo que cada nulo deja al azar. Lo que le dejas fijo al nulo, "
     "se lo regalas: la distancia entre dos peldaños es lo que valía ese canal."},
    {"term": "p empírico", "text": "Qué fracción de los monos igualó o superó a la estrategia. "
     "El más pequeño observable es 1/(monos+1)."}]


def measure(trades: pd.DataFrame, frame: pd.DataFrame, cfg: dict, name: str) -> dict:
    """The real run and every rung's null runs, priced identically.

    Args:
        trades: One strategy's trades on one sample.
        frame: The bars they are placed on.
        cfg: What inputs.config() returned, with `feed` set.
        name: The strategy, which seeds its own monkeys.

    Returns:
        {"kept", "seen", "per_rung", "found"}: the calibrated trades, the real statistics,
        each rung's null statistics, and the headline rung's p per statistic.
    """
    kept = simulate.fixed(trades, frame, cfg)
    names = cfg["statistics"]["report"]
    seen = simulate.real(kept, names)
    per_rung = {rung: simulate.nulls(kept, rung, cfg, name) for rung in cfg["nulls"]["rungs"]}
    head = cfg["nulls"]["headline"]
    return {"kept": kept, "seen": seen, "per_rung": per_rung,
            "found": {n: verdict.pvalue(seen[n], per_rung[head][n], n) for n in names}}


def tabs(got: dict, cfg: dict, statistic: str) -> list[dict]:
    """The three readings: where it landed, the ladder of rungs, where its edge came from."""
    seen, per_rung, names = got["seen"], got["per_rung"], cfg["statistics"]["report"]
    head = per_rung[cfg["nulls"]["headline"]]
    draws = cfg["nulls"]["draws"]
    landed = [blocks.table("Tu estrategia contra el mono del peldaño titular", pd.DataFrame(
        [[n, seen[n], head[n].mean(), np.percentile(head[n], 95),
          (head[n] < seen[n]).mean(), got["found"][n]] for n in names],
        columns=["estadístico", "tu estrategia", "mono medio", "mono p95", "percentil",
                 "p"]),
        "Cinco estadísticos y ningún compuesto: cuál importa lo decide el dueño, y discrepan "
        "hasta en 45 puntos de la población.")]
    landed += [{**blocks.distribution(f"{n} — {draws:,} monos, peldaño {rung}", "", values[n],
                                      seen[n], RUNGS_ES[rung],
                                      p=verdict.pvalue(seen[n], values[n], n)),
                "select": {"estadístico": n, "peldaño": rung}}
               for rung, values in per_rung.items() for n in names]
    ladder = {"kind": "grid", "title": "p de cada estadístico en cada peldaño",
              "rows": list(per_rung), "cols": names,
              "values": [[verdict.pvalue(seen[n], per_rung[r][n], n) for n in names]
                         for r in per_rung],
              "scale": "sequential", "levels": [cfg["verdict"]["alpha"], 0.1, 0.25, 0.5],
              "labels": None, "note": "; ".join(f"{r}: aleatoriza {RUNGS_ES[r]}"
                                               for r in per_rung) + "."}
    a = verdict.attribute(seen, per_rung, statistic)
    rest = a["total"] - a["holding_time"] - a["sizing"]
    channels = {"kind": "bars", "title": f"De dónde sale la ventaja, en {statistic}",
                "unit": statistic, "reference": 0.0,
                "items": [{"label": label, "value": value, "error": None,
                           "state": "info"} for label, value in (
                    ("ventaja total sobre el mono suelto", a["total"]),
                    ("de cuánto aguanta la posición", a["holding_time"]),
                    ("del tamaño por volatilidad", a["sizing"]),
                    ("resto: el momento de entrar", rest))],
                "note": "El resto no se mide aparte: es lo que queda cuando los canales que sí "
                        "se pueden dar al azar ya se han dado."}
    return [envelope.tab("landed", "Dónde cayó entre los monos", landed,
                         selectors=[{"key": "estadístico", "label": "Estadístico",
                                     "options": names, "default": statistic},
                                    {"key": "peldaño", "label": "Peldaño",
                                     "options": list(per_rung),
                                     "default": cfg["nulls"]["headline"]}]),
            envelope.tab("ladder", "La escalera de nulos", [ladder]),
            envelope.tab("channels", "De dónde sale la ventaja", [channels])]


def run(strategy: str, given: dict, cfg: dict, statistic: str = "net") -> dict:
    """One strategy against its monkeys.

    Args:
        strategy: Its name in the export.
        given: {"trades": its trades on the sample, "frame": the bars, "folder": the export
            folder, whose manifest names project and databank for the identity}.
        cfg: What inputs.config() returned, with `feed` set.
        statistic: Which statistic the headline call and the channels read.

    Returns:
        The contract dict: a call on the headline rung, three tabs, the reasons to distrust.
    """
    started = time.time()
    trades = given["trades"]
    got = measure(trades, given["frame"], cfg, strategy)
    p, alpha = got["found"][statistic], cfg["verdict"]["alpha"]
    said = blocks.verdict(
        "bate al mono" if p <= alpha else "no se distingue del mono",
        "pass" if p <= alpha else "fail",
        f"En {statistic}, el {100 * (1 - p):.1f} % de los monos del peldaño "
        f"{cfg['nulls']['headline']} ({RUNGS_ES[cfg['nulls']['headline']]}) quedó por debajo; "
        f"p = {p:.4f}. Reconciliación {got['kept']['checks']['corr']:.6f} "
        f"(relleno {got['kept']['checks']['fill']}).", p)
    warn = [{"code": line.split(":")[0].lower(), "state": "watch",
             "text": line.split(":", 1)[1].strip()}
            for line in verdict.distrust(got["kept"], got["found"], len(trades), cfg)]
    ident = output.identify(given["folder"], [strategy])[strategy]
    return envelope.envelope(
        MODULE, strategy, ident, cfg, started,
        tabs(got, cfg, statistic), said, warn + identity.warning(ident), GLOSSARY,
        summary={"n": len(trades), "reconcile": got["kept"]["checks"]["corr"],
                 "nulls_seed": cfg["nulls"]["seed"],
                 **{f"p_{n}": v for n, v in got["found"].items()}})


def row(got: dict, trades: int, cfg: dict) -> dict:
    """One strategy's line of nulls.csv: real statistics, p per rung, attribution, distrust."""
    names = cfg["statistics"]["report"]
    out = {"n": trades, "reconcile": got["kept"]["checks"]["corr"]}
    out |= {f"real_{n}": got["seen"][n] for n in names}
    out |= {f"p_{rung}_{n}": verdict.pvalue(got["seen"][n], values[n], n)
            for rung, values in got["per_rung"].items() for n in names}
    out |= {f"edge_{k}": v for k, v in verdict.attribute(got["seen"], got["per_rung"],
                                                         names[0]).items()}
    out["distrust"] = " | ".join(verdict.distrust(got["kept"], got["found"], trades, cfg))
    return out

