#!/usr/bin/env python3
"""Generic task-XML edits a build applies regardless of asset: template, caps, sync."""

import re
from pathlib import Path

SYNCED = "Auto-sync every 1 hour"


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
    text = re.sub(r"<MaxStrategies>\d+</MaxStrategies>",
                  f"<MaxStrategies>{strategies}</MaxStrategies>", text)
    return re.sub(r'(<StopCondition[^>]*passedStrategies=")\d+("[^>]*hours=")\d+("[^>]*minutes=")\d+',
                  rf"\g<1>{strategies}\g<2>{minutes // 60}\g<3>{minutes % 60}", text)


def sync_databanks(config: str) -> tuple[str, list[str]]:
    """Make every databank of the project write itself to disk.

    Args:
        config: The project's config.xml as text.

    Returns:
        The config and the databanks changed. The donor ships its build outputs as
        "Auto-sync never", which builds fine and leaves the directory empty, so nothing
        outside SQX can read the result and /curate has no files to act on.
    """
    changed = re.findall(r'<Databank name="([^"]*)"[^>]*syncType="Auto-sync never"', config)
    return re.sub(r'(<Databank name="[^"]*"[^>]*syncType=")Auto-sync never',
                  rf"\g<1>{SYNCED}", config), changed
