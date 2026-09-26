#!/usr/bin/env python3
"""The surgery every cross-check configurator repeats: find the task, switch it on, silence it."""

import re
from xml.etree import ElementTree

DELETE_FAILED = re.compile(r"<DeleteFailedStrategies>\w+")


def member_of(config: str, title: str) -> str | None:
    """The task XML member the project's task with this title points at.

    Args:
        config: The project's config.xml as text.
        title: The task's title attribute, e.g. "SPP IS".

    Returns:
        The member name, or None when the project has no such task. The title is what the
        GUI shows and what a clone keeps; the member name is an index SQX assigns and
        changes between projects, so nothing here addresses a task by member.
    """
    tag = next((t for t in ElementTree.fromstring(config).find("Tasks")
                if t.get("title") == title), None)
    return tag.get("taskXMLFile") if tag is not None else None


def active(config: str, title: str, on: bool) -> str:
    """Switch one task of the project on or off by the title the GUI shows.

    Args:
        config: The project's config.xml as text.
        title: The task's title attribute.
        on: Whether SQX runs it when the project runs.

    Returns:
        The config with that task's `active` rewritten. A task the study does not want is
        left in place and switched off rather than deleted: the decision is reversible,
        and a project missing a task looks like a different project.
    """
    tag = re.search(rf'<Task\b[^>]*title="{re.escape(title)}"[^>]*/>', config).group(0)
    return config.replace(tag, re.sub(r'active="[^"]*"', f'active="{str(on).lower()}"', tag), 1)


def enable(text: str, name: str) -> str:
    """Turn one cross-check on, and the master switch it hangs from.

    Args:
        text: A task XML.
        name: Element name, e.g. "OptProfileSysParamPermutation".

    Returns:
        The task with both switched on. `<CrossChecks use="false">` is the parent, and an
        enabled cross-check under a disabled parent runs nothing and says nothing — which
        is exactly what `doctrine.apply_doctrine` leaves behind, since it writes
        `crosschecks.default: []` into every task that has no generator.
    """
    text = re.sub(rf'<{name} use="(?:true|false)"', f'<{name} use="true"', text, count=1)
    return re.sub(r'<CrossChecks use="(?:true|false)"', '<CrossChecks use="true"',
                  text, count=1)


def silence(text: str) -> tuple[str, int]:
    """Leave the task unable to drop a strategy from its own output.

    Args:
        text: A task XML.

    Returns:
        The task and how many acceptance conditions were turned off. Every active
        condition of a donor task lives inside `<CrossChecks>` (counted 2026-09-23 on the
        frozen donor: 13 in the WFM task, 19 in each SPP task, all of them there), and
        several belong to cross-checks this task does not even run. They all go: a task
        that deletes what fails turns a reading into a filter, and then the only thing the
        study can say at the end is how many survived — never which test killed which
        strategy. The verdict is taken in Python and applied with `/curate`.
    """
    text = DELETE_FAILED.sub("<DeleteFailedStrategies>false", text)
    return re.subn(r'(<Condition\s+)use="true"', r'\g<1>use="false"', text)


def recommended(block: str) -> str:
    """Permute SQX's recommended parameters, and nothing else.

    Args:
        block: A cross-check element carrying a <WhatToParametrize> section — the SPP and
            the walk-forward matrix both do.

    Returns:
        The element with `type="0"`, `Recommended` true and every hand-picked family
        false. The donor's SPP task carries `type="1"` with periods, constants and used
        exit parameters ticked, which permutes things the strategy does not key on and
        inflates the run for nothing (owner's default, 2026-09-22).
    """
    found = re.search(r"<WhatToParametrize\b.*?</WhatToParametrize>", block, re.S)
    inner = re.sub(r'type="\d+"', 'type="0"', found.group(0), count=1)
    inner = re.sub(r"<Recommended>(?:true|false)</Recommended>",
                   "<Recommended>true</Recommended>", inner, count=1)
    for family in ("Periods", "Shifts", "Constants", "OtherParams", "EntryParams",
                   "EntryLogic", "ExitParamsUsed", "ExitParamsUnused", "BooleanParams"):
        inner = re.sub(rf"<{family}>(?:true|false)</{family}>", f"<{family}>false</{family}>",
                       inner, count=1)
    return block[:found.start()] + inner + block[found.end():]


def others_on(text: str, keep: str) -> list[str]:
    """Which other cross-checks of this task would also run.

    Args:
        text: A task XML.
        keep: The one this study means to run.

    Returns:
        The names of every other enabled cross-check, in file order. A project cloned by
        `sqx/projects/builder.py` arrives with all of them off, because the doctrine writes
        `crosschecks.default: []`; one that did not go through it can carry the donor's,
        and a walk-forward matrix task that also runs a Monte Carlo retest costs hours
        nobody asked for and writes a databank nobody can attribute.
    """
    block = re.search(r"<CrossChecks\b.*?</CrossChecks>", text, re.S)
    return [child.tag for child in ElementTree.fromstring(block.group(0))
            if child.get("use") == "true" and child.tag != keep]
