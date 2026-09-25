#!/usr/bin/env python3
"""Which databank each task of a project reads and which it writes."""

import re


def databanks(text: str) -> dict[str, str]:
    """Which databank one task reads and which it writes.

    Args:
        text: A task XML.

    Returns:
        {"Input": name, "Output": name} for the labels the task carries, missing keys when
        it carries neither.
    """
    return {m.group(1): m.group(2) for m in
            re.finditer(r'<Databank label="\w+ databank" name="(Input|Output)" value="([^"]*)"', text)}


def set_databank(text: str, which: str, value: str) -> tuple[str, str | None]:
    """Point one task's input or output at a databank.

    Args:
        text: A task XML.
        which: "Input" or "Output".
        value: Databank name, exactly as `config.xml` spells it — SQX matches on the string
            and silently ignores a name no `<Databank>` declares.

    Returns:
        The task and what the value was before, or None when the task has no such element.
    """
    pat = re.compile(rf'(<Databank label="\w+ databank" name="{which}" value=")([^"]*)(")')
    found = pat.search(text)
    return (pat.sub(rf"\g<1>{value}\g<3>", text, count=1), found.group(2)) if found else (text, None)


def chain_databanks(members: dict[str, bytes]) -> list[dict]:
    """Make each task read what the task before it wrote, in the config's own order.

    Args:
        members: The .cfx contents by member name, patched in place.

    Returns:
        One row per task: its member, what it writes, what it read before and what it reads
        now. The first task keeps whatever input the donor gave it — there is no previous
        output to hand it, and a Build on `genetic-evolution` seeds from the system databanks
        (`Initial population`, `Strategies to improve`), not from its `Input`.

    A donor's task chain is only correct for the tasks the donor shipped in the order it
    shipped them. Drop some with `--only` and the survivors still point where they used to:
    measured 2026-09-23, the additional-markets task read `Retest Markets - Family` — its OWN
    output — so the cross-market check would have run over an empty databank instead of the
    strategies the OOS retest passed. Nothing announces that; the task simply tests nothing.
    """
    config = members["config.xml"].decode("utf-8")
    order = re.findall(r'<Task\b[^>]*taskXMLFile="([^"]+)"', config)
    rows, previous = [], None
    for member in order:
        if member not in members:
            continue
        text = members[member].decode("utf-8")
        current = databanks(text)
        was = current.get("Input")
        if previous:
            text, was = set_databank(text, "Input", previous)
            members[member] = text.encode("utf-8")
        rows.append({"task": member, "writes": current.get("Output"),
                     "read_before": was, "reads": previous or was})
        previous = current.get("Output") or previous
    return rows
