#!/usr/bin/env python3
"""Cross TF's extra timeframes, each a retest of its own copied from `CrossTF` — D1 on MetaTrader 4."""

import re

from core.assetdata import doctrine
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.databanks import set_databank
from sqx.projects.tasksettings import set_engine, set_timeframe
from sqx.projects.wfc import declare
from sqx.projects.workflow import CROSSTF, add_task

# Owner, 2026-09-30: a timeframe is a task, never a block of the cross-check (its export cannot
# be split on one symbol), and D1 runs on MetaTrader 4: a D1 strategy only enters at 00:00 and a
# prop firm's session opens at 00:05, so on the MetaTrader 5 engine it traded nothing.
TASK = re.compile(r'title="(CrossTF [A-Z]+\d+)"')


def planned(source: str) -> list[dict]:
    """The extra timeframes the doctrine asks for from one source timeframe, as tasks.

    Args:
        source: The mothers' timeframe, e.g. "H1".

    Returns:
        One {timeframe, title, databank, engine} per extra timeframe of `crosstf.timeframes`,
        in its order; the engine is `crosstf.engines`' for that timeframe, else the doctrine's.
    """
    d = doctrine()
    study = d["crosstf"]
    return [{"timeframe": tf, "title": f"{CROSSTF['title']} {tf}",
             "databank": f"{CROSSTF['output']}_{tf}",
             "engine": (study.get("engines") or {}).get(tf, d["engine"])}
            for tf in study["timeframes"][source]]


def present(config: str) -> list[str]:
    """The extra-timeframe Cross TF tasks a project already carries, by title."""
    return TASK.findall(config)


def write(members: dict[str, bytes], crosstf_text: str, solo: dict) -> str:
    """Create or rewrite one separate task from the configured CrossTF task.

    Args:
        members: The .cfx contents, patched in place.
        crosstf_text: The CrossTF task XML just written by `crosstf.set_main`: same
            window, precision, costs and silenced acceptance.
        solo: One row of `planned`.

    Returns:
        The member written: every chart on `solo["timeframe"]`, every Setup on
        `solo["engine"]`, reading `CrossTF_Input` and writing its own databank.
    """
    config = members["config.xml"].decode("utf-8")
    member = member_of(config, solo["title"])
    if member is None:
        member = add_task(members, solo["title"], member_of(config, CROSSTF["title"]))
        members["config.xml"] = declare(members["config.xml"].decode("utf-8"),
                                        [solo["databank"]]).encode("utf-8")
    text = re.sub(r'(<RetestOnAdditionalMarkets\b[^>]*?)use="[^"]*"', r'\g<1>use="false"',
                  crosstf_text, count=1)
    text = set_engine(set_timeframe(text, solo["timeframe"])[0], solo["engine"])
    text = silence(text)[0]
    text = set_databank(text, "Input", CROSSTF["input"])[0]
    members[member] = set_databank(text, "Output", solo["databank"])[0].encode("utf-8")
    return member
