"""The shape of a literature entry, and what a draft must satisfy before it is stored."""

import re
from typing import cast

from studies.research.literature import anchors

# The sixteen keys of `edges-2026-10-02.yaml` are the contract `marketProfile/bibliography.py`
# reads; `id`, `source`, `verified` and `overlaps_is` are stamped by `accept`, never drafted.
DRAFT = ["paper", "slug", "asset_class", "assets", "family", "direction", "horizon", "condition",
         "size", "sample", "grade", "needs_clock", "decay", "translation", "selection", "anchors"]
OPTIONAL = ["question"]
STAMPED = ["id", "source", "verified", "overlaps_is", "overlaps_oos1", "overlaps_oos2", "read", "similar_to"]
FAMILIES = ["tendencia", "ruptura", "reversion", "momentum", "volatilidad", "patron"]
GRADES = ["peer-reviewed", "working paper", "quantified practitioner test", "code repository"]
READS = {"full text": "yes (every anchor checked against the stored text)",
         "abstract only": "abstract only"}
# The hard filters, applied before extraction; a rejection names one.
FILTERS = {
    "no_rule": "the paper states no trading rule with an entry (theory, a model, a forecast)",
    "cross_sectional": "ranks or holds several assets at once: not a one-asset time-series rule",
    "fundamentals": "needs data that is not the asset's own price (earnings, flows, macro, text)",
    "clock": "the entry or the exit reads the hour, the weekday or the calendar (hard rule 15)",
    "not_sqx_at_market": "not expressible with SQX building blocks entering at market",
    "conditions": "the entry needs more than two conditions (hard rule 14)",
    "two_legs": "long and short held together: not one direction per strategy (hard rule 13)",
    "unreadable": "neither the full text nor an abstract stating the rule could be read",
    "no_backtest": "an item of a code repository that reports no backtest result of its own"}
# field → where its value lives in the entry; `rule` must be quoted, the rest may be absent.
ANCHORED = {"rule": ("translation", "entry"), "assets": ("assets",), "direction": ("direction",),
            "lookback": ("horizon", "lookback"), "holding": ("horizon", "holding"),
            "condition": ("condition",), "size": ("size",), "sample": ("sample",),
            "variants_tried": ("selection", "variants_tried"), "out_of_sample": ("decay",)}
TRANSLATION = ["entry", "hold", "context", "params", "note", "conditions"]
MEASURE_ARGS = {"enter", "when", "leave", "cap", "days", "trail", "ruler"}
CLOCK = re.compile(r"\b(hour|o'clock|session|weekday|monday|tuesday|wednesday|thursday|friday|"
                   r"day of the (week|month)|month[- ]end|turn of the month|time of day|"
                   r"overnight|\d{1,2}:\d{2})\b", re.I)


def value(entry: dict, path: tuple) -> object:
    """The value an anchored field has in the entry."""
    for key in path:
        entry = entry[key]
    return entry


def shape(draft: dict) -> list[str]:
    """What is wrong with a draft's keys and vocabulary, before any quote is looked up."""
    out = [f"missing key: {k}" for k in DRAFT if k not in draft]
    out += [f"unknown key: {k}" for k in draft if k not in DRAFT + OPTIONAL]
    out += [f"{k} is stamped on acceptance, not drafted" for k in draft if k in STAMPED]
    if out:
        return out
    if draft["family"] not in FAMILIES:
        out.append(f"family: one of {FAMILIES}")
    if not str(draft["direction"]).startswith(("long", "short", "both")):
        out.append("direction: opens with long, short or both")
    if not str(draft["grade"]).startswith(tuple(GRADES)):
        out.append(f"grade: opens with one of {GRADES}")
    if not str(draft["needs_clock"]).startswith("no"):
        out.append("needs_clock: a rule that needs the clock is rejected (filter `clock`)")
    if set(draft["horizon"]) != {"lookback", "holding", "source_bar"}:
        out.append("horizon: lookback, holding, source_bar")
    if set(draft["selection"]) != {"variants_tried", "sample_from", "sample_to"}:
        out.append("selection: variants_tried, sample_from, sample_to")
    tr = draft["translation"]
    out += [f"translation: missing {k}" for k in TRANSLATION if k not in tr]
    out += [f"translation: unknown {k}" for k in tr if k not in TRANSLATION + ["measures"]]
    # `tested_by` is written by a session, never drafted: the existing measure of the same rule.
    return out


def rules(draft: dict) -> list[str]:
    """What breaks the owner's hard rules: the clock, the count of conditions, an open question."""
    tr, out = draft["translation"], []
    read = " ".join(str(tr[k]) for k in ("entry", "hold", "context"))
    if CLOCK.search(read):
        out.append(f"translation: reads the clock («{cast('re.Match[str]', CLOCK.search(read))[0]}») — hard rule 15")
    if tr["conditions"] not in (1, 2):
        out.append("translation.conditions: 1 or 2 entry conditions (hard rule 14)")
    question = draft.get("question")
    if question is not None:
        if set(question) != {"text", "readings", "answer"} or len(question["readings"]) < 2:
            out.append("question: text, at least two readings, answer ('' until the owner's)")
        elif not question["answer"] and "measures" in tr:
            out.append("question: a rule with two readings is not measured before the owner answers")
    return out + [w for spec in tr.get("measures", []) for w in measure(spec)]


def measure(spec: dict) -> list[str]:
    """What is wrong with one `{name, args}` of `translation.measures`."""
    if set(spec) != {"name", "args"} or not set(spec["args"]) <= MEASURE_ARGS:
        return [f"translation.measures: each {{name, args}}, args among {sorted(MEASURE_ARGS)}"]
    if 1 + len(spec["args"].get("when", [])) > 2:
        return ["translation.measures: enter plus more than one `when` (hard rule 14)"]
    return []


def validate(draft: dict, source: dict[str, str], read: str, min_chars: int) -> list[str]:
    """Every reason a draft cannot be stored; empty when it can.

    Args:
        draft: The entry as the scout wrote it.
        source: The stored source by place (anchors.pages).
        read: "full text" or "abstract only": how the paper was fetched.
        min_chars: Shortest quote that counts as a sentence.
    """
    out = shape(draft)
    if out:
        return out
    out = rules(draft)
    only = "abstract" if read == "abstract only" else ""
    marks = draft["anchors"]
    out += [f"anchors: missing {k}" for k in ANCHORED if k not in marks]
    out += [f"anchors: unknown {k}" for k in marks if k not in ANCHORED]
    for name, path in ANCHORED.items():
        if name in marks:
            out += anchors.errors(marks[name], value(draft, path), name, source, min_chars, only)
    if marks.get("rule") == anchors.ABSENT:
        out.append("rule: a paper that states no rule is rejected (filter `no_rule`)")
    return out
