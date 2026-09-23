"""Given those numbers, what can be claimed and what should be distrusted.

It computes none of the numbers it judges and imports no simulation. It issues no keep or
discard: it locates a result, names what is wrong with it, and stops."""

import numpy as np

from nulls.stats import GOOD_HIGH

RECONCILE_FLOOR = 0.99      # below this the priced run is not the run SQX reported


def pvalue(seen: float, drawn: np.ndarray, name: str) -> float:
    """How often chance did at least as well as the real run.

    Args:
        seen: The real run's statistic.
        drawn: The same statistic over every null run.
        name: Its key in GOOD_HIGH, which says which side of it is the good one.

    Returns:
        The Davison-Hinkley p, `(1 + beaten) / (draws + 1)`. The +1 is not a rounding
        nicety: without it a real run no draw matched would score exactly 0, which is not a
        probability, and the smallest honest value is 1/(draws+1).
    """
    beaten = (drawn >= seen).sum() if GOOD_HIGH[name] else (drawn <= seen).sum()
    return float((1 + beaten) / (len(drawn) + 1))


def attribute(seen: dict, per_rung: dict, name: str) -> dict:
    """How much of the edge over the monkey each channel accounts for.

    Args:
        seen: What simulate.real() returned.
        per_rung: Rung name to the null statistics it produced.
        name: Which statistic to attribute.

    Returns:
        `total`, the real run's margin over the bottom rung, and one entry per channel: the
        gap between the null that keeps it and the null that hands it to chance, which is
        what that channel was worth **to a random trader**. Read the gaps, not their sum:
        this is a sequential decomposition and the channels are not orthogonal, so the
        order they are removed in is a declared choice and the remainder is what the entry
        timing itself carried.
    """
    mean = {rung: float(np.mean(values[name])) for rung, values in per_rung.items()}
    edge = seen[name] - mean["free"]
    sign = 1.0 if GOOD_HIGH[name] else -1.0
    return {"total": edge,
            "holding_time": sign * (mean["timing"] - mean["timing_holds"]),
            "sizing": sign * (mean["timing"] - mean["timing_sizing"]),
            "null_mean": mean["free"], "real": seen[name]}


def distrust(kept: dict, found: dict, trades: int, cfg: dict) -> list[str]:
    """Every reason to read these numbers with suspicion, in the owner's language.

    Args:
        kept: What simulate.fixed() returned.
        found: The headline rung's p per statistic, as pvalue() returned them.
        trades: How many trades the sample holds.
        cfg: What inputs.config() returned.

    Returns:
        One sentence per reason, empty when there is none. Nothing here removes a result or
        changes a number: a threshold that excludes evidence is a decision, and it is the
        owner's.
    """
    knobs, said = cfg["verdict"], []
    if kept["checks"]["corr"] < RECONCILE_FLOOR:
        said.append(f"RECONCILIACION: el P/L reconstruido correla {kept['checks']['corr']:.4f} "
                    f"con el de SQX, por debajo de {RECONCILE_FLOOR}. Nada de lo que sigue "
                    f"describe el backtest que SQX corrio.")
    if trades < knobs["min_trades"]:
        said.append(f"MUESTRA: {trades} trades, menos de {knobs['min_trades']}. No se calcula p.")
    floor = 1 / (cfg["nulls"]["draws"] + 1)
    topped = sorted(name for name, value in found.items() if value <= floor)
    if topped:
        said.append(f"P SATURADO en {', '.join(topped)}: el p mas pequeno observable es "
                    f"{floor:.1e}. Un resultado ahi abajo no esta medido, esta topado, y una "
                    f"correccion por multiplicidad no lo puede leer: sube nulls.draws.")
    if not kept["levels"]:
        said.append("CONVENCION INTRABAR: la estrategia no lleva stop ni objetivo, asi que "
                    "barrier.intrabar no se puede calibrar contra SQX en esta corrida. El dia "
                    "que lleve barreras, calibrarla es obligatorio antes de leer un p.")
    said.append("COSTES PROVISIONALES: el spread y la comision de XAUUSD son los defaults de "
                "SQX, no cifras pactadas con el broker (assets/symbols/XAUUSD.yaml). La posicion del "
                "null la fija sobre todo el coste, asi que estos p se mueven con ellos.")
    return said
