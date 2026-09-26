"""One feed's quality report as the contract's data: counts by year and month, episodes, extremes."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.data.feedQuality import summary

MODULE = "feedQuality"
GLOSSARY = [
    {"term": "Escala", "text": "El movimiento M1 típico de esa hora de la semana: MAD × 1,4826 "
     "de los retornos de las 52 semanas anteriores, nunca por debajo de 3 ticks ni de 0,25 "
     "veces la mediana de las 120 horas de esa semana."},
    {"term": "Pico", "text": "Una vela cuyo cierre (o cuya mecha más allá del cuerpo) se mueve "
     "K veces la escala o más. K es propio de cada feed y está congelado en el ledger."},
    {"term": "Pico-y-vuelta", "text": "Un pico del que el precio deshace al menos el 80 % en "
     "3 minutos: la firma de un tick malo, y también la de un flash crash real."},
    {"term": "Movimiento extremo", "text": "Un pico que no vuelve: casi siempre una noticia. "
     "Se informa, pero no entra en la atribución."},
    {"term": "Congelado", "text": "10 velas M1 seguidas con O, H, L y C idénticos, en sesión y "
     "fuera de la franja 23:00–01:59 del feed."},
    {"term": "Hueco", "text": "5 minutos o más sin vela dentro de la sesión, fuera del rollover. "
     "Si todos los feeds de Dukascopy callan a la vez es caída del proveedor (5–179 min), "
     "cierre parcial (180 o más) o festivo (el día entero)."},
    {"term": "Año estable", "text": "El primero desde el que ningún año tiene más huecos "
     "marcados que max(3 × la mediana desde 2013, 30). Antes: calidad B hasta 10 × la "
     "mediana, inestable por encima."}]
SPIKE_COLUMNS = ["t", "size", "cls", "both"]


def _extremes(ev: pd.DataFrame, n: int) -> list[dict]:
    """The n most extreme events of each column, for the review by hand."""
    out = []
    for kind, title, cols in (("cierre", "cierre", SPIKE_COLUMNS), ("mecha", "mecha", SPIKE_COLUMNS),
                              ("congelado", "congelados", ["t", "size"]),
                              ("hueco", "huecos", ["t", "size", "cls"])):
        top = ev[ev["kind"] == kind].nlargest(n, "size")[cols].copy()
        top["t"] = top["t"].dt.strftime("%Y-%m-%d %H:%M")
        top = top.rename(columns={"t": "minuto (hora del feed)", "size": "tamaño",
                                  "cls": "clase", "both": "también en la otra columna"})
        out.append(blocks.table(f"Los {n} más extremos — {title}", top,
                                "Picos en múltiplos de la escala; congelados en velas; "
                                "huecos en minutos de sesión."))
    return out


def run(feed: str, ev: pd.DataFrame, facts: dict, cfg: dict) -> dict:
    """One feed's report.

    Args:
        feed: SQX symbol without the timeframe suffix.
        ev: Its events with gaps classified (detect.events + calendar.classify).
        facts: scan.facts()'s dict for the same feed.
        cfg: inputs.config()'s dict.

    Returns:
        The contract dict. It describes a feed and judges no strategy: the verdict block
        only says whether the feed is fit to build on, and from when.
    """
    started = time.time()
    yearly, monthly = summary.counts(ev, "Y"), summary.counts(ev, "M")
    session_ok = facts["residual_gaps_per_year"] <= cfg["gap"]["max_residual_per_year"]
    marked = [e for e in facts["episodes"] if e["columna"] in ("congelado", "hueco")]
    recent = [e for e in marked if int(e["mes"][:4]) >= (facts["stable_from"] or 0)]
    state = "pass" if session_ok and not recent else "watch"
    said = blocks.verdict(
        f"estable desde {facts['stable_from']}", state,
        f"K = {facts['K']}; {facts['marked_per_year']:g} anomalías marcadas por año (mediana "
        f"desde {cfg['stable']['base_year']}); huecos propios {facts['residual_gaps_per_year']:g} "
        f"al año ({'sesión bien deducida' if session_ok else 'por encima de 30: sesión MAL declarada'}); "
        f"{len(marked)} meses de episodio en congelados o huecos ({len(recent)} desde el año "
        f"estable) y {len(facts['episodes']) - len(marked)} en el rollover, que sólo se cuentan.",
        facts["marked_per_year"])
    per_year = yearly.reset_index(names="año")
    per_year["año"] = per_year["año"].astype(str)
    per_year["calidad"] = per_year["año"].map(facts["grade"])
    lines = {"kind": "lines", "title": "Anomalías marcadas por mes", "unit": "sucesos",
              "x": [str(m) for m in monthly.index],
              "series": [{"label": col, "values": monthly[col].tolist(), "role": "real"}
                         for col in summary.MARKED]}
    episodes = blocks.table("Meses de episodio", pd.DataFrame(facts["episodes"]),
                            "Un mes es episodio si sus congelados o sus huecos superan 5 veces "
                            "la mediana de los 36 meses anteriores, con al menos 5 sucesos.")
    k_table = blocks.table("Cómo se eligió K", pd.DataFrame(
        [{"K": k, "mediana de picos al año, años tranquilos": v}
         for k, v in facts["quiet_medians"].items()]),
        f"K* = el menor con menos de {cfg['k']['max_per_year']} picos de cierre al año "
        f"(mediana {cfg['k']['quiet_years'][0]}–{cfg['k']['quiet_years'][1]}).")
    tabs = [envelope.tab("years", "Por año", [blocks.table("Recuento por año", per_year,
                         "«marcadas» suma lo que la atribución del paso 8 lee.")]),
            envelope.tab("months", "Por mes", [lines, episodes]),
            envelope.tab("extremes", "Los más extremos", _extremes(ev, cfg["review"]["extreme_per_column"]),
                         note="Para revisarlos a mano contra la historia: la inyección mide qué "
                              "se escapa, esto mide si marca tonterías."),
            envelope.tab("calibration", "Calibración", [k_table, blocks.table(
                "Sesión y tick", pd.DataFrame([{"sesión deducida": facts["session"],
                                                "tick del feed": facts["tick"]}]))])]
    return envelope.envelope(MODULE, None, None, cfg, started, tabs, said, glossary=GLOSSARY,
                             summary={"feed": feed, "K": facts["K"],
                                      "stable_from": facts["stable_from"],
                                      "marked_per_year": facts["marked_per_year"]})
