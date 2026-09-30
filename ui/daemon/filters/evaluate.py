"""Which columns a filter may read, and which visible strategies an AND of rows sets aside."""

import re

import numpy as np

from ledger import gate
from ui.daemon.filters import dists
from ui.daemon.results.catalogue import STUDIES
from ui.daemon.workflow.steps import STEPS
from ui.text.glossary import label

# Studies whose figures read OOS2 whatever the asset (encargo 22 §7.1: never a filter on OOS2 --
# lifted for humans by the owner on 2026-09-28; it holds only under `ledger.gate.enforced()`):
# the WFM's window ends in it, step 20 is its SPA, the CSCV cuts build+oos1+oos2 (Q11), market
# surfaces and the ATR stop may read it, exposure is judged over the whole history. `refused`
# adds every study of a step the asset's `_policy.yaml` reserves oos2 for; the WFC's
# compositions are caught by name below.
OOS2_STUDIES = {"wfm", "blindJoint", "cscv", "marketSurfaces", "atrCalculator", "exposure"}
OOS2 = re.compile(r"oos\s*_?2", re.IGNORECASE)
SAMPLE = re.compile(r"^(.*) [(\[]([^()\[\]]+)[)\]]$")    # «Net profit (IS)», «… [OOS]»
NUMERIC = (">", "<", ">=", "<=", "entre")
SHOWN = {">": ">", "<": "<", ">=": "≥", "<=": "≤", "=": "=", "entre": "entre",
         "dentro": "dentro", "fuera": "fuera"}


def number(value: object) -> float | None:
    """A cell as a float, or None for a blank or a word."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def named(key: str) -> str:
    """A filterable column key in the words the window shows, as the databank table heads it.

    Args:
        key: `Net profit (IS)` (an SQX metric and its sample), `crossTF.H1.p` (study, sub,
            field) or `dist:<study>/<title> [<unit>]` (a distribution).

    Returns:
        «Beneficio neto IS», «Cross-timeframe · H1 · p», «Distribución · Test del mono · …»;
        a key none of those fits, through the glossary.
    """
    if key.startswith("dist:"):
        study, title = key[len("dist:"):].split("/", 1)
        return f"Distribución · {STUDIES[study][2] if study in STUDIES else label(study)} · {title}"
    parts = key.split(".")
    if len(parts) > 1 and parts[0] in STUDIES:
        return " · ".join([STUDIES[parts[0]][2], *parts[1:-1], label(parts[-1])])
    sample = SAMPLE.match(key)
    return f"{label(sample.group(1))} {sample.group(2)}" if sample else label(key)


def refused(symbol: str | None) -> set[str]:
    """The study keys never offered: OOS2_STUDIES, plus the studies of every step that
    `assets/_policy.yaml` reserves this asset's oos2 for (`ledger.gate.reserved`). Empty for a
    human (owner, 2026-09-28): only an autonomous agent under `gate.enforced()` is kept off OOS2."""
    if not gate.enforced():
        return set()
    steps = set(gate.reserved(symbol).get("oos2", [])) if symbol else set()
    return OOS2_STUDIES | {k for s in STEPS if float(s["n"]) in steps for k in s["studies"]}


def reads_oos2(column: dict, studies: set[str]) -> bool:
    """Whether a column of `/api/databank/table` is an OOS2 figure."""
    if column["kind"] == "metric":
        return bool(OOS2.search(column.get("sample", "")))
    return column.get("study") in studies or bool(OOS2.search(column["key"]))


def offered(table: dict, by_id: dict[str, dict[str, dict]], studies: set[str]) -> list[dict]:
    """The metrics the dropdown lists: the databank's real columns, then its distributions.

    Args:
        table: What `/api/databank/table` answered.
        by_id: What `dists.project` answered.
        studies: What `refused` gave.

    Returns:
        [{key, label (the words shown), kind (metric | study | dist), sample, numeric,
        n (rows with a value), reading (dist only)}], OOS2 left out.
    """
    ids = {r["identity"] for r in table["rows"] if r["identity"]}
    out = []
    for i, c in enumerate(table["columns"]):
        if c["kind"] == "name" or reads_oos2(c, studies):
            continue
        values = [r["values"][i] for r in table["rows"] if r["values"][i] is not None]
        if values:
            tail = re.search(r"\[(IS|OOS)\]$", c["key"])
            sample = c.get("sample") or (tail.group(1) if tail else "")
            out.append({"key": c["key"], "label": named(c["key"]), "kind": c["kind"],
                        "sample": sample, "n": len(values),
                        "numeric": all(number(v) is not None for v in values)})
    seen: dict[str, dict] = {}
    for identity in ids & set(by_id):
        for k, block in by_id[identity].items():
            seen.setdefault(k, {"key": k, "label": named(k), "kind": "dist", "sample": "",
                                "numeric": True, "n": 0,
                                "reading": dists.reading(block)})["n"] += 1
    return out + sorted(seen.values(), key=lambda m: m["key"])


def numeric(value: object) -> object:
    """A value as a float when it reads as a number, else as it came."""
    return number(value) if number(value) is not None else value


def normal(rows: list[dict]) -> list[dict]:
    """The rows with every value that reads as a number stored as one: the window sends text,
    and the ledger's `thresholds` and the saved filters must hold 30, not "30"."""
    return [{**r, "value": [numeric(v) for v in r["value"]] if isinstance(r["value"], list)
             else numeric(r["value"])} for r in rows]


def written(value: object) -> str:
    """A value as the expression prints it and the owner can type it back: 30, not 30.0, and
    0.00001, never 1e-05 — exact, without the grouping `numbers.num` adds."""
    x = number(value)
    return np.format_float_positional(x, trim="-") if x is not None else str(value)


def expression(rows: list[dict]) -> str:
    """The filter as one line, each column in the window's words: the ledger's `criterion`
    and the funnel's why. The machine form stays in the ledger row's `thresholds`."""
    parts = []
    for r in rows:
        if r["op"] == "entre":
            value = f"{written(r['value'][0])} y {written(r['value'][1])}"
        elif r["op"] in ("dentro", "fuera"):
            value = f"del intervalo {written(r['value'])} %"
        else:
            value = written(r["value"])
        parts.append(f"{named(r['metric'])} {SHOWN[r['op']]} {value}")
    return " AND ".join(parts)


def check(rows: list[dict], metrics: list[dict]) -> str | None:
    """Why a filter cannot run, in Spanish, or None when it can."""
    known = {m["key"]: m for m in metrics}
    if not rows:
        return "el filtro no tiene ninguna condición"
    for r in rows:
        m = known.get(r["metric"])
        if m is None:
            return (f"«{named(r['metric'])}» no es una columna de este databank (o es de "
                    "OOS2, que no se filtra)")
        if r["op"] not in SHOWN:
            return f"operador desconocido «{r['op']}»"
        if (m["kind"] == "dist") != (r["op"] in ("dentro", "fuera")):
            return (f"«{named(r['metric'])}»: una distribución se filtra con «dentro»/«fuera» "
                    "del intervalo, y una columna con >, <, ≥, ≤, = o entre")
        if r["op"] in ("dentro", "fuera") and number(r["value"]) not in dists.PAIRS:
            return f"el intervalo tiene que ser uno de {sorted(dists.PAIRS)} %"
        if r["op"] == "entre" and (not isinstance(r["value"], list) or len(r["value"]) != 2
                                   or any(number(v) is None for v in r["value"])):
            return f"«{named(r['metric'])}» entre: hacen falta dos números"
        if r["op"] in NUMERIC[:4] and (not m["numeric"] or number(r["value"]) is None):
            return (f"«{named(r['metric'])}» {SHOWN[r['op']]}: la columna o el valor no es "
                    "un número")
    return None


def holds(row: dict, cell: object, block: dict | None) -> bool | None:
    """One condition on one strategy: True, False, or None when it has no value to judge."""
    op, value = row["op"], row["value"]
    if op in ("dentro", "fuera"):
        got = None if block is None else dists.inside(block, int(number(value)))
        return None if got is None else got == (op == "dentro")
    if op == "=":
        return None if cell is None else (number(cell) == number(value)
                                          if number(value) is not None else str(cell) == str(value))
    x = number(cell)
    if x is None:
        return None
    if op == "entre":
        lo, hi = sorted(number(v) for v in value)
        return lo <= x <= hi
    return {">": x > number(value), "<": x < number(value), ">=": x >= number(value),
            "<=": x <= number(value)}[op]


def judge(table: dict, rows: list[dict], by_id: dict[str, dict[str, dict]],
          hidden: set[str]) -> tuple[dict[str, str], dict[str, str], int]:
    """Which of the visible strategies the AND of rows keeps.

    Args:
        table: What `/api/databank/table` answered.
        rows: [{metric, op, value}], already `check`ed.
        by_id: What `dists.project` answered.
        hidden: What earlier filters and deletions already set aside.

    Returns:
        (visible identity → name, dropped identity → name, how many stayed visible for a
        blank: a strategy with no value for a row's metric is not judged by it, and stays).
    """
    col = {c["key"]: i for i, c in enumerate(table["columns"])}
    visible = {r["identity"]: r for r in table["rows"]
               if r["identity"] and r["identity"] not in hidden}
    dropped, blank = {}, 0
    for identity, r in visible.items():
        said = [holds(f, r["values"][col[f["metric"]]] if f["metric"] in col else None,
                      by_id.get(identity, {}).get(f["metric"])) for f in rows]
        if False in said:
            dropped[identity] = r["name"]
        elif None in said:
            blank += 1
    return {i: r["name"] for i, r in visible.items()}, dropped, blank
