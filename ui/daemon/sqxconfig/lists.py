"""The fixed vocabularies of the SQX settings, the ranges a number may take, and why a value is locked.

The SQX lists (precisions, engines, stop conditions) are HAND-COPIED constants, copied on
2026-09-27 from the install's own settings page `SQX/internal/web/RESULTS2/result2.js`
(`precisions`, `engineTypes`, `buildStopConditionTypes`). Nothing reads that file at run time:
a new SQX version that adds a value needs this module edited.
"""

PRECISIONS = [{"value": 1, "text": "1 · sólo el timeframe elegido (el más rápido)"},
              {"value": 2, "text": "2 · un minuto (lento)"},
              {"value": 3, "text": "3 · tick real, spread propio (el más lento)"},
              {"value": 4, "text": "4 · tick real, spread real (el más lento)"}]
# `MCBacktestPrecision` of a MC Retest task: _build.yaml documents exactly these two.
MC_PRECISIONS = PRECISIONS[:2]
ENGINES = ["MetaTrader4", "MetaTrader5 (netted)", "MetaTrader5 (hedged)", "Tradestation",
           "MultiCharts", "JForex", "Stockpicker", "Single-asset cloud strategy"]
STOP_CONDITIONS = ["databank-full", "passed-count", "time-limit", "never"]
# The <Block category="orderTypes"> keys of the frozen donor's Build task.
ORDER_TYPES = ["EnterAtMarket", "EnterAtStop", "EnterAtLimit", "EnterReverseAtMarket"]
# The cross-checks a task of the donor carries under <CrossChecks>.
CROSSCHECKS = ["RetestWithHigherPrecision", "RetestOnAdditionalMarkets", "MonteCarloManipulation",
               "MonteCarloRetest", "OptProfileSysParamPermutation", "SequentialOptimization",
               "WalkForwardOptimization", "WalkForwardMatrix", "WhatIf"]
# The <MoneyManagement><Method type=…> the donor's tasks carry. `tasksettings.set_money_management`
# switches on the one named here and fails on any other, so the list is the donor's, not SQX's.
MM_METHODS = ["ATRRiskBasedSizingFixedRisk", "ATRRiskBasedSizing", "FixedAmount", "FixedSize",
              "RiskFixedBalancePct", "RiskFixedPctOfAccount"]
# The four columns SQX computes pass by pass (subresult 33, knowhow/conditions/wfm-acceptance.md).
WF_SPECIAL = ["WFPctOfProfitableRuns", "WFMaxProfitByRunInPct", "WFMinTradesInRun",
              "WFMaxPctDDbyRun"]
# knowhow/costs/commission-methods.md
COMMISSIONS = ["None", "SizeBased", "PerTrade", "PercentageBased", "Stockpicker"]
SWAP_TYPES = ["points", "percent", "money"]
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
SPREADS = ["is", "oos", "oos2"]
# Titles and databank names the harvests look for by that exact spelling.
CONTRACT = {"title", "databank", "input"}
# _classes.yaml keys the code reads by name: core/assetdata.py `fields`/`sqx_settings`,
# core/assets.py (units), core/assetwrite.py `create`.
CLASS_CONTRACT = {"fields", "field", "unit"}

# (section, key) → (lowest, highest) a number may take; None is open. Only where the YAML's
# comment or the quantity itself fixes a bound: a percentage, a count, the WFM's 5 columns.
RANGES = {
    ("complexity", "max_entry_conditions"): (1, None), ("complexity", "max_exit_conditions"): (0, None),
    ("complexity", "lookback_bars"): (1, None),
    ("exits", "min_hours"): (0, None), ("exits", "max_hours"): (0, None),
    ("money_management", "max_drawdown"): (0, 100), ("money_management", "initial_capital"): (0, None),
    ("databank", "max_strategies"): (1, None),
    ("mc_retest", "simulations"): (1, None),
    ("mc_retest", "Probability"): (0, 100), ("mc_retest", "ProbabilityOpen"): (0, 100),
    ("mc_retest", "ProbabilityHigh"): (0, 100), ("mc_retest", "ProbabilityLow"): (0, 100),
    ("mc_retest", "ProbabilityClose"): (0, 100), ("mc_retest", "ProbabilityGapChange"): (0, 100),
    ("mc_retest", "MaxChange"): (0, None), ("mc_retest", "MaxChangeOfGap"): (0, None),
    ("mc_retest", "ATRPeriod"): (1, None),
    ("wfc", "min_trades_total"): (0, None),
    ("spp", "max_tests"): (1, 1000000000), ("spp", "spread_pct"): (1, 100), ("spp", "step_pct"): (1, 100),
    ("wfm", "max_tests"): (1, None), ("wfm", "distribution_pct"): (1, 100), ("wfm", "step_pct"): (1, 100),
    ("wfm", "threshold_pct"): (0, 100), ("wfm", "grid_passing_size"): (1, 5),
    ("wfm", "min_squares"): (0, 30),
}
# Numbers under these keys are percentages of OOS or counts of passes: WFM axes.
WFM_AXES = {"oos_pct": (1, 99), "runs": (1, None)}

LOCKED = {
    "contract": "Contrato con la cosecha de Python: cambiarlo rompe el análisis aguas abajo, "
                "en silencio. Se cambia en el YAML y en el código a la vez.",
    "fixed": "FIJO por decisión del dueño (2026-09-24): no es un mando. Otro valor sería otro "
             "estudio con el mismo nombre.",
    "conditions": "Cada condición es una estructura, no un valor: se edita en el YAML. Vacío "
                  "significa ninguna, por decisión del dueño (2026-09-24).",
    "sqx": "Un nombre o un hecho de SQX, no una decisión: sólo lectura.",
    "markets": "El universo de retest se decide en Activos; aquí sólo se consulta.",
    "classes": "Contrato con el código: core/assetdata.py, core/assets.py y core/assetwrite.py "
               "leen este campo por su nombre, y cada fichero de activo lleva estos campos. "
               "Cambiarlo aquí rompería todos los activos.",
}
# Values a study re-reads from _build.yaml when it analyses a run that already happened.
REREAD = ("Aviso: un run ya hecho se relee con este valor — {who} vuelve a leer _build.yaml al "
          "analizarlo, no guarda el que usó. Cámbialo entre runs, no después de uno "
          "(knowhow/eng/studies-reread-build-yaml.md, OPEN.md §80).")
