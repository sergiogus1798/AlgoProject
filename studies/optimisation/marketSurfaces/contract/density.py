"""One metric of every market overlaid as smooth densities, a series per market."""

import numpy as np
import pandas as pd

from core.study import blocks, result
from studies.optimisation.marketSurfaces.contract.tabs import selector, short

BINS = 240      # fine enough that the window's step outline reads as a curve
MIN_N = 10      # a market with fewer usable variants has no density worth drawing


def kde(values: np.ndarray, edges: np.ndarray) -> list[float]:
    """A Gaussian kernel density on the bins' centres, area 1 over the bins.

    Args:
        values: One metric per variant, finite.
        edges: The shared bin edges.

    Returns:
        One density per bin, Silverman's bandwidth (a constant sample gets a hundredth of the span).
    """
    v = np.asarray(values, dtype=float)
    spread = min(v.std(), np.subtract(*np.percentile(v, [75, 25])) / 1.34)
    h = 0.9 * spread * len(v) ** -0.2 if spread > 0 else (edges[-1] - edges[0]) / 100
    mid = (edges[1:] + edges[:-1]) / 2
    dens = np.exp(-0.5 * ((mid[:, None] - v[None, :]) / h) ** 2).sum(axis=1)
    return (dens / (dens.sum() * np.diff(edges))).tolist()


def tab(cells_by_metric: dict[str, pd.DataFrame], units: dict[str, str],
               segments: list[str], order: list[str], origin: str) -> dict:
    """One `distribution` per (metric, segment): every market's density, toggled in the window.

    Args:
        cells_by_metric: Metric label to `inputs.surfaces.long`, usable cells only.
        units: Metric label to its unit ("USD" or "").
        segments: The segments read.
        order: Market order, the main one first (so it is the first series, the first colour).
        origin: The mother's `variant_id`, marked as the main market's own line.

    Returns:
        The «superficies» tab, its blocks tagged with `segment` and `metric`.
    """
    out = []
    for metric, cells in cells_by_metric.items():
        for segment in segments:
            one = cells[cells["segment"] == segment]
            raw = {short(m): one.loc[one["market"] == m, "value"].to_numpy() for m in order}
            raw = {m: v[(v >= np.percentile(v, 0.5)) & (v <= np.percentile(v, 99.5))] if len(v)
                   else v for m, v in raw.items()}      # each market's own tails, not the union's
            raw = {m: v for m, v in raw.items() if len(v) >= MIN_N}
            if not raw:
                continue
            main = one.loc[(one["market"] == order[0]) & (one["variant_id"] == origin), "value"]
            reals = {short(order[0]): float(main.iloc[0])} if len(main) else None
            b = blocks.distribution(
                f"{metric} por mercado — {segment}", units[metric],
                np.concatenate(list(raw.values())), None,
                f"Una curva suave (densidad, área 1) por mercado: los {len(raw)} se comparan por "
                "su forma aunque tengan distinto número de variantes. La línea continua es la "
                "madre en el mercado principal; la discontinua, la mediana de cada mercado. "
                f"Enciende y apaga mercados con las casillas. Cada mercado se recorta "
                f"entre sus percentiles 0,5 y 99,5. No se dibuja un mercado con menos de {MIN_N} "
                f"variantes usables.",
                bins=BINS, series=raw, reals=reals)
            b.pop("share_positive", None)       # one figure for twelve markets would be the first's
            edges = np.asarray(b["bins"])
            for s, v in zip(b["series"], raw.values()):
                s["counts"] = kde(v[np.isfinite(v)], edges)
            b["help"] = ("La distribución de la métrica entre las variantes del lote en cada "
                         "mercado. Si la curva de un mercado se parece a la del principal, la "
                         "región de parámetros rinde de forma parecida; el nivel depende del coste.")
            out.append({**b, "select": {"segment": segment, "metric": metric}})
    return result.tab("superficies", "Una superficie por mercado", out,
                      [selector(segments), {"key": "metric", "label": "Métrica",
                                            "options": list(cells_by_metric),
                                            "default": next(iter(cells_by_metric))}],
                      "La superficie es la métrica de las variantes en cada mercado, todos "
                      "superpuestos. Su nivel depende del coste (provisional); lo que se "
                      "compara entre mercados es la forma y el orden, no el nivel.")
