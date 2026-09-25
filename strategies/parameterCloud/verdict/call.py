"""What the numbers mean, against thresholds that are set before the cloud is read."""

import numpy as np
import pandas as pd

MEANS = {
    "spike": "el punto elegido está en un pico: casi nada a su alrededor se le acerca",
    "plateau": "el punto elegido tiene compañía: su vecindad rinde parecido",
    "middling": "el punto elegido no destaca en su propia nube",
    "smooth": "la superficie es una función suave de los parámetros",
    "rough": "vecinos inmediatos discrepan: buena parte del resultado es el sorteo",
    "off_centre": "el óptimo del modelo suave no está donde se sitúa la estrategia",
    "persistent": "el orden entre variantes sobrevive de un periodo al siguiente",
    "reshuffled": "la superficie se rebaraja cada periodo: optimizarla es optimizar ruido",
    "carried": "hay periodos que sostienen el resultado y otros en los que la familia entera pierde",
    "broad": "la familia gana en casi todos los periodos",
    "drift_high": "la región buena se desplaza: reoptimizar la persigue en vez de encontrarla",
    "drift_low": "la región buena se queda donde estaba de un periodo al siguiente",
}


def point(reading: dict, cfg: dict) -> str:
    """A1's reading: noise peak, plateau, or unremarkable.

    Args:
        reading: What `neighbourhood.reading` returned.
        cfg: The `verdict` block of config.yaml.

    Returns:
        One key of MEANS. The rank alone decides nothing: a rank near 1 with company is a
        plateau and is the shape you want, and the same rank alone is a peak.
    """
    near = reading["near"]
    if near["q"] < cfg["rank_high"]:
        return "middling"
    return "spike" if near["pi"] <= cfg["plateau_low"] else "plateau"


def surface(model: dict, rough: float, curve: dict, cfg: dict) -> list[str]:
    """A3's reading: how much of the surface is shape and how much is draw.

    Args:
        model: What `surrogate.fit` returned on the neighbourhood.
        rough: What `surrogate.local_roughness` returned.
        curve: What `surrogate.curvature` returned at the origin.
        cfg: The `verdict` block of config.yaml.

    Returns:
        One or two keys of MEANS. Roughness is read on the model-free measure and the
        residual one at once: a quadratic calls every ridge it cannot represent noise, so
        agreeing is what licenses the word.
    """
    calls = ["rough" if model["roughness"] >= cfg["roughness_high"]
             or rough >= cfg["local_roughness_high"] else "smooth"]
    if curve["slope"] >= cfg["slope_high"]:
        calls.append("off_centre")
    return calls


def temporal(fraction: pd.Series, rho: pd.Series, drift: pd.Series,
             cfg: dict) -> list[str]:
    """B2's reading: whether the surface holds its shape period by period.

    Args:
        fraction: f_y, what `stability.fractions` returned.
        rho: What `stability.persistence` returned.
        drift: d_y, what `stability.centroids` returned.
        cfg: The `verdict` block of config.yaml.

    Returns:
        Three keys of MEANS: one about level, one about order, one about where the good
        region sat. They fail independently:
        a family can make money in every period while its internal ranking is noise, and
        that combination is precisely the one that makes in-sample tuning pointless and
        the strategy itself fine.
    """
    order = "persistent" if float(np.median(rho)) >= cfg["rho_low"] else "reshuffled"
    level = "broad" if float(fraction.min()) >= cfg["fraction_low"] else "carried"
    wander = "drift_high" if float(np.median(drift)) >= cfg["drift_high"] else "drift_low"
    return [level, order, wander]
