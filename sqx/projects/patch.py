#!/usr/bin/env python3
"""Generic task-XML edits a build applies regardless of asset: template, caps, sync."""

import io
import re
import zipfile
from pathlib import Path

from core.store.write import atomic
from core.symbols import current
from sqx.projects import cfxio

SYNCED = "Auto-sync every 1 hour"
# What SQX's own stock Builder carries in `templateFile` while it builds Simple Strategies, on
# all three installs: the one value seen to mean "no template" (read 2026-10-02).
NO_TEMPLATE = "SQ3StrategyTemplateExample.sq4"
GENERATIONS = ("genetic-evolution", "random-generation")


def install_template(template: Path, target: Path) -> None:
    """Copy a template into an install with its old feed names translated (`core.symbols.current`).

    SQX resolves a template's own `lastSettings.xml` as a project resource: a feed renamed since
    the template was saved makes every later `action=start` answer «Project has unresolved
    resources», while the build itself runs (🔬 2026-10-01, AUDJPY_TICK). Whole file or
    nothing: a Build reading that stem never opens half a zip.
    """
    members = cfxio.members(template)
    whole = io.BytesIO()
    with zipfile.ZipFile(whole, "w", zipfile.ZIP_DEFLATED) as z:
        for n, blob in members.items():
            z.writestr(
                n,
                current(blob.decode("utf-8")).encode("utf-8")
                if n.endswith(".xml")
                else blob,
            )
    atomic(target, whole.getvalue(), seal=False)


def set_template(text: str, path: Path) -> str:
    """Point a Build task at one template and make it actually use it.

    Args:
        text: A task XML.
        path: Absolute path of the .sqx inside the install that will build.

    Returns:
        The task XML with templateFile replaced and StrategyType forced to "template".
        The second half is the free gate: with type="simple" SQX builds generically and
        ignores the template, with no error anywhere (OPEN.md issue 9).
    """
    text = re.sub(r'templateFile="[^"]*"', f'templateFile="{path}"', text)
    return re.sub(r'(<StrategyType[^>]*?)type="[^"]*"', r'\1type="template"', text)


def set_simple(text: str, side: str) -> str:
    """Make a Build task generate Simple Strategies — no template — on one market side.

    Args:
        text: A task XML.
        side: "long" or "short" (hard rule 13: never both in one build).

    Returns:
        The task with StrategyType "simple" and no template named, and `<MarketSides>` on
        that side with both symmetries off. `<MarketSides type=>` is the «Long / Short /
        Both» switch of «What to build»: the owner's own projects carry "long" or "short"
        with the symmetries false, the stock Builder "both" with EntrySymmetry true. A
        template's direction comes from its rules instead, so this is the only direction
        gate a Simple Strategy has.
    """
    text = re.sub(r'(<StrategyType[^>]*?)type="[^"]*"', r'\1type="simple"', text)
    text = re.sub(r'templateFile="[^"]*"', f'templateFile="{NO_TEMPLATE}"', text)
    text = re.sub(r'<MarketSides type="[^"]*"', f'<MarketSides type="{side}"', text)
    return re.sub(r"<(EntrySymmetry|ExitSymmetry)>[^<]*</", r"<\1>false</", text)


def set_generation(text: str, mode: str) -> str:
    """Choose how the Build searches: one of GENERATIONS.

    Args:
        text: A task XML.
        mode: "genetic-evolution", or "random-generation" for a population's random twin.

    Returns:
        The task with only `<BuildMode generationType=>` changed; `tasksettings.set_genetic`
        keeps that attribute when it copies the owner's block over the rest.
    """
    return re.sub(r'(<BuildMode generationType=")[^"]*"', rf'\g<1>{mode}"', text)


def set_caps(text: str, strategies: int, minutes: int) -> str:
    """Cap how much the builder may produce and how long it may run.

    Args:
        text: A task XML.
        strategies: MaxStrategies, the databank-full stop.
        minutes: Wall-clock cap on the run.

    Returns:
        The task XML with both caps applied. A build with no cap inherits the donor's,
        which on XAUUSD is 10,000 strategies and 90 minutes.
    """
    text = re.sub(
        r"<MaxStrategies>\d+</MaxStrategies>",
        f"<MaxStrategies>{strategies}</MaxStrategies>",
        text,
    )
    return re.sub(
        r'(<StopCondition[^>]*passedStrategies=")\d+("[^>]*hours=")\d+("[^>]*minutes=")\d+',
        rf"\g<1>{strategies}\g<2>{minutes // 60}\g<3>{minutes % 60}",
        text,
    )


def sync_databanks(config: str) -> tuple[str, list[str]]:
    """Make every databank of the project write itself to disk.

    Args:
        config: The project's config.xml as text.

    Returns:
        The config and the databanks changed. The donor ships its build outputs as
        "Auto-sync never", which builds fine and leaves the directory empty, so nothing
        outside SQX can read the result and /curate has no files to act on.
    """
    changed = re.findall(
        r'<Databank name="([^"]*)"[^>]*syncType="Auto-sync never"', config
    )
    return re.sub(
        r'(<Databank name="[^"]*"[^>]*syncType=")Auto-sync never',
        rf"\g<1>{SYNCED}",
        config,
    ), changed
