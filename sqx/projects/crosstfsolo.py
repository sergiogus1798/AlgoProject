#!/usr/bin/env python3
"""Cross TF's extra timeframes, each a retest of its own copied from `CrossTF`."""

import re

from core.assetdata import doctrine
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.databanks import set_databank
from sqx.projects.tasksettings import set_engine, set_timeframe
from sqx.projects.wfc import declare
from sqx.projects.workflow import CROSSTF, CROSSTF_BUILD, add_task
from core.xmlget import hit

# Owner, 2026-09-30: a timeframe is a task, never a block of the cross-check (its export cannot
# be split on one symbol). D1 was removed from Cross TF on 2026-10-09 (owner).
TASK = re.compile(r'title="(CrossTF [A-Z]+\d+)"')
PHASE2 = re.compile(r'title="(CrossTF ([A-Z]+\d+) build)"')      # `CROSSTF_BUILD`'s title


def planned(source: str, only: list[str] | None = None, d: dict | None = None) -> list[dict]:
    """The extra timeframes the doctrine asks for from one source timeframe, as tasks.

    Args:
        source: The mothers' timeframe, e.g. "H1".
        only: The timeframes of the doctrine's list this run reads; all of them when None.
        d: The doctrine; `core.assetdata.doctrine()` when None (tests pass their own).

    Returns:
        One {timeframe, title, databank, engine} per extra timeframe of `crosstf.timeframes`,
        in its order; the engine is the doctrine's.
    """
    d = d or doctrine()
    study = d["crosstf"]
    if source not in study["timeframes"]:
        raise SystemExit(f"assets/_build.yaml: `crosstf.timeframes` no dice en qué timeframes se "
                         f"reprueba una madre {source} — decídelo antes de construir.")
    return [{"timeframe": tf, "title": f"{CROSSTF['title']} {tf}",
             "databank": f"{CROSSTF['output']}_{tf}",
             "engine": d["engine"]}
            for tf in study["timeframes"][source] if only is None or tf in only]


def phase2(source: str, d: dict | None = None) -> list[dict]:
    """The phase-2 twins of `planned`: the same timeframes, named by `CROSSTF_BUILD`.

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
            for s in planned(source, d=d)]


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
        member = add_task(members, solo["title"], hit(member_of(config, CROSSTF["title"])))
        members["config.xml"] = declare(members["config.xml"].decode("utf-8"),
                                        [solo["databank"]]).encode("utf-8")
    text = re.sub(r'(<RetestOnAdditionalMarkets\b[^>]*?)use="[^"]*"', r'\g<1>use="false"',
                  crosstf_text, count=1)
    text = set_engine(set_timeframe(text, solo["timeframe"])[0], solo["engine"])
    text = silence(text)[0]
    text = set_databank(text, "Input", CROSSTF["input"])[0]
    members[member] = set_databank(text, "Output", solo["databank"])[0].encode("utf-8")
    return member
