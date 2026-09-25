"""What the two curves mean, against thresholds fixed before the trades are read."""

import numpy as np
import pandas as pd

MEANS = {
    "signal": "la entrada predice movimiento favorable por encima del azar con su mismo horario",
    "no_signal": "la entrada no se distingue de entrar al azar a las mismas horas: lo que gana "
                 "viene de las salidas o de la deriva del mercado",
    "latency_fragile": "una barra de retraso se lleva una parte grande del edge bruto: o es "
                       "frágil a la latencia, o hay información del futuro en la entrada",
    "latency_robust": "el edge sobrevive a entrar tarde",
}


def signal(real: np.ndarray, bands: dict) -> str:
    """Whether the real e-ratio curve sits above its random band.

    Args:
        real: The real e(k).
        bands: What `eratio.band` returned.

    Returns:
        One key of MEANS. It asks for the **majority** of horizons rather than one: a
        single k above the band out of fifty is what a 5% band produces by construction.
    """
    return "signal" if (real > bands["high"]).mean() > 0.5 else "no_signal"


def latency(table: pd.DataFrame, threshold: float) -> str:
    """Whether one bar of delay is affordable.

    Args:
        table: What `delay.cost` returned on the strategy's own timeframe.
        threshold: The `dcr_high` of config.yaml.

    Returns:
        One key of MEANS, read on the first delay in the table.
    """
    return ("latency_fragile" if abs(table["DCR"].iloc[0]) >= threshold
            else "latency_robust")
