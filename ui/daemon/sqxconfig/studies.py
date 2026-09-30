"""The study files behind the WFC and the CSCV, shown beside _build.yaml's `wfc` and in a CSCV section.

Owner, 2026-09-28: every input of both steps is seen and edited here, not only the SQX tasks
`_build.yaml` declares — the batch each mother gets (the SPP design's cap and the factory's floor),
the factory's seed and grids, the canaries, the trade floor and split the two studies share, each
study's own knobs, and the CSCV's blocks, which live in the ledger's frozen thresholds and are
stamped with who and when on every write (`studywrite.py`).
"""

from math import comb

from core.assetyaml import leaves, read
from core.paths import ROOT
from engines.variants.panel import SHORTCUTS
from studies.optimisation.cscv.measure.cscv import SCORES
from studies.optimisation.cscv.measure.rules import RULES
from sqx.variants.tooltips import TIPS as FACTORY_TIPS
from studies.breakage.spp.tooltips import TIPS as SPP_TIPS
from studies.optimisation.cscv.tooltips import TIPS as CSCV_TIPS
from studies.optimisation.wfc.tooltips import TIPS as WFC_TIPS
from ui.daemon.sqxconfig.options import choice

# Short names the window sends back, so it never sends a path; REL is what the window prints.
REL = {"variants": "sqx/variants/config.yaml", "sppdesign": "studies/breakage/spp/config.yaml",
       "batch": "engines/variants/config.yaml", "wfcstudy": "studies/optimisation/wfc/config.yaml",
       "cscvstudy": "studies/optimisation/cscv/config.yaml", "thresholds": "ledger/thresholds.yaml"}
FILES = {name: ROOT / rel for name, rel in REL.items()}

# (file, the branch shown, its heading) per section, in the order the section lists them.
PARTS = {
    "wfc": [("sppdesign", ["design"], "Variantes por madre · diseño del lote"),
            ("variants", ["minimum"], "Mínimo de variantes por madre"),
            ("variants", ["design"], "Fábrica de variantes · semilla y rejillas"),
            ("variants", ["canaries"], "Canarios de control"),
            ("batch", [], "Lectura del lote · compartido con el CSCV"),
            ("wfcstudy", [], "Lectura del WFC")],
    "cscv": [("cscvstudy", ["cscv"], "El CSCV"),
             ("batch", [], "Lectura del lote · compartido con el WFC")],
}

PLACEHOLDER = "ledger:"   # what a config.yaml writes where the ledger owns the number
SHARE = (0, 1)            # a fraction of something
# (file, last key) -> (min, max). Every other number is open.
RANGES = {("sppdesign", "n_target"): (1, None), ("sppdesign", "min_span"): SHARE,
          ("sppdesign", "min_levels"): (2, 50), ("sppdesign", "max_levels"): (2, 50),
          ("sppdesign", "plateau_share"): SHARE, ("sppdesign", "neighbourhood"): SHARE,
          ("sppdesign", "factorial"): SHARE, ("sppdesign", "coverage"): SHARE,
          ("variants", "variants"): (1, None), ("variants", "widen_step"): SHARE,
          ("variants", "max_span"): (0, 2), ("variants", "radius"): (1, None),
          ("variants", "min_levels"): (2, None), ("variants", "span"): SHARE,
          ("variants", "steps"): (2, None), ("variants", "n"): (0, None),
          ("batch", "min_trades"): (0, None), ("wfcstudy", "rho_floor"): (-1, 1),
          ("wfcstudy", "table_ends"): (1, None), ("cscvstudy", "random_draws"): (1, None),
          ("cscvstudy", "bootstrap"): (1, None), ("cscvstudy", "cluster_k_max"): (1, None),
          ("thresholds", "cscv.blocks"): (4, 20)}
CHOICES = {("batch", "split_mode"): list(SHORTCUTS), ("cscvstudy", "period"): ["D", "W", "ME"],
           ("cscvstudy", "score"): list(SCORES)}
# The two studies re-read these at analysis time: a batch already harvested reads differently.
# Said once per group, not per row: in CSCV every row would carry it.
REREAD = ("batch", "wfcstudy", "cscvstudy", "thresholds")
WARN = ("⚠ El WFC y el CSCV leen estos valores al leer el lote, no al fabricarlo: volver a leer "
        "un lote ya hecho con otro valor da otro resultado. Cámbialos antes de leer, no después.")
# The window speaks Spanish and these config.yaml comments are English, written for the code:
# each value's help is its study's own Spanish tooltip. `batch` is the exception, its comments
# are already the owner's words, in Spanish.
TIPS = {"variants": FACTORY_TIPS, "sppdesign": SPP_TIPS, "wfcstudy": WFC_TIPS,
        "cscvstudy": CSCV_TIPS}
CSCV_HELP = ("Paso 18. Donde el WFC pregunta si esta superficie se mantuvo fuera de muestra, el "
             "CSCV pregunta lo que hay detrás: ¿la MANERA de elegir parámetros tiende a "
             "sobreajustar? Parte la historia en bloques, prueba cada mitad posible como dentro "
             "de muestra contra la otra, y cuenta cuántas veces la variante elegida dentro queda "
             "por debajo de la mediana fuera: eso es el PBO. Lee siempre build+oos1+oos2.")


def spec(name: str, path: list, value: object, threshold: str = "") -> dict:
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
    if (name, last) == ("cscvstudy", "rules"):
        return {"type": "choices", "options": choice(list(RULES))}
    if isinstance(value, bool):
        return {"type": "bool", "options": [{"value": True, "text": "sí · true"},
                                            {"value": False, "text": "no · false"}]}
    if isinstance(value, (int, float)):
        lo, hi = RANGES.get((name, last), (None, None))
        return {"type": "number", "min": lo, "max": hi}
    return {"type": "list" if isinstance(value, list) else "text"}


def row(key: str) -> tuple[int, dict]:
    """The ledger's row for one threshold, and its index in `thresholds`.

    Raises:
        ValueError unless the key is declared exactly once, as `ledger.thresholds.value`
        refuses too; `ledger_fields` shows that as a locked value instead of failing the zone.
    """
    rows = [(i, r) for i, r in enumerate(read(FILES["thresholds"])["thresholds"]) if r["key"] == key]
    if len(rows) != 1:
        raise ValueError(f"{key}: declarado {len(rows)} veces en ledger/thresholds.yaml, y "
                         "el estudio necesita exactamente una fila")
    return rows[0]


def blocks_help(n: int) -> str:
    """What a number of CSCV blocks buys: its partitions, C(n, n/2)."""
    if n % 2:
        return f"{n} es impar: el CSCV necesita un número par de bloques"
    many = f"{comb(n, n // 2):,}".replace(",", ".")   # 12.870, the Spanish thousands
    return f"{n} bloques dan C({n},{n // 2}) = {many} particiones"


def ledger_fields(key: str, hint: str, group: str, base: list) -> list[dict]:
    """A `ledger:<key>` placeholder as the two values the window edits: the number and its why.

    Args:
        key: The threshold's key, e.g. "cscv.blocks".
        hint: The placeholder's own help, from `help_of`.
        group: The heading it sits under.
        base: The placeholder's path, so the heading nests the way its neighbours do.

    Returns:
        Two fields of the file "thresholds". Who set it and when go into the help, so the
        window shows how old the decision is before anyone changes it.
    """
    try:
        i, r = row(key)
    except ValueError as err:   # a bad merge in the ledger must not take the whole zone down
        return [{"file": "thresholds", "group": group, "base": base[:-1], "path": base,
                 "key": base[-1], "value": f"ledger:{key}", "help": hint, "type": "text",
                 "locked": str(err)}]
    stamp = f"Umbral congelado del Ledger ({key}): fijado por {r['set_by']} el {r['set_on']}."
    value = r["value"]
    extra = blocks_help(value) + ". " if key == "cscv.blocks" else ""
    common = {"file": "thresholds", "group": group, "base": ["thresholds", i], "group_help": WARN}
    return [{**common, "path": ["thresholds", i, "value"], "key": base[-1], "value": value,
             "help": f"{extra}{stamp} {hint}".strip(), **spec("thresholds", ["value"], value, key)},
            {**common, "path": ["thresholds", i, "why"], "key": "why", "value": r["why"],
             "help": "Por qué tiene este valor. Al cambiar el número la ventana propone uno "
                     "nuevo con la fecha y el valor anterior; edítalo si no es el tuyo.",
             **spec("thresholds", ["why"], r["why"])}]


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
    for depth in range(len(path), 0, -1):
        if ".".join(map(str, path[:depth])) in tips:
            return tips[".".join(map(str, path[:depth]))]
    return ""


def fields(section: str) -> list[dict]:
    """Every study value one section of the zone shows, in the order of PARTS.

    Args:
        section: "wfc" or "cscv".

    Returns:
        One field per value, with its own `file` (a key of FILES), `group` (its heading),
        `base` (the part of its path the heading already names) and `group_help` (said once
        under the heading). `help` is Spanish (`help_of`); `sections.py` cleans it.
    """
    out = []
    for name, branch, group in PARTS[section]:
        for leaf in leaves(FILES[name]):
            path = leaf["path"]
            if path[:len(branch)] != branch:
                continue
            value = leaf["value"]
            if isinstance(value, str) and value.startswith(PLACEHOLDER):
                out += ledger_fields(value.removeprefix(PLACEHOLDER), help_of(name, path, leaf),
                                     group, path)
                continue
            out.append({"file": name, "group": group, "base": branch, "path": path,
                        "key": leaf["label"], "value": value, "help": help_of(name, path, leaf),
                        "group_help": WARN if name in REREAD else "", **spec(name, path, value)})
    return out
