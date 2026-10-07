#!/usr/bin/env python3
"""Cross TF's extra timeframes, each a retest of its own copied from `CrossTF` — D1 on MetaTrader 4."""

import re

from core.assetdata import doctrine
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.databanks import set_databank
from sqx.projects.tasksettings import set_engine, set_timeframe
from sqx.projects.wfc import declare
from sqx.projects.workflow import CROSSTF, CROSSTF_BUILD, add_task

# Owner, 2026-09-30: a timeframe is a task, never a block of the cross-check (its export cannot
# be split on one symbol), and D1 runs on MetaTrader 4: a D1 strategy only enters at 00:00 and a
# prop firm's session opens at 00:05, so on the MetaTrader 5 engine it traded nothing.
TASK = re.compile(r'title="(CrossTF [A-Z]+\d+)"')
PHASE2 = re.compile(r'title="(CrossTF ([A-Z]+\d+) build)"')      # `CROSSTF_BUILD`'s title


def planned(source: str, only: list[str] | None = None, d: dict | None = None) -> list[dict]:
    """The extra timeframes the doctrine asks for from one source timeframe, as tasks.

    Args:
        source: The mothers' timeframe, e.g. "H1".
        only: The timeframes of the doctrine's list this run reads; all of them when None.
            The criteria calibration of 2026-10-02 leaves D1 out (owner: «quítalo» — every
            D1 sibling of an H1 Simple Strategy is clamped) without touching the doctrine.
        d: The doctrine; `core.assetdata.doctrine()` when None (tests pass their own).

    Returns:
        One {timeframe, title, databank, engine} per extra timeframe of `crosstf.timeframes`,
        in its order; the engine is `crosstf.engines`' for that timeframe, else the doctrine's.
    """
    d = d or doctrine()
    study = d["crosstf"]
    return [{"timeframe": tf, "title": f"{CROSSTF['title']} {tf}",
             "databank": f"{CROSSTF['output']}_{tf}",
             "engine": (study.get("engines") or {}).get(tf, d["engine"])}
            for tf in study["timeframes"][source] if only is None or tf in only]


def phase2(source: str, d: dict | None = None) -> list[dict]:
    """The phase-2 twins of `planned`: the same timeframes but D1, named by `CROSSTF_BUILD`.

    Args:
        source: The mothers' timeframe.
        d: The doctrine, as in `planned`.

    Returns:
        `planned` rows with the build title and databank, plus `segment`. `write` them with
        the CrossTF task text priced over that segment.
    """
    b = CROSSTF_BUILD
    return [{**s, "title": b["title"].format(tf=s["timeframe"]),
             "databank": b["databank"].format(tf=s["timeframe"]), "segment": b["segment"]}
            for s in planned(source, d=d) if s["timeframe"] not in b["skip"]]


def present_phase2(config: str) -> list[dict]:
    """The phase-2 tasks a project carries — [] for one created before they existed.

    Returns:
        One {timeframe, title, databank} per task, in config order.
    """
    return [{"timeframe": tf, "title": title,
             "databank": CROSSTF_BUILD["databank"].format(tf=tf)}
            for title, tf in PHASE2.findall(config)]


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
