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
    "cloud": ["drift_median", "dropped", "gap", "point", "r2", "rho_median", "roughness",
              "surface", "temporal", "variants"],
    "crossTF": ["baseline", "control", "p", "reading", "seen", "trades"],
    "crossmarket": ["cleared", "edge_r", "fraction", "markets", "median_pf",
                    "paired_under_alpha", "pf_cv", "reason", "under_alpha", "worst_pf"],
    "cscv": ["score"], "wfc": ["score"],
    "edgeCost": ["edge_mean", "edge_median", "n"],
    "exposure": ["aligned", "captured", "days", "dd_ratio", "efficiency", "equity_start",
                 "hours_off", "n", "reasons", "return_per_exposure_pct", "return_ratio",
                 "exp_avg_notional_pct", "exp_hours_per_week", "exp_notional_when_in_pct",
                 "exp_share", "exp_tilt"] + [f"lots_{s}" for s in SIZINGS]
                + [f"bench_{s}_{t}" for s in SIZINGS for t in STATS]
                + [f"strat_{t}" for t in STATS],
    "marketSurfaces": ["call", "costs_provisional", "declared", "markets", "segments", "state",
                       "variants"],
    "mcRetest": ["binding", "blocked_by", "composite", "stress_cvar_dd_pct", "stress_net_p5",
                 "vetoes"],
    "wfm": ["cells", "drift_high", "high", "low", "rho", "share_changed", "share_negative",
            "steps"],
}
VERDICT_ONLY = ("conditionalMap", "decay", "entryQuality", "feedQuality", "gate", "isOos",
                "monkey", "monteCarlo", "profitShape", "snoopingScreen", "spp", "spread",
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
