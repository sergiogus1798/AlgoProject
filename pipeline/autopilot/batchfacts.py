"""The `facts` dict a study result carries, as fact rows: one FILE per mother (`<batch>/estudios/<study>.json`) or a page."""

import json
from pathlib import Path

import numpy as np

# Text a rule can test as a number: a state (pasa/limbo/no_pasa, one is better than the next)
# and an order (positivo/neutro/perverso) — the WFC's and the market surfaces'.
WORDS = {"pasa": 1.0, "limbo": 0.0, "no_pasa": -1.0, "positivo": 1.0, "neutro": 0.0, "perverso": -1.0}
BOOLS = {"True": 1.0, "False": 0.0}


def number(value: object) -> float | None:
    """A cell as a float, or None when it is not a number (text, None, NaN).

    A CSV cell comes as text: a number in it is read, and "True"/"False" are 1 and 0.
    """
    if isinstance(value, str):
        value = BOOLS.get(value, value)
        try:
            value = float(value)
        except ValueError:
            return None
    if not isinstance(value, (bool, int, float, np.number, np.bool_)):
        return None
    return float(value) if value == value else None


def databank_name(folder: str) -> str:
    """A batch folder's mother as the databank spells it: `Strategy_10.11.484` -> `Strategy 10.11.484`."""
    return folder.replace("_", " ")


def flat(facts: dict) -> list[tuple[str, object]]:
    """A result's `facts` dict as (key, value) pairs: nested keys joined with dots (`c1.estado`,
    `l1.p_menos`...), a state word as its number (`WORDS`), any other text left for `number`
    to drop."""
    pairs, todo = [], [("", facts)]
    while todo:
        at, node = todo.pop()
        for k, v in node.items():
            if isinstance(v, dict):
                todo.append((f"{at}{k}.", v))
            else:
                pairs.append((f"{at}{k}", WORDS.get(v, v) if isinstance(v, str) else v))
    return pairs


def rows(study: str, file: Path, pairs: list) -> list[dict]:
    """`pairs` (the contract's flattened numbers) plus the file's top-level `facts` dict (`flat`).

    The mother is the batch folder two levels up (`databank_name`).
    """
    pairs = list(pairs) + flat(json.loads(file.read_text(encoding="utf-8")).get("facts") or {})
    name = databank_name(file.parent.parent.name)
    return [{"study": study, "strategy": name, "identity": "", "key": k, "value": number(x)}
            for k, x in pairs]
