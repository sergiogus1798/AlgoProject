"""The study files behind the WFC and the CSCV, shown beside _build.yaml's `wfc` and in a CSCV section.

Owner, 2026-09-28: every input of both steps is seen and edited here, not only the SQX tasks
`_build.yaml` declares — the batch each mother gets (the SPP design's cap and the factory's floor),
the factory's seed and grids, the canaries, the trade floor and split the two studies share, each
study's own knobs, and the CSCV's blocks, which live in the ledger's frozen thresholds and are
stamped with who and when on every write (`studywrite.py`).
"""

from typing import Any
from functools import lru_cache
from math import comb
from pathlib import Path

from core.assetyaml import leaves, read
from core.paths import ROOT
from engines.variants.panel import SHORTCUTS
from sqx.variants.tooltips import TIPS as FACTORY_TIPS
from studies.breakage.spp.tooltips import TIPS as SPP_TIPS
from studies.optimisation.cscv.tooltips import TIPS as CSCV_TIPS
from studies.optimisation.cloud.tooltips import TIPS as CLOUD_TIPS
from studies.optimisation.marketSurfaces.tooltips import TIPS as SURF_TIPS
from studies.optimisation.wfc.tooltips import TIPS as WFC_TIPS
from studies.optimisation.wfm.tooltips import TIPS as WFM_TIPS
from studies.screening.analysis.tradelevel import WINDOWS
from studies.screening.falsePositives.tooltips import TIPS as FP_TIPS
from studies.screening.gate.tooltips import TIPS as GATE_TIPS
from ui.daemon.sqxconfig.options import choice
from ui.daemon.sqxconfig.studyhelp import (
    CSCV_HELP,
    FP_HELP,
    GATE_HELP,
    SURF_HELP,
    WFM_HELP,
)  # noqa: F401

# Short names the window sends back, so it never sends a path; REL is what the window prints.
REL = {
    "variants": "sqx/variants/config.yaml",
    "sppdesign": "studies/breakage/spp/config.yaml",
    "batch": "engines/variants/config.yaml",
    "wfcstudy": "studies/optimisation/wfc/config.yaml",
    "cscvstudy": "studies/optimisation/cscv/config.yaml",
    "surfstudy": "studies/optimisation/marketSurfaces/config.yaml",
    "wfmstudy": "studies/optimisation/wfm/config.yaml",
    "thresholds": "ledger/thresholds.yaml",
    "gatecfg": "studies/screening/gate/config.yaml",
    "fpcfg": "studies/screening/falsePositives/config.yaml",
    "cloudcfg": "studies/optimisation/cloud/config.yaml",
    "calibcfg": "studies/optimisation/wfc/calibrate/config.yaml",
}
FILES = {name: ROOT / rel for name, rel in REL.items()}

# (file, the branch shown, its heading) per section, in the order the section lists them.
PARTS = {
    # Encargo 48: the batch's size is the ledger's `variants.*`; the SPP's `n_target` and `strata`
    # are no longer read by the factory (OPEN question to the owner: drop this first part?). The
    # map (step 16.5) and the calibration (a file that may not exist yet) have their own parts.
    "wfc": [
        (
            "sppdesign",
            ["design"],
            "Variantes por madre · diseño del lote (el brief del SPP)",
        ),
        ("variants", ["size"], "Tamaño del lote de variantes"),
        ("variants", ["design"], "Fábrica de variantes · semilla y rejillas"),
        ("variants", ["canaries"], "Canarios de control"),
        ("cloudcfg", [], "Mapa de parámetros · paso 16.5"),
        ("batch", [], "Lectura del lote · compartido con el CSCV"),
        ("wfcstudy", [], "Lectura del WFC"),
        ("calibcfg", [], "Calibración del criterio del WFC"),
    ],
    "cscv": [("cscvstudy", [], "El CSCV")],
    # Steps 18.5 and 19 (owner, 2026-10-07): one part each, the study's whole file.
    "surfaces": [
        ("surfstudy", [], "Las superficies de mercado"),
        ("batch", [], "Lectura del lote · compartido con el WFC"),
    ],
    "wfmreading": [("wfmstudy", [], "La WFM")],
    # Step 8, owner 2026-10-07: every value a rule of the gate reads is an input. The rules'
    # own thresholds live in pipeline/autopilot/criteria.yaml, not here.
    "gate": [
        ("gatecfg", ["screens"], "Cribas del nivel 0"),
        ("gatecfg", ["cascade"], "Cascada"),
        ("gatecfg", ["drift"], "R3 · la deriva del mercado"),
        ("gatecfg", ["frequency"], "R5 · sobredispersión de la frecuencia"),
        ("gatecfg", ["centring"], "R5 y R5d · el centro de la población"),
        ("gatecfg", ["cost_stress"], "R5c · el coste estresado"),
        ("gatecfg", ["concentration"], "R8 · la t sin lo mejor"),
        ("gatecfg", ["mae"], "R9b · la peor excursión en contra"),
        ("gatecfg", ["delay"], "Nivel 2 · ejecución una barra tarde"),
        ("gatecfg", ["homogeneity"], "R7 · homogeneidad por periodo"),
        ("gatecfg", ["drawdown"], "R6 · el drawdown contra el build"),
        ("gatecfg", ["monkey"], "Nivel 3c · el mono"),
    ],
    "falsepositives": [
        ("fpcfg", ["monkeys"], "Los monos de la cadena"),
        ("fpcfg", ["population"], "Poblaciones de prueba con ventaja plantada"),
    ],
}

from studies.optimisation.wfc.calibrate.tooltips import TIPS as CALIB_TIPS
from ui.daemon.sqxconfig.ranges import RANGES

PLACEHOLDER = "ledger:"  # what a config.yaml writes where the ledger owns the number
# A key that may be blank: a blank seed draws a new one each run, a blank cap leaves it open.
OPTIONAL = {("gatecfg", "seed"), ("gatecfg", "cap_slope"), ("fpcfg", "seed")}
CHOICES = {
    ("batch", "split_mode"): list(SHORTCUTS),
    ("wfmstudy", "modo_real"): ["fijo", "reoptimizado"],
    ("gatecfg", "window"): list(WINDOWS),
    ("gatecfg", "variant"): list("abcd"),
    ("gatecfg", "drop_period"): list(WINDOWS),
    ("gatecfg", "period"): list(WINDOWS),
    ("fpcfg", "rung"): ["free", "timing"],
    ("fpcfg", "sizing"): ["donor", "atr"],
}
# The two studies re-read these at analysis time: a batch already harvested reads differently.
# Said once per group, not per row: in CSCV every row would carry it.
REREAD = ("batch", "wfcstudy", "cscvstudy", "surfstudy", "wfmstudy", "thresholds")
WARN = (
    "⚠ El WFC y el CSCV leen estos valores al leer el lote, no al fabricarlo: volver a leer "
    "un lote ya hecho con otro valor da otro resultado. Cámbialos antes de leer, no después."
)
# The window speaks Spanish and these config.yaml comments are English, written for the code:
# each value's help is its study's own Spanish tooltip. `batch` is the exception, its comments
# are already the owner's words, in Spanish.
TIPS = {
    "variants": FACTORY_TIPS,
    "cloudcfg": CLOUD_TIPS,
    "calibcfg": CALIB_TIPS,
    "sppdesign": SPP_TIPS,
    "wfcstudy": WFC_TIPS,
    "cscvstudy": CSCV_TIPS,
    "surfstudy": SURF_TIPS,
    "wfmstudy": WFM_TIPS,
    "gatecfg": GATE_TIPS,
    "fpcfg": FP_TIPS,
}


def spec(name: str, path: list, value: object, threshold: str = "") -> dict[str, Any]:
    """What the window may do with one value of a study file.

    Args:
        name: A key of FILES.
        path: Keys and indices leading to it.
        value: Its current value.
        threshold: The ledger key when the value is a threshold row's.

    Returns:
        The same shape `options.spec` returns: `type`, `options`, `min`/`max`. The re-read
        warning is not here: it goes once under each group (`group_help`).
    """
    last = threshold or path[-1]
    if path[-1] == "why":
        return {"type": "text"}
    if (name, last) in CHOICES:
        return {"type": "choice", "options": choice(CHOICES[name, last])}
    if (name, last) in OPTIONAL:  # empty or a number, never anything else
        lo, hi = RANGES[name, last]
        return {"type": "number", "min": lo, "max": hi, "optional": True}
    if isinstance(value, bool):
        return {
            "type": "bool",
            "options": [
                {"value": True, "text": "sí · true"},
                {"value": False, "text": "no · false"},
            ],
        }
    if isinstance(value, (int, float)):
        lo, hi = RANGES.get((name, last), (None, None))
        return {"type": "number", "min": lo, "max": hi}
    return {"type": "list" if isinstance(value, list) else "text"}


@lru_cache(maxsize=4)
def _ledger(path: Path, stamp: int) -> list[tuple[int, dict]]:
    """The ledger's rows with their index, read once per version of the file (`stamp` is its mtime):
    the zone lists some thirty ledger-backed values and re-read the file for each, 7 s a render."""
    return list(enumerate(read(path)["thresholds"]))


def row(key: str) -> tuple[int, dict]:
    """The ledger's row for one threshold, and its index in `thresholds`.

    Raises:
        ValueError unless the key is declared exactly once, as `ledger.thresholds.value`
        refuses too; `ledger_fields` shows that as a locked value instead of failing the zone.
    """
    rows = [
        (i, r)
        for i, r in _ledger(FILES["thresholds"], FILES["thresholds"].stat().st_mtime_ns)
        if r["key"] == key
    ]
    if len(rows) != 1:
        raise ValueError(
            f"{key}: declarado {len(rows)} veces en ledger/thresholds.yaml, y "
            "el estudio necesita exactamente una fila"
        )
    return rows[0]


def blocks_help(n: int) -> str:
    """What a number of CSCV blocks buys: its partitions, C(n, n/2)."""
    if n % 2:
        return f"{n} es impar: el CSCV necesita un número par de bloques"
    many = f"{comb(n, n // 2):,}".replace(",", ".")  # 12.870, the Spanish thousands
    return f"{n} bloques dan C({n},{n // 2}) = {many} particiones"


def ledger_fields(
    key: str, hint: str, group: str, base: list, warn: str = WARN
) -> list[dict]:
    """A `ledger:<key>` placeholder as the two values the window edits: the number and its why.

    Args:
        key: The threshold's key, e.g. "cscv.blocks".
        hint: The placeholder's own help, from `help_of`.
        group: The heading it sits under.
        base: The placeholder's path, so the heading nests the way its neighbours do.
        warn: The sentence said once under the heading.

    Returns:
        Two fields of the file "thresholds". Who set it and when go into the help, so the
        window shows how old the decision is before anyone changes it.
    """
    try:
        i, r = row(key)
    except (
        ValueError
    ) as err:  # a bad merge in the ledger must not take the whole zone down
        return [
            {
                "file": "thresholds",
                "group": group,
                "base": base[:-1],
                "path": base,
                "key": base[-1],
                "value": f"ledger:{key}",
                "help": hint,
                "type": "text",
                "locked": str(err),
            }
        ]
    stamp = f"Umbral congelado del Ledger ({key}): fijado por {r['set_by']} el {r['set_on']}."
    value = r["value"]
    extra = blocks_help(value) + ". " if key == "cscv.blocks" else ""
    common = {
        "file": "thresholds",
        "group": group,
        "base": ["thresholds", i],
        "group_help": warn,
    }
    return [
        {
            **common,
            "path": ["thresholds", i, "value"],
            "key": base[-1],
            "value": value,
            "help": f"{extra}{stamp} {hint}".strip(),
            **spec("thresholds", ["value"], value, key),
        },
        {
            **common,
            "path": ["thresholds", i, "why"],
            "key": "why",
            "value": r["why"],
            "help": "Por qué tiene este valor. Al cambiar el número la ventana propone uno "
            "nuevo con la fecha y el valor anterior; edítalo si no es el tuyo.",
            **spec("thresholds", ["why"], r["why"]),
        },
    ]


def help_of(name: str, path: list, leaf: dict) -> str:
    """One value's explanation in Spanish: its tooltip, or its branch's, or the file's comment.

    Args:
        name: A key of FILES.
        path: The value's path.
        leaf: What `assetyaml.leaves` reported, for the Spanish comments of `batch`.

    Returns:
        The sentence, or "" when the study has none; never the file's English comment.
    """
    if name not in TIPS:
        return leaf["hint"]
    tips = TIPS[name]
    if (
        name == "gatecfg" and path[0] == "screens"
    ):  # a screen's knob is keyed by its name
        path = [read(FILES[name])["screens"][path[1]]["name"], *path[2:]]
    for depth in range(len(path), 0, -1):
        if ".".join(map(str, path[:depth])) in tips:
            return tips[".".join(map(str, path[:depth]))]
    return ""


def fields(section: str) -> list[dict]:
    """Every study value one section of the zone shows, in the order of PARTS.

    Args:
        section: a key of PARTS.

    Returns:
        One field per value, with its own `file` (a key of FILES), `group` (its heading),
        `base` (the part of its path the heading already names) and `group_help` (said once
        under the heading). `help` is Spanish (`help_of`); `sections.py` cleans it.
    """
    out = []
    for name, branch, group in PARTS[section]:
        if not FILES[name].exists():
            continue
        for leaf in leaves(FILES[name]):
            path = leaf["path"]
            if path[: len(branch)] != branch or (
                path[0] == "screens" and path[-1] != "min_trades"
            ):
                continue
            value = leaf["value"]
            if isinstance(value, str) and value.startswith(PLACEHOLDER):
                out += ledger_fields(
                    value.removeprefix(PLACEHOLDER),
                    help_of(name, path, leaf),
                    group,
                    path,
                    "" if name in ("gatecfg", "fpcfg") else WARN,
                )
                continue
            out.append(
                {
                    "file": name,
                    "group": group,
                    "base": branch,
                    "path": path,
                    "key": leaf["label"],
                    "value": value,
                    "help": help_of(name, path, leaf),
                    "group_help": WARN if name in REREAD else "",
                    **spec(name, path, value),
                }
            )
    return out
