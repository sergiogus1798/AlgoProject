"""What a session adds to a stored entry: the owner's answer to its question, and its measures."""

from pathlib import Path

import yaml

from studies.research.literature import dedupe, schema, store

PROFILE = Path(__file__).parent.parent / "marketProfile" / "config.yaml"


def profile_measures() -> list[dict]:
    """The `measures` rows of the market profile's own config, read as data."""
    return yaml.safe_load(PROFILE.read_text(encoding="utf-8"))["measures"]


def clashes(specs: list[dict], entries: list[dict]) -> tuple[list[str], list[str]]:
    """Why some measures of an entry cannot be stored as they are.

    Args:
        specs: Its `translation.measures`.
        entries: Every stored entry.

    Returns:
        (names already used by the profile or by another entry, measures that are the same
        rule as an existing one — each as a sentence naming it).
    """
    measures = profile_measures()
    used = {m["name"] for m in measures} | {
        s["name"] for e in entries for s in e["translation"].get("measures", [])}
    names = [s["name"] for s in specs]
    taken = [f"translation.measures: the name {n} is taken" for n in names if n in used]
    taken += [f"translation.measures: the name {n} is repeated" for n in set(names)
              if names.count(n) > 1]
    twins = []
    for s in specs:
        twin = dedupe.same_rule(s["args"], entries, measures)
        if twin:
            twins.append(f"{s['name']} is the same rule as {twin}")
    return taken, twins


def answer(ident: str, number: int) -> str:
    """Write the owner's choice among the readings of an entry's question; returns the reading."""
    entry = next(e for e in store.entries() if e["id"] == ident)
    entry["question"]["answer"] = entry["question"]["readings"][number - 1]
    store.replace(entry)
    return entry["question"]["answer"]


def measures(ident: str, specs: list[dict]) -> list[str]:
    """Add measures to a stored entry — once its condition exists, or its question is answered.

    Returns:
        Every refusal; empty when the measures were written.
    """
    entries = store.entries()
    entry = next(e for e in entries if e["id"] == ident)
    wrong = [w for s in specs for w in schema.measure(s)]
    if entry.get("question") and not entry["question"]["answer"]:
        wrong.append("the entry's question is still open: the owner answers first")
    if wrong:
        return wrong
    taken, twins = clashes(specs, entries)
    if taken or twins:
        return taken + twins
    entry["translation"]["measures"] = entry["translation"].get("measures", []) + specs
    store.replace(entry)
    return []
