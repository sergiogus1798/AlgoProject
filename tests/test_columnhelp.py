#!/usr/bin/env python3
"""ui.text.columnhelp: every column the databank tables show today has its «?» sentence, every
raw study field a short header of at most 22 characters, and an unknown column gets None."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.text.columnhelp import help_for, label_for

METRICS = ("# of trades", "Max DD %", "Net profit", "Profit factor", "Ret/DD Ratio",
           "Sharpe Ratio", "Winning Percent", "Drawdown", "Annual % Return", "CAGR/Max DD %",
           "PSR", "TRL Ratio", "DoF Ratio", "Param Count", "Stability", "SQN", "ZScore")
PERCENTILES = ("80", "85", "90", "95", "97.5")
SIZINGS = ("one_lot", "avg_size", "equal_risk")
STATS = ("net", "return_pct", "cagr_pct", "maxdd_pct", "vol", "sharpe")

# (study, raw fields with a header of their own); every study also has "verdict".
FIELDS = {
    "atrCalculator": [f"{k}_p{p}" for p in PERCENTILES for k in
                      ("x", "zone", "unreliable", "high", "low", "effective_oos1",
                       "effective_oos2")] + ["n_winners_build", "n_winners_oos1",
                                             "n_winners_oos2"],
    "blindJoint": ["wfc", "cscv", "marketSurfaces", "wfm"],
    "cloud": ["legible", "live", "r2_adj", "r2_ref", "variants"],
    "crossTF": ["baseline", "control", "p", "reading", "seen", "trades"],
    "crossmarket": ["markets", "markets_valid", "invalid_fraction", "fixed_distance", "freq_off",
                    "freq_off_fraction", "z_conj", "p_conj", "z_conj_v2", "z_conj_v0", "z_conj_v1",
                    "z_minus_market", "minus_market", "p_breadth", "breadth_count", "tau_half",
                    "e_principal", "worse", "worse_fraction", "z_beta", "e_end", "beta",
                    "e_end_ratio", "net_t_pooled", "trades"],
    "cscv": ["score", "estado", "n", "p_perdida", "pbo", "pbo_p", "pbo_sobre_p95", "orden_estable",
             "beta", "r2", "hc", "duplicados_pct", "d01", "d02", "d03"],
    "wfc": ["composicion", "estado", "fuerte", "n", "nivel_top", "orden", "p_mas", "p_menos",
            "r_sel", "rho", "score", "p_nivel"],
    "edgeCost": ["edge_mean"],
    "exposure": ["aligned", "captured", "days", "dd_ratio", "efficiency", "equity_start",
                 "hours_off", "n", "reasons", "return_per_exposure_pct", "return_ratio",
                 "exp_avg_notional_pct", "exp_hours_per_week", "exp_notional_when_in_pct",
                 "exp_share", "exp_tilt"] + [f"lots_{s}" for s in SIZINGS]
                + [f"bench_{s}_{t}" for s in SIZINGS for t in STATS]
                + [f"strat_{t}" for t in STATS],
    "marketSurfaces": ["call", "declared", "estado", "markets", "oos2", "orden", "p_mas", "p_menos",
                       "peso", "prima", "prima_bajo_p5", "rho", "rho_auto", "segundos", "state",
                       "variants"],
    "mcRetest": ["binding", "blocked_by", "composite", "stress_cvar_dd_pct", "stress_net_p5",
                 "vetoes"],
    "wfm": ["area_celdas", "area_pasa", "asimetria", "celdas_efectivas", "centro_exceso_oos2",
            "deriva", "frac_celdas_positivas", "l1_mediana_exceso", "l1_p_mas", "l1_p_menos",
            "l2_delta", "l2_p_menos", "modo_real", "recobro_oos2", "sqx_failed", "why"],
}
VERDICT_ONLY = ("conditionalMap", "decay", "entryQuality", "feedQuality", "gate", "isOos",
                "monkey", "monteCarlo", "spp",
                "structure")


def test_every_metric_has_help() -> None:
    """Each metric, bare or with its sample suffix left on."""
    for name in METRICS:
        assert help_for("metric", "", name), name
        assert help_for("metric", "", f"{name} (OOS)") == help_for("metric", "", name), name


def test_every_study_column_has_help_and_a_short_label() -> None:
    """Every listed field explains itself, and every raw field has a header within 22."""
    for study in (*FIELDS, *VERDICT_ONLY):
        assert help_for("study", study, "verdict"), study
    for study, fields in FIELDS.items():
        for field in fields:
            assert help_for("study", study, field), (study, field)
            got = label_for(study, field)
            assert got and len(got) <= 22, (study, field, got)


def test_families_name_their_member() -> None:
    """A percentile or a sizing is said in the sentence, never a generic one."""
    assert "p97.5" in help_for("study", "atrCalculator", "x_p97.5")
    assert "oos2" in help_for("study", "atrCalculator", "effective_oos2_p90")
    assert "tamaño medio" in help_for("study", "exposure", "bench_avg_size_sharpe")
    assert label_for("exposure", "strat_sharpe") == "Sharpe estrategia"


def test_criteria_metrics_have_help_and_a_short_label() -> None:
    """Every criteria-metric column the four studies publish (owner, 2026-10-04)."""
    tokens = ("Net_Profit", "Profit_Factor", "Ret_DD", "Max_Drawdown", "Sharpe", "Sortino")
    columns = {
        "spp": [f"distancia_{u}_{s}_{t}" for u in ("pct", "IQR") for s in ("IS", "OOS1")
                for t in tokens] + [f"{k}_{t}" for k in ("decaimiento", "A", "Wasserstein")
                                    for t in ("Sharpe", "Sortino", "Profit_Factor", "R_Edge")],
        "wfc": [f"wfc.{c}.{k}" for c in ("c1", "c2", "c3")
                for k in ("rho", "p_mas", "p_menos", "nulo_p5", "nulo_p95", "nivel_top",
                          "p_nivel", "nivel_todas", "r_sel")],
        "mcRetest": ["percentil_original_estres", "brecha_mediana_pct_estres",
                     "distancia_IQR_estres"],
        "marketSurfaces": [f"{k}_{s}" for k in ("lift_Jaccard_mediano", "exceso_madre_en_top")
                           for s in ("build", "oos1", "oos2")]}
    for study, fields in columns.items():
        for field in fields:
            assert "Sin umbral" in help_for("study", study, field), (study, field)
            assert len(label_for(study, field)) <= 22, (study, field, label_for(study, field))
    assert label_for("spp", "distancia_IQR_OOS1_Net_Profit") == "ΔIQR OOS1 Net Profit"
    assert label_for("marketSurfaces", "lift_Jaccard_mediano_build") == "Lift Jaccard IS"


def test_unknown_column_is_none() -> None:
    """No guess for a column nobody described."""
    assert help_for("study", "wfm", "nonsense") is None
    assert help_for("metric", "", "Nonsense") is None
    assert label_for("exposure", "bench_x_net") is None


if __name__ == "__main__":
    test_every_metric_has_help()
    test_every_study_column_has_help_and_a_short_label()
    test_families_name_their_member()
    test_unknown_column_is_none()
    print("ok")
