"""The versioned thresholds, and whether the code still uses the numbers they declare."""

import re

import pandas as pd
import yaml

from core.paths import ROOT

FILE = ROOT / "ledger" / "thresholds.yaml"
SELECTOR = re.compile(r"^(\w+)\[(\w+)=([^\]]+)\]$")


def declared() -> list[dict]:
    """Every threshold this project has written down, with who set it and when.

    Returns:
        The rows of `thresholds.yaml`. Read by whoever needs a number; written by nobody.
    """
    return yaml.safe_load(FILE.read_text(encoding="utf-8"))["thresholds"]


def resolve(source: str) -> float:
    """The value the code actually uses, followed from a `file#a.b.c` pointer.

    Args:
        source: `path/to/config.yaml#key.sub.key`, where a step may also be
            `list[field=value]` to pick one entry out of a list of dicts.

    Returns:
        Whatever sits at the end of that path. Raises on a pointer that no longer
        resolves, which is the point: a threshold whose home moved is exactly the case a
        silent default would hide.
    """
    path, dotted = source.split("#", 1)
    node = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    for step in dotted.split("."):
        picked = SELECTOR.match(step)
        if picked:
            name, field, wanted = picked.groups()
            node = next(item for item in node[name] if str(item[field]) == wanted)
        else:
            node = node[step]
    return node


def divergences() -> pd.DataFrame:
    """Where the register and the code disagree.

    Returns:
        One row per declared threshold: what it says, what the code uses, and whether they
        match. While `thresholds.yaml` is a register rather than the source, this is the
        only thing standing between two copies of a number and a study that quietly ran
        under a threshold nobody recorded.
    """
    rows = []
    for row in declared():
        live = resolve(row["source"])
        rows.append({"key": row["key"], "declarado": row["value"], "en_código": live,
                     "coincide": bool(live == row["value"]), "fijado_por": row["set_by"],
                     "el": row["set_on"]})
    return pd.DataFrame(rows)
