"""The steps of docs/AgentPDFs/WORKFLOW.md: where the disk says each happened, its tests and its tab."""

# One row per line of WORKFLOW.md's table, in its order (the half steps included: that file
# rules over any other count). `doc` is the bold title of that row, word for word:
# tools/checks.py fails when the numbers or these titles drift from the table. `title` is the
# short name the rail's card prints. `how` names the evidence `derive.py` reads for it:
#   template  — a template is linked to the project (runs.csv, projects/registry.csv, ledger)
#   preflight — `core.assetcheck` on the project's asset, today
#   project   — the project's folder in an install
#   sqx       — the tasks `sqx.projects.stage.titles(stage)` names, read from the install
#   study     — a contract result of any key in `studies`, under the data root
#   variants  — the mothers' batches in strategyPermutations/<project>/
#   blind     — step 20: the ledger's door, then the blindJoint result
# `studies` are study folder names (the catalogue's `key`); the first one gives the funnel.
# `tab`/`sub` are the databank panel's tab and sub-panel where the result is read (the mock's
# PANELS, encargo 22 §4.3), '' for none and for the tab's first sub-panel. `feeds` are the
# stages whose output databanks the step's tests read, "batch" for a mother's variant batch,
# () for the databank the panel shows. `extra` are tests offered on the step that prove
# nothing about it: the readings outside the sequence, run on the retest's population.
# `S` holds literals only: tools/checks.py reads it with ast.literal_eval, without importing.
S = [
    ("1", "Idea en el chat", "Idea en el chat", "person", "template", [], "", "", ()),
    ("2", "Vocabulario", "Vocabulario", "person", "template", [], "", "", ()),
    ("3", "Plantilla", "Plantilla", "person", "template", [], "", "", ()),
    ("4", "Preflight", "Preflight", "python", "preflight", [], "", "", ()),
    ("5", "Custom project", "Creación del custom project", "sqx", "project", [], "", "", ()),
    ("6", "Build", "Configuración del build", "sqx", "sqx", [], "Puerta IS/OOS", "", ()),
    ("7", "Retest OOS", "Retest OOS en SQX", "sqx", "sqx", [], "Puerta IS/OOS", "", ()),
    ("8", "Análisis IS/OOS", "Análisis IS/OOS en Python", "python", "study",
     ["gate", "edgeCost", "snoopingScreen", "feedQuality", "spread"], "Puerta IS/OOS", "",
     ("oos", "build")),
    ("9", "Retest crossmarkets", "Retest crossmarkets en SQX", "sqx", "sqx", [],
     "Cross Market", "", ()),
    ("10", "Análisis crossmarkets", "Análisis crossmarkets en Python", "python", "study",
     ["crossmarket"], "Cross Market", "", ("crossmarket",)),
    ("10.5", "Preparación crossTF", "Preparación crossTF", "sqx", "bank", [],
     "Cross Timeframe", "", ()),
    ("11", "Retest crossTF", "Retest crossTimeframes en SQX", "sqx", "sqx", [],
     "Cross Timeframe", "", ()),
    ("12", "Análisis crossTF", "Análisis crossTFs en Python", "python", "study", ["crossTF"],
     "Cross Timeframe", "", ("crosstf",)),
    ("13", "MC Retest", "MC Retest en SQX", "sqx", "sqx", [], "MC Retest", "", ()),
    ("14", "Análisis MC Retest", "Análisis MC Retest en Python", "python", "study",
     ["mcRetest"], "MC Retest", "", ("mcretest",)),
    ("15", "SPP", "SPPs en SQX", "sqx", "sqx", [], "SPP", "", ()),
    ("16", "Análisis SPP", "Análisis SPPs en Python", "python", "study", ["spp"], "SPP", "",
     ("spp",)),
    ("16.5", "Variantes para el WFC", "Preparación de variantes para el WFC", "sqx",
     "variants", [], "WFC", "", "batch"),
    ("17", "Walk Forward Correlation", "Walk Forward Correlation", "python", "study", ["wfc"],
     "WFC", "", "batch"),
    ("18", "CSCV", "CSCV", "python", "study", ["cscv"], "CSCV", "", "batch"),
    ("18.5", "Superficies por mercado", "Superficies por mercado", "python", "study",
     ["marketSurfaces"], "Market Surfaces", "", "batch"),
    ("19", "Walk Forward Matrix", "Walk Forward Matrix en SQX", "sqx", "sqx", ["wfm"], "WFM",
     "", ("wfm",)),
    ("20", "Análisis conjunto (ciego)",
     "Análisis conjunto de 17, 18, 18.5 y 19 — CIEGO hasta tener los cuatro", "python",
     "blind", ["blindJoint"], "Cierre", "Análisis conjunto (paso 20)", ("wfm",)),
    ("21", "Exposición vs buy & hold", "Exposición contra el buy and hold", "python", "study",
     ["exposure"], "Cierre", "Exposición", ()),
    ("22", "Mapa condicional", "Mapa condicional", "python", "study", ["conditionalMap"],
     "Cierre", "Mapa condicional", ()),
    ("23", "Estructura", "Estructura", "python", "study", ["structure"], "Cierre",
     "Estructura", ()),
    ("24", "Stop loss ATR", "El stop loss para MT5", "python", "study", ["atrCalculator"],
     "Cierre", "Stop ATR", ()),
    ("25", "Edge por coste, por estrategia", "Edge por coste, por estrategia", "python",
     "study", ["edgeCost"], "Cierre", "Edge por coste", ()),
    ("26", "Validación MT5", "Validación en MT5 con la feed de cada empresa de fondeo → pool validado",
     "python", "study", ["mt5Validation"], "Cierre", "", ()),
]
# The SQX stage each SQX step reads its tasks from (`sqx.projects.stage.titles`).
STAGE = {"6": "build", "7": "oos", "9": "crossmarket", "11": "crosstf", "13": "mcretest",
         "15": "spp", "16.5": "wfc", "19": "wfm"}
EXTRA = {"8": ["monkey", "profitShape", "entryQuality"]}
KEYS = ("n", "title", "doc", "kind", "how", "studies", "tab", "sub", "feeds")
STEPS = [dict(zip(KEYS, row)) | ({"stage": STAGE[row[0]]} if row[0] in STAGE else {})
         | ({"bank": "CrossTF_Input"} if row[0] == "10.5" else {})
         | ({"only_strategy": True} if row[0] == "25" else {})
         | {"extra": EXTRA.get(row[0], [])} for row in S]

# Verdict words that mean the strategy is out. Anything else — MANTENER, INCONCLUSIVE, blind,
# a describing word — keeps it in the funnel's `out`; the `why` prints every word counted.
DROP = {"DESCARTAR", "FAIL", "fail", "reject", "dead", "not_worth_it"}

# Where a study's contract results live besides reports/<project>/<databank>/<day>/<key>/:
# the batches of a mother (WFC, CSCV, market surfaces), the structural and the stop batches.
BATCH_ROOTS = ("strategyPermutations", "structural", "atrCalculator")
