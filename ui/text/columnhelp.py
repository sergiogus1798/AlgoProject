"""The «?» and the short header of every column the databank tables show: `help_for`, `label_for`.

`METRICS` (SQX metric → sentence) and `STUDY` ((study, field) → sentence) are the registries;
the per-percentile and per-sizing families are resolved by pattern (`columnhelp_closing`). A
field with no sentence returns None: an unknown column gets no «?» rather than a guess.
"""

import re

from ui.text.columnhelp_closing import ATR, BENCH, LOTS, STRAT, WINNERS, atr, exposure
from ui.text.columnhelp_fields import FIELDS
from ui.text.columnhelp_metrics import METRICS
from ui.text.columnhelp_verdicts import VERDICTS

STUDY = {**{(s, "verdict"): text for s, text in VERDICTS.items()}, **FIELDS}

# Short Spanish headers for the raw field names, at most 22 characters. The owner's technical
# words stay in English (Net Profit, Sharpe, PF, CAGR, OOS1…).
LABEL = {
    ("blindJoint", "wfc"): "WFC", ("blindJoint", "cscv"): "CSCV",
    ("blindJoint", "marketSurfaces"): "Superficies", ("blindJoint", "wfm"): "WFM",
    ("cloud", "point"): "Punto", ("cloud", "surface"): "Superficie",
    ("cloud", "temporal"): "Temporal", ("cloud", "variants"): "Variantes",
    ("cloud", "dropped"): "Descartadas", ("cloud", "r2"): "R² vecindad",
    ("cloud", "roughness"): "Rugosidad local", ("cloud", "gap"): "Sharpe madre − mezcla",
    ("cloud", "rho_median"): "ρ mediana por años", ("cloud", "drift_median"): "Deriva mediana",
    ("wfc", "score"): "ρ IS/OOS", ("cscv", "score"): "PBO",
    ("marketSurfaces", "call"): "Lectura", ("marketSurfaces", "state"): "Estado",
    ("marketSurfaces", "declared"): "Mercados declarados",
    ("marketSurfaces", "markets"): "Mercados en el lote",
    ("marketSurfaces", "variants"): "Variantes", ("marketSurfaces", "segments"): "Tramos",
    ("marketSurfaces", "costs_provisional"): "Costes provisionales",
    ("wfm", "rho"): "ρ", ("wfm", "low"): "ρ IC bajo", ("wfm", "high"): "ρ IC alto",
    ("wfm", "cells"): "Celdas", ("wfm", "steps"): "Tramos",
    ("wfm", "share_negative"): "Celdas con ρ < 0",
    ("wfm", "share_changed"): "Parámetros cambiados", ("wfm", "drift_high"): "Deriva alta",
    ("crossTF", "seen"): "Sharpe escalada", ("crossTF", "p"): "p",
    ("crossTF", "baseline"): "Sharpe madre", ("crossTF", "control"): "Sharpe control",
    ("crossTF", "reading"): "Lectura", ("crossTF", "trades"): "Operaciones",
    ("crossmarket", "reason"): "Motivo", ("crossmarket", "markets"): "Mercados",
    ("crossmarket", "cleared"): "Mercados superados", ("crossmarket", "fraction"): "Amplitud",
    ("crossmarket", "under_alpha"): "Calendar Shift p ≤ α",
    ("crossmarket", "paired_under_alpha"): "Timing Alpha p ≤ α",
    ("crossmarket", "edge_r"): "Ventaja (ATR)", ("crossmarket", "worst_pf"): "Peor PF",
    ("crossmarket", "median_pf"): "PF mediano", ("crossmarket", "pf_cv"): "STD del PF",
    ("edgeCost", "edge_mean"): "Edge medio (× coste)",
    ("edgeCost", "edge_median"): "Edge mediano (× coste)", ("edgeCost", "n"): "Operaciones",
    ("mcRetest", "composite"): "Compuesto", ("mcRetest", "binding"): "Lo que limita",
    ("mcRetest", "stress_net_p5"): "Net Profit p5 estrés",
    ("mcRetest", "stress_cvar_dd_pct"): "CVaR DD % estrés", ("mcRetest", "vetoes"): "Vetos",
    ("mcRetest", "blocked_by"): "Bloqueada por",
    ("exposure", "n"): "Operaciones", ("exposure", "days"): "Días",
    ("exposure", "equity_start"): "Saldo inicial", ("exposure", "exp_share"): "Exposición",
    ("exposure", "exp_hours_per_week"): "Horas dentro/semana",
    ("exposure", "exp_avg_notional_pct"): "Nocional medio %",
    ("exposure", "exp_notional_when_in_pct"): "Nocional dentro %",
    ("exposure", "exp_tilt"): "Sesgo largo/corto",
    ("exposure", "return_per_exposure_pct"): "Retorno por exposición",
    ("exposure", "efficiency"): "Eficiencia", ("exposure", "return_ratio"): "Retorno / B&H",
    ("exposure", "dd_ratio"): "DD / DD B&H", ("exposure", "hours_off"): "Horas fuera/semana",
    ("exposure", "captured"): "Movimiento capturado", ("exposure", "aligned"): "Alineado",
    ("exposure", "reasons"): "Motivos",
}

STAT_LABEL = {"net": "Net Profit", "return_pct": "Retorno %", "cagr_pct": "CAGR %",
              "maxdd_pct": "DD máx %", "vol": "Vol.", "sharpe": "Sharpe"}
SIZING_LABEL = {"one_lot": "B&H 1 lote", "avg_size": "B&H medio", "equal_risk": "B&H riesgo"}
ATR_LABEL = {"x": "X p{p}", "low": "X p{p} IC bajo", "high": "X p{p} IC alto",
             "unreliable": "X p{p} poco fiable", "zone": "Zona p{p}",
             "effective_oos1": "p efectivo OOS1 p{p}", "effective_oos2": "p efectivo OOS2 p{p}"}
WINNERS_LABEL = {"build": "Ganadoras IS", "oos1": "Ganadoras OOS1", "oos2": "Ganadoras OOS2"}
SAMPLE = re.compile(r" [(\[](IS|OOS|OOS1|OOS2|IS\+OOS1)[)\]]$")


def help_for(kind: str, study: str, field: str) -> str | None:
    """The «?» sentence of one databank column.

    Args:
        kind: "metric" or "study".
        study: The catalogue key; ignored for a metric.
        field: For a metric, its SQX name without the sample suffix («Net profit»; a suffix
            left on is dropped); for a study, the column's field, "verdict" for its verdict.

    Returns:
        One or two Spanish sentences, or None when the column has none.
    """
    if kind == "metric":
        return METRICS.get(SAMPLE.sub("", field))
    if (study, field) in STUDY:
        return STUDY[(study, field)]
    if study == "exposure":
        return exposure(field)
    if study == "atrCalculator":
        return atr(field)
    return None


def label_for(study: str, field: str) -> str | None:
    """The short Spanish header of one study column, or None to fall back on the glossary.

    Args:
        study: The catalogue key.
        field: The column's field as the study writes it.

    Returns:
        At most 22 characters.
    """
    if (study, field) in LABEL:
        return LABEL[(study, field)]
    if study == "exposure" and (got := BENCH.match(field)):
        return f"{STAT_LABEL[got[2]]} {SIZING_LABEL[got[1]]}"
    if study == "exposure" and (got := STRAT.match(field)):
        return f"{STAT_LABEL[got[1]]} estrategia"
    if study == "exposure" and (got := LOTS.match(field)):
        return f"Lotes {SIZING_LABEL[got[1]]}"
    if study == "atrCalculator" and (got := ATR.match(field)):
        return ATR_LABEL[got[1]].format(p=got[2])
    if study == "atrCalculator" and (got := WINNERS.match(field)):
        return WINNERS_LABEL[got[1]]
    return None
