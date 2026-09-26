"""Every strategy of one harvest against its feed's anomalies, as one result and one panel."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.data.feedQuality import alarm, one

MODULE = one.MODULE


def run(results: dict[str, dict], names: pd.Series, unread: list[str], cfg: dict) -> dict:
    """The population panel, from each strategy's one.run() summary.

    Args:
        results: identity -> one.run()'s result.
        names: identity -> strategy name.
        unread: Names whose .sqx no install holds: their order type is unknown, so they are
            not judged, and say so.
        cfg: inputs.config()'s dict.

    Returns:
        {"population": the result, "panel": one row per strategy with `verdict`
        (MANTENER, or DESCARTAR only when the alarm fires and `action` is drop — decision
        14: never an automatic drop)}.
    """
    started = time.time()
    rows = [{"identity": i, "strategy": names[i], **r["summary"]} for i, r in results.items()]
    rows += [{"identity": None, "strategy": n, "alarm": "sin .sqx"} for n in unread]
    panel = pd.DataFrame(rows).set_index("strategy").sort_values("at_risk", ascending=False)
    fired = panel["alarm"] == alarm.ALARM
    panel["verdict"] = np.where(fired & (cfg["alarm"]["action"] == "drop"), "DESCARTAR", "MANTENER")
    counts = panel["alarm"].value_counts()
    bars = {"kind": "bars", "title": "% del beneficio en riesgo por estrategia", "unit": "%",
            "reference": None,
            "items": [{"label": s, "value": float(100 * v) if v == v and v is not None else 0.0,
                       "error": None, "state": one.STATE.get(a, "none")}
                      for s, v, a in zip(panel.index, panel["at_risk"], panel["alarm"])]}
    table = blocks.table("Todas", panel.reset_index(), "p del test de permutación, IS y OOS "
                         "juntas; «insuficiente» con menos de 10 operaciones marcadas.")
    note = (f"{counts.get(alarm.ALARM, 0)} con alarma, {counts.get(alarm.QUIET, 0)} sin alarma, "
            f"{counts.get(alarm.SHORT, 0)} insuficientes, {len(unread)} sin .sqx — "
            f"{'sólo se marcan' if cfg['alarm']['action'] == 'mark' else 'DESCARTAR en curate'}. "
            "Con p < 0,01 saltará por azar en torno al 1 % de las estrategias.")
    population = envelope.envelope(MODULE, None, None, cfg, started,
                                   [envelope.tab("panel", "Cada estrategia contra su feed",
                                                 [bars, table], note=note)],
                                   glossary=one.GLOSSARY)
    return {"population": population, "panel": panel}
