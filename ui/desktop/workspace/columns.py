"""Which columns one databank table can show: today's default, and every metric per segment."""

import re

from ui.text.columnhelp import help_for
from ui.text.glossary import label

# The chooser's groups. «OOS» is the payload's own out-of-sample block, whatever span its task
# covered: the segments route says which (OOS1, OOS2) when the cosecha's trades tell it.
SEGMENTS = ("IS", "OOS", "OOS2", "IS+OOS1")
SAMPLE = {"IS": "IS", "OOS": "OOS", "OOS2": "OOS2", "oos2": "OOS2"}
DASH = "–"
PENDING = "leyendo del demonio…"
WHY = {"OOS2": "sin export de OOS2 para este databank",
       "IS+OOS1": "la unión IS+OOS1 sólo se calcula para neto, operaciones, Profit Factor, "
                  "Win Rate, drawdown y Ret/DD",
       "": "SQX no exporta esta métrica en este segmento"}
NO_OOS = "sin operaciones OOS: su unión sería sólo su IS"
# What says a strategy loses money, read in the red (owner, 2026-09-28): a profit factor under
# 1, and below zero a metric whose sign is the profit's. A drawdown, a loss or a count never.
FACTOR = re.compile(r"(?i)\bprofit factor\b|\bPF\b")
SIGNED = re.compile(r"(?i)profit|return|sharpe|sortino|expectancy|ret/dd|cagr|calmar|sqn|"
                    r"avg\.? trade|average trade|neto|edge")
NEVER = re.compile(r"(?i)drawdown|^(max )?dd\b|\bdd (máximo|max)|ulcer|loss|pérdida")


def metric_id(metric: str, segment: str) -> str:
    """The id a metric column is saved under: `Net profit|OOS`."""
    return f"{metric}|{segment}"


def is_metric(key: str) -> bool:
    """Whether a column id names a metric (`Net profit|OOS`) rather than a study's column."""
    return "|" in key


def unprofitable(key: str, value: object) -> bool:
    """Whether a cell's figure says the strategy does not make money, to paint it red.

    Args:
        key: The column id: a metric's (`Profit factor|OOS`) or a study column's key.
        value: The cell's value; anything but a number is never red.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    name = key.rpartition("|")[0] if is_metric(key) else key
    if FACTOR.search(name):
        return value < 1
    if NEVER.search(name):
        return False
    return value < 0 and (not is_metric(key) or bool(SIGNED.search(name)))


def column_id(column: dict) -> str:
    """The id of one payload column: a metric by name and sample, a study column by its key."""
    if column["kind"] == "metric":
        return metric_id(column["metric"], SAMPLE.get(column["sample"], column["sample"]))
    return column["key"]


def union_why(name: str, segs: dict | None) -> str | None:
    """Why an IS+OOS1 column has no figure, or None when the segments route computed it."""
    if segs is None:
        return PENDING
    if segs.get("error"):
        return f"no se pudo calcular: {segs['error']}"
    return segs.get("why") if name in segs["union"] else WHY["IS+OOS1"]


def choices(columns: list[dict], defaults: list[tuple[int, str]],
            segs: dict | None) -> dict[str, dict]:
    """Every column the chooser offers for one table.

    Args:
        columns: GET /api/databank/table's `columns`.
        defaults: `table.pick` of this table: today's view, as (payload index, header).
        segs: GET /api/databank/segments; `{error}` when it failed, None while not read.

    Returns:
        id → {id, header, group (segment, or «Estudio»), index (payload column or None),
        union (a metric the segments route computes, or None), why (None when it has data),
        default, help (the header's «?», `ui.text.columnhelp`, or None)}. Defaults first in their order, then the metric grid by segment.
    """
    out = {}
    for i, head in defaults[1:]:
        c = columns[i]
        group = SAMPLE.get(c["sample"], c["sample"]) if c["kind"] == "metric" else "Estudio"
        out[column_id(c)] = {"id": column_id(c), "header": head, "group": group, "index": i,
                             "union": None, "why": None, "default": True,
                             "help": (help_for("metric", "", c["metric"]) if c["kind"] == "metric"
                                      else help_for("study", c["study"], c["field"]))}
    at = {column_id(c): i for i, c in enumerate(columns) if c["kind"] == "metric"}
    union = (segs or {}).get("union") or []
    names = list(dict.fromkeys([c["metric"] for c in columns if c["kind"] == "metric"] + union))
    for segment in SEGMENTS:
        for name in names:
            key = metric_id(name, segment)
            if key in out:
                continue
            joined = segment == "IS+OOS1"
            why = (None if key in at else union_why(name, segs) if joined
                   else WHY.get(segment, WHY[""]))
            out[key] = {"id": key, "header": f"{label(name)} {segment}", "group": segment,
                        "index": at.get(key), "union": name if joined and not why else None,
                        "why": why, "default": False, "help": help_for("metric", "", name)}
    return out


def shown_ids(view: dict | None, defaults: list[str]) -> list[str]:
    """The ids a table shows: its defaults, less what the owner hid, plus what he added, in
    his order. A default column that appeared after he chose (a new study) is shown, at the
    end; an id nobody offers now stays in the list and `resolve` skips it."""
    view = view if isinstance(view, dict) else {}
    hidden, added = set(view.get("hidden", [])), view.get("added", [])
    base = [d for d in defaults if d not in hidden] + [a for a in added if a not in defaults]
    rank = {k: i for i, k in enumerate(view.get("order", []))}
    return sorted(base, key=lambda k: (k not in rank, rank.get(k, 0)))


def diff(shown: list[str], defaults: list[str], old: dict | None,
         offered: dict[str, dict]) -> dict:
    """What the owner changed against the default, to save: `hidden`, `added`, `order`. What
    the old choice named and this databank does not offer now is kept, not lost."""
    old = old if isinstance(old, dict) else {}
    gone = [k for k in old.get("order", []) if k not in offered and k not in shown]
    return {"hidden": [d for d in defaults if d not in shown]
                      + [k for k in old.get("hidden", []) if k not in defaults],
            "added": [k for k in shown if k not in defaults]
                     + [k for k in old.get("added", []) if k not in offered and k not in shown],
            "order": list(shown) + gone}


def resolve(ids: list[str], offered: dict[str, dict]) -> list[dict]:
    """The chosen columns in order; an id this databank does not offer now is skipped."""
    return [offered[k] for k in ids if k in offered]


def value(choice: dict, row: dict, segs: dict | None) -> object:
    """One cell: the payload's value, or the segments route's for a computed union metric."""
    if choice["index"] is not None:
        return row["values"][choice["index"]]
    if choice["union"] and segs and row["identity"]:
        return segs["rows"].get(row["identity"], {}).get(choice["union"])
    return None


def note(choice: dict, row: dict, segs: dict | None) -> str:
    """The tooltip of an empty metric cell: why it reads «–»."""
    if choice["union"] and segs and row["identity"] in segs.get("no_oos", ()):
        return NO_OOS
    return choice["why"] or "sin dato para esta estrategia"


def merged(before: list[str], checked: set[str], offered: dict[str, dict]) -> list[str]:
    """The chooser's answer: what stays keeps its place, what was added goes at the end in
    the chooser's order (segment by segment)."""
    return [k for k in before if k in checked] + [k for k in offered
                                                  if k in checked and k not in before]
