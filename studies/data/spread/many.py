"""Every strategy of one harvest repriced at the real spread, as one result and one panel."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.data.spread import one

MODULE = one.MODULE


def run(results: dict[str, dict], names: pd.Series, cfg: dict) -> dict:
    """The population panel, from each strategy's one.run() summary.

    Args:
        results: identity -> one.run()'s result.
        names: identity -> strategy name.
        cfg: inputs.config()'s dict.

    Returns:
        {"population": the result, "panel": one row per strategy with `verdict` —
        DESCARTAR only when the real spread breaks it and `reprice.action` is drop}.
    """
    started = time.time()
    panel = pd.DataFrame([{"identity": i, "strategy": names[i], **r["summary"]}
                          for i, r in results.items()]).set_index("strategy")
    panel = panel.sort_values(["verdict_state", "neto con slippage real [OOS]"]
                              if "neto con slippage real [OOS]" in panel else ["verdict_state"])
    broken = panel["verdict_state"] == "fail"
    panel["verdict"] = np.where(broken & (cfg["reprice"]["action"] == "drop"), "DESCARTAR", "MANTENER")
    samples = [s for s in ("IS", "OOS") if f"neto SQX [{s}]" in panel]
    judged = one.JUDGE[cfg["reprice"]["judge"]]
    counts = {s: {"ganaban": int((panel[f"neto SQX [{s}]"] > 0).sum()),
                  "siguen": int((panel[f"{judged} [{s}]"] > 0).sum())} for s in samples}
    won = {s: panel[panel[f"neto SQX [{s}]"] > 0] for s in samples}
    change = {s: 100 * (won[s][f"{judged} [{s}]"] / won[s][f"neto SQX [{s}]"] - 1).median()
              for s in samples}
    funnel = {"kind": "bars", "title": "Estrategias con neto positivo, antes y después", "unit": "",
              "reference": None,
              "items": [{"label": f"{s} {k}", "value": float(v), "error": None,
                         "state": "info" if k == "ganaban" else "pass"}
                        for s in samples for k, v in counts[s].items()]}
    shown = ["verdict", "broken"] + [c for s in samples for c in
                                     (f"neto SQX [{s}]", f"neto reajustado [{s}]", f"neto con slippage real [{s}]",
                                      f"PF con slippage real [{s}]",
                                      f"spread real medio (puntos) [{s}]", f"% con tick [{s}]")]
    table = blocks.table("Todas", panel[shown].reset_index(), "«broken» nombra el tramo donde "
                         "ganaba con el spread de SQX y deja de ganar con el real.")
    note = (f"{int(broken.sum())} de {len(panel)} se rompen con "
            f"{'el spread real' if cfg['reprice']['judge'] == 'spread' else 'el spread y el slippage reales'} — "
            + "; ".join(f"{s}: {counts[s]['ganaban']} ganaban, {counts[s]['siguen']} siguen, su neto "
                        f"cambia una mediana de {change[s]:+.0f} %" for s in samples)
            + f". {'Sólo se marcan' if cfg['reprice']['action'] == 'mark' else 'DESCARTAR en curate'}.")
    population = envelope.envelope(MODULE, None, None, cfg, started,
                                   [envelope.tab("panel", "Cada estrategia a spread real",
                                                 [funnel, table], note=note)],
                                   glossary=one.GLOSSARY)
    return {"population": population, "panel": panel}
