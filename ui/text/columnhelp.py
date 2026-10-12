"""The «?» and the short header of every column the databank tables show: `help_for`, `label_for`.

`METRICS` (SQX metric → sentence) and `STUDY` ((study, field) → sentence) are the registries;
the per-percentile and per-sizing families are resolved by pattern (`columnhelp_closing`). A
field with no sentence returns None: an unknown column gets no «?» rather than a guess.
"""

import re

from ui.text.columnhelp_closing import BENCH, LOTS, STRAT, exposure
from ui.text.columnhelp_criteria import criteria
from ui.text.columnhelp_fields import FIELDS
from ui.text.columnhelp_metrics import METRICS
from ui.text.columnhelp_steps import STEPS
from ui.text.columnhelp_tf import TF
from ui.text.columnhelp_verdicts import VERDICTS

STUDY = {**{(s, "verdict"): text for s, text in VERDICTS.items()}, **FIELDS, **STEPS,
         **{("crossTF", k): v[1] for k, v in TF.items()}}

# Short Spanish headers for the raw field names, at most 22 characters. The owner's technical
# words stay in English (Net Profit, Sharpe, PF, CAGR, OOS1…).
LABEL = {
    ("blindJoint", "wfc"): "WFC", ("blindJoint", "cscv"): "CSCV",
    ("blindJoint", "marketSurfaces"): "Superficies", ("blindJoint", "wfm"): "WFM",
    ("cloud", "variants"): "Variantes", ("cloud", "live"): "Parámetros vivos",
    ("cloud", "r2_adj"): "R² ajustado", ("cloud", "r2_ref"): "R² del ruido",
    ("cloud", "legible"): "Legible",
    ("wfc", "composicion"): "Composición", ("wfc", "estado"): "Estado", ("wfc", "orden"): "Orden",
    ("wfc", "fuerte"): "Fuerte", ("wfc", "n"): "Variantes", ("wfc", "rho"): "ρ de Spearman",
    ("wfc", "p_mas"): "p+", ("wfc", "p_menos"): "p−", ("wfc", "nivel_top"): "Nivel del top",
    ("wfc", "r_sel"): "R_sel",
    ("wfc", "score"): "ρ de Spearman", ("cscv", "score"): "PBO",
    ("wfc", "p_nivel"): "p del nivel", ("wfc", "fines_de_semana"): "Cierres tras finde",
    ("wfc", "orden_bloque"): "Orden a 2 semanas", ("wfc", "descuadre_sqx"): "Descuadre con SQX",
    ("cscv", "estado"): "Estado", ("cscv", "n"): "Variantes", ("cscv", "p_perdida"): "P de pérdida",
    ("cscv", "pbo"): "PBO", ("cscv", "pbo_p"): "p del PBO", ("cscv", "pbo_sobre_p95"): "PBO sobre p95",
    ("cscv", "orden_estable"): "Orden estable", ("cscv", "beta"): "β de degradación",
    ("cscv", "r2"): "R² ajustado", ("cscv", "hc"): "Recorte del Sharpe",
    ("cscv", "duplicados_pct"): "Duplicados %", ("cscv", "d01"): "Potencia Sharpe 0,1",
    ("cscv", "d02"): "Potencia Sharpe 0,2", ("cscv", "d03"): "Potencia Sharpe 0,3",
    ("marketSurfaces", "call"): "Lectura", ("marketSurfaces", "state"): "Estado",
    ("marketSurfaces", "estado"): "Estado (palabra)", ("marketSurfaces", "orden"): "Orden",
    ("marketSurfaces", "rho"): "ρ de Spearman", ("marketSurfaces", "p_mas"): "p+",
    ("marketSurfaces", "p_menos"): "p−", ("marketSurfaces", "peso"): "Peso de mercados",
    ("marketSurfaces", "prima"): "Prima del top",
    ("marketSurfaces", "prima_bajo_p5"): "Prima bajo p5", ("marketSurfaces", "rho_auto"): "ρ del principal",
    ("marketSurfaces", "oos2"): "Leído en oos2", ("marketSurfaces", "segundos"): "Segundos",
    ("marketSurfaces", "declared"): "Mercados declarados",
    ("marketSurfaces", "markets"): "Mercados en la media",
    ("marketSurfaces", "variants"): "Variantes",
    ("wfm", "why"): "Por qué", ("wfm", "modo_real"): "Modo real",
    ("wfm", "l1_mediana_exceso"): "L1 mediana exceso", ("wfm", "l1_p_mas"): "L1 p+",
    ("wfm", "l1_p_menos"): "L1 p−", ("wfm", "l2_delta"): "L2 delta", ("wfm", "l2_p_menos"): "L2 p−",
    ("wfm", "centro_exceso_oos2"): "Exceso celda central",
    ("wfm", "celdas_efectivas"): "Celdas efectivas",
    ("wfm", "frac_celdas_positivas"): "Celdas positivas",
    ("wfm", "deriva"): "Deriva", ("wfm", "area_celdas"): "Celdas del área",
    ("wfm", "area_pasa"): "Área de SQX", ("wfm", "asimetria"): "Asimetría semanal",
    ("wfm", "recobro_oos2"): "Recobro en oos2", ("wfm", "sqx_failed"): "Marcada por SQX",
    ("crossTF", "seen"): "Sharpe escalada", ("crossTF", "p"): "p",
    ("crossTF", "baseline"): "Sharpe madre", ("crossTF", "control"): "Sharpe control",
    ("crossTF", "reading"): "Lectura", ("crossTF", "trades"): "Operaciones",
    ("crossmarket", "markets"): "Mercados",
    ("crossmarket", "markets_valid"): "Mercados válidos",
    ("crossmarket", "invalid_fraction"): "Fracción no válida",
    ("crossmarket", "fixed_distance"): "P1 · Dist. fijas",
    ("crossmarket", "freq_off"): "P2 · Frec. distinta",
    ("crossmarket", "freq_off_fraction"): "P2 · Fracción frec.",
    ("crossmarket", "z_conj"): "P3 · z conjunta",
    ("crossmarket", "p_conj"): "P3 · p conjunta",
    ("crossmarket", "z_conj_v2"): "P4 · z en V2",
    ("crossmarket", "z_conj_v0"): "z en V0",
    ("crossmarket", "z_conj_v1"): "z en V1",
    ("crossmarket", "z_minus_market"): "P5 · z sin un mercado",
    ("crossmarket", "minus_market"): "Mercado quitado",
    ("crossmarket", "p_breadth"): "P6 · p amplitud",
    ("crossmarket", "breadth_count"): "Mercados a favor",
    ("crossmarket", "tau_half"): "P7 · τ en la mitad",
    ("crossmarket", "e_principal"): "Ventaja del principal",
    ("crossmarket", "worse"): "P8 · En contra",
    ("crossmarket", "worse_fraction"): "P8 · Fracción contra",
    ("crossmarket", "z_beta"): "P9 · z pendiente",
    ("crossmarket", "e_end"): "P9 · Ventaja final",
    ("crossmarket", "beta"): "Pendiente por año",
    ("crossmarket", "e_end_ratio"): "Ventaja final / media",
    ("crossmarket", "net_t_pooled"): "t conjunta (neto)",
    ("crossmarket", "trades"): "Operaciones",
    ("edgeCost", "edge_mean"): "Edge medio (× coste)",
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
    ("exposure", "notes"): "Avisos",
}

STAT_LABEL = {"net": "Net Profit", "return_pct": "Retorno %", "cagr_pct": "CAGR %",
              "maxdd_pct": "DD máx %", "vol": "Vol.", "sharpe": "Sharpe"}
SIZING_LABEL = {"one_lot": "B&H 1 lote", "avg_size": "B&H medio", "equal_risk": "B&H riesgo"}
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
    if got := criteria(study, field):
        return got[1]
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
    if study == "crossTF" and field in TF:
        return TF[field][0]
    if study == "exposure" and (got := BENCH.match(field)):
        return f"{STAT_LABEL[got[2]]} {SIZING_LABEL[got[1]]}"
    if study == "exposure" and (got := STRAT.match(field)):
        return f"{STAT_LABEL[got[1]]} estrategia"
    if study == "exposure" and (got := LOTS.match(field)):
        return f"Lotes {SIZING_LABEL[got[1]]}"
    if got := criteria(study, field):
        return got[0]
    return None
