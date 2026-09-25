"""The report: every reading as a table, in the order the argument is made."""

import numpy as np
import pandas as pd

from strategies.parameterCloud.verdict import call


def header(data: dict, cut: int, collapsed: list[str]) -> str:
    """What was read, what was left out, and where the history was stopped.

    Args:
        data: What `inputs.cloud.cloud` returned.
        cut: Days removed for falling inside the reserved segment.
        collapsed: Parameters left with one value by the study's own filters.

    Returns:
        Three lines. The collapsed parameters are named first because they are a finding:
        a parameter the filters flattened chooses between trading and not trading, which
        no sensitivity index would have told you.
    """
    lines = [f"{len(data['frame'])} variantes sobre {data['metric']}, "
             f"{data['dropped']} descartadas (canarios y pocas operaciones); "
             f"origen {data['origin']}"]
    if collapsed:
        lines.append("! colapsados por los filtros, fuera del modelo: "
                     + ", ".join(c[6:] for c in collapsed))
    if cut:
        lines.append(f"! {cut} días recortados: caen en el tramo reservado")
    return "\n".join(lines)


def point(reading: dict, verdict: str) -> str:
    """A1: where theta-zero sits, in its neighbourhood and in the cloud.

    Args:
        reading: What `neighbourhood.reading` returned.
        verdict: What `verdict.call.point` returned.

    Returns:
        A two-row table plus the reading. `shrunk` is the number to carry downstream.
    """
    frame = pd.DataFrame({k: reading[k] for k in ("near", "cloud")}).T
    frame.columns = ["n", "q (rango)", f"pi ({reading['delta']:.0%})", "M_shrunk"]
    return (f"original {reading['original']:.3f}\n"
            + frame.round(3).to_string() + f"\n-> {verdict}: {call.MEANS[verdict]}")


def sensitivity(names: list[str], indices: dict, model: dict, rough: float,
                curve: dict, calls: list[str]) -> str:
    """A2 and A3: who moves the result, and whether the surface is a surface.

    Args:
        names: The parameters the model was fitted on.
        indices: What `sensitivity.sobol` returned.
        model: What `surrogate.fit` returned on the neighbourhood.
        rough: What `surrogate.local_roughness` returned.
        curve: What `surrogate.curvature` returned.
        calls: What `verdict.call.surface` returned.

    Returns:
        The Sobol table sorted by total index, then the three shape numbers. A total index
        far above the first-order one is interaction, which is the shape of tuned logic.
    """
    table = pd.DataFrame({"parámetro": [n[6:] for n in names],
                          "S": indices["first"], "S_total": indices["total"]})
    lines = [table.sort_values("S_total", ascending=False).round(3).to_string(index=False),
             f"suavidad r2 {model['r2']:.3f} · rugosidad residual "
             f"{model['roughness']:.3f} · desacuerdo entre vecinos {rough:.3f} IQR",
             f"curvatura en el origen: pendiente {curve['slope']:.2f}, autovalores "
             f"{np.array2string(curve['eigenvalues'], precision=1)}"]
    return "\n".join(lines + [f"-> {c}: {call.MEANS[c]}" for c in calls if c in call.MEANS])


def stability(table: pd.DataFrame, rho: pd.Series, drift: pd.Series,
              calls: list[str]) -> str:
    """B2: the per-period picture, period by period.

    Args:
        table: Periods down, with f_y, the origin's rank and the active days.
        rho: What `stability.persistence` returned.
        drift: What `stability.centroids` returned.
        calls: What `verdict.call.temporal` returned.

    Returns:
        One row per period, then the two medians the reading is taken on.
    """
    joined = table.join(rho.rename("rho_siguiente")).join(drift.rename("deriva"))
    return "\n".join([joined.round(3).to_string(),
                      f"mediana rho {np.median(rho):+.3f} · mediana deriva "
                      f"{np.median(drift):.3f} · peor periodo f_y {table['f_y'].min():.3f}"]
                     + [f"-> {c}: {call.MEANS[c]}" for c in calls])


def ensemble(result: dict, pool: int) -> str:
    """C1: the blend against the single point.

    Args:
        result: What `ensemble.blend` returned.
        pool: How many variants the plateau held.

    Returns:
        Two rows and the gap. A wide gap in favour of the single point is overfit
        measured, not an argument for keeping it.
    """
    frame = pd.DataFrame({"punto único": result["single"], "mezcla": result["blended"]}).T
    return (f"meseta {pool} variantes, {result['k']} con curva, a 1/{result['k']} del riesgo\n"
            + frame.round(3).to_string()
            + f"\ndiferencia de Sharpe {result['gap']:+.3f}")
