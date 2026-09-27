"""The steps of docs/AgentPDFs/WORKFLOW.md, each with where the disk says it happened."""

# One row per line of WORKFLOW.md's table, in its order (the half steps included: that file
# rules over any other count). `how` names the evidence `derive.py` reads for it:
#   template  — a template is linked to the project (runs.csv, projects/registry.csv, ledger)
#   preflight — `core.assetcheck` on the project's asset, today
#   project   — the project's folder in an install
#   sqx       — the tasks `sqx.projects.stage.titles(stage)` names, read from the install
#   study     — a contract result of any key in `studies`, under the data root
#   variants  — the mothers' batches in strategyPermutations/<project>/
#   blind     — step 20: the ledger's door, then the blindJoint result
# `studies` are study folder names (the catalogue's `key`); the first one gives the funnel.
STEPS = [
    {"n": "1", "title": "Idea en el chat", "kind": "person", "how": "template", "studies": []},
    {"n": "2", "title": "Vocabulario", "kind": "person", "how": "template", "studies": []},
    {"n": "3", "title": "Plantilla", "kind": "person", "how": "template", "studies": []},
    {"n": "4", "title": "Preflight", "kind": "python", "how": "preflight", "studies": []},
    {"n": "5", "title": "Custom project", "kind": "sqx", "how": "project", "studies": []},
    {"n": "6", "title": "Build", "kind": "sqx", "how": "sqx", "stage": "build", "studies": []},
    {"n": "7", "title": "Retest OOS", "kind": "sqx", "how": "sqx", "stage": "oos",
     "studies": []},
    {"n": "8", "title": "Análisis IS/OOS", "kind": "python", "how": "study",
     "studies": ["gate", "edgeCost", "snoopingScreen", "feedQuality", "spread"]},
    {"n": "9", "title": "Retest crossmarkets", "kind": "sqx", "how": "sqx",
     "stage": "crossmarket", "studies": []},
    {"n": "10", "title": "Análisis crossmarkets", "kind": "python", "how": "study",
     "studies": ["crossmarket"]},
    {"n": "10.5", "title": "Preparación crossTF", "kind": "sqx", "how": "bank",
     "bank": "CrossTF_Input", "studies": []},
    {"n": "11", "title": "Retest crossTF", "kind": "sqx", "how": "sqx", "stage": "crosstf",
     "studies": []},
    {"n": "12", "title": "Análisis crossTF", "kind": "python", "how": "study",
     "studies": ["crossTF"]},
    {"n": "13", "title": "MC Retest", "kind": "sqx", "how": "sqx", "stage": "mcretest",
     "studies": []},
    {"n": "14", "title": "Análisis MC Retest", "kind": "python", "how": "study",
     "studies": ["mcRetest"]},
    {"n": "15", "title": "SPP", "kind": "sqx", "how": "sqx", "stage": "spp", "studies": []},
    {"n": "16", "title": "Análisis SPP", "kind": "python", "how": "study", "studies": ["spp"]},
    {"n": "16.5", "title": "Variantes para el WFC", "kind": "sqx", "how": "variants",
     "stage": "wfc", "studies": []},
    {"n": "17", "title": "Walk Forward Correlation", "kind": "python", "how": "study",
     "studies": ["wfc"]},
    {"n": "18", "title": "CSCV", "kind": "python", "how": "study", "studies": ["cscv"]},
    {"n": "18.5", "title": "Superficies por mercado", "kind": "python", "how": "study",
     "studies": ["marketSurfaces"]},
    {"n": "19", "title": "Walk Forward Matrix", "kind": "sqx", "how": "sqx", "stage": "wfm",
     "studies": ["wfm"]},
    {"n": "20", "title": "Análisis conjunto (ciego)", "kind": "python", "how": "blind",
     "studies": ["blindJoint"]},
    {"n": "21", "title": "Exposición vs buy & hold", "kind": "python", "how": "study",
     "studies": ["exposure"]},
    {"n": "22", "title": "Mapa condicional", "kind": "python", "how": "study",
     "studies": ["conditionalMap"]},
    {"n": "23", "title": "Estructura", "kind": "python", "how": "study",
     "studies": ["structure"]},
    {"n": "24", "title": "Stop loss ATR", "kind": "python", "how": "study",
     "studies": ["atrCalculator"]},
    {"n": "25", "title": "Edge por coste, por estrategia", "kind": "python", "how": "study",
     "studies": ["edgeCost"], "only_strategy": True},
]

# Verdict words that mean the strategy is out. Anything else — MANTENER, INCONCLUSIVE, blind,
# a describing word — keeps it in the funnel's `out`; the `why` prints every word counted.
DROP = {"DESCARTAR", "FAIL", "fail", "reject", "dead", "not_worth_it"}

# Where a study's contract results live besides reports/<project>/<databank>/<day>/<key>/:
# the batches of a mother (WFC, CSCV, market surfaces), the structural and the stop batches.
BATCH_ROOTS = ("strategyPermutations", "structural", "atrCalculator")
