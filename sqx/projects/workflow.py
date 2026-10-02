#!/usr/bin/env python3
"""Give a donor clone every task of the workflow: keep the steps' own, add the ones it lacks."""

import re
import zipfile
from pathlib import Path

import yaml

from core.assetdata import doctrine, load
from sqx.projects.crosschecks import member_of
from sqx.projects.databanks import set_databank
from sqx.projects.setups import set_span
from sqx.projects.stage import STAGES, apply, titles
from sqx.projects.wfc import declare

SOURCE = "OOS"                        # the plain retest every added task is copied from
# The permanent order (owner, 2026-09-29): Cross Market → Cross TF → MC Retest. Cross TF reads
# the Cross Market survivors scaled (`input`, filled by `sqx.projects.crosstfload`, step 10.5);
# MC Retest reads the mothers CrossTF kept, without their siblings (`mothers`, filled the same
# way before step 13).
CROSSTF = {"title": "CrossTF", "input": "CrossTF_Input", "output": "CrossTF",
           "mothers": "CrossTF_Mothers"}


def steps() -> list[str]:
    """Every workflow step, in stages.yaml order, with the WFC last."""
    return list(yaml.safe_load(STAGES.read_text(encoding="utf-8"))) + ["wfc"]


def kept_members(config: str) -> set[str]:
    """The donor's task files a workflow project keeps: those some step runs.

    Args:
        config: The donor's config.xml as text.

    Returns:
        Task XML file names. `MC Trades` and the helper tasks go: no step runs them.
    """
    wanted = {t for s in steps() for t in titles(s)}
    return {f for f, t in re.findall(r'<Task\b[^>]*?taskXMLFile="([^"]*)"[^>]*?title="([^"]*)"',
                                     config) if t in wanted}


def add_task(members: dict[str, bytes], title: str, source: str) -> str:
    """Copy one retest task into a new member under a new title, switched off.

    Args:
        members: The .cfx contents, patched in place.
        title: The new task's title — the contract every harvest reads it by.
        source: The member copied, a retest task that has run.

    Returns:
        The new member's file name.
    """
    config = members["config.xml"].decode("utf-8")
    n = max(int(k) for k in re.findall(r"Retest-Task(\d+)\.xml", " ".join(members))) + 1
    member = f"Retest-Task{n}.xml"
    tag = re.search(rf'<Task\b[^>]*taskXMLFile="{re.escape(source)}"[^>]*/>', config).group(0)
    new = re.sub(r'name="[^"]*"', f'name="Retest strategies {n}"', tag)
    new = re.sub(r'taskXMLFile="[^"]*"', f'taskXMLFile="{member}"', new)
    new = re.sub(r'title="[^"]*"', f'title="{title}"', new)
    new = re.sub(r'active="[^"]*"', 'active="false"', new)
    members["config.xml"] = config.replace("</Tasks>", f"  {new}\n  </Tasks>", 1).encode("utf-8")
    members[member] = members[source]
    return member


def complete(members: dict[str, bytes]) -> list[str]:
    """Add the cross-timeframe task and the three WFC legs to a donor clone.

    Args:
        members: The .cfx contents after `keep`, patched in place.

    Returns:
        The titles added. Their databanks are wired by `rewire`, after the chain.
    """
    source = member_of(members["config.xml"].decode("utf-8"), SOURCE)
    added = [CROSSTF["title"]] + [t["title"] for t in doctrine()["wfc"]["tasks"]]
    for title in added:
        add_task(members, title, source)
    return added


def rewire(members: dict[str, bytes]) -> None:
    """Point the added tasks at their own databanks and declare them.

    Args:
        members: The .cfx contents after `chain_databanks`, patched in place.

    The chain hands each task the previous one's output, which is right for Build → OOS →
    markets and wrong for these: the cross-timeframe task reads the survivors loaded from
    its own folder, the eight MC Retest tasks all read the mothers Cross TF kept (they do
    not chain, `sqx.projects.mcretest`), and the three WFC legs all read the same batch of
    variants.
    """
    study = doctrine()["wfc"]
    wiring = ([(CROSSTF["title"], CROSSTF["input"], CROSSTF["output"])]
              + [(t, CROSSTF["mothers"], t) for t in titles("mcretest")]
              + [(t["title"], study["input"], t["databank"]) for t in study["tasks"]])
    for title, source, output in wiring:
        member = member_of(members["config.xml"].decode("utf-8"), title)
        text = set_databank(members[member].decode("utf-8"), "Input", source)[0]
        members[member] = set_databank(text, "Output", output)[0].encode("utf-8")
    names = sorted({n for _, i, o in wiring for n in (i, o)})
    members["config.xml"] = declare(members["config.xml"].decode("utf-8"), names).encode("utf-8")


def finish(cfx: Path, symbol: str) -> None:
    """Price the cross-timeframe task over its own span, then leave only Build and OOS on.

    Args:
        cfx: The installed workflow project, after `configure` priced every task at its type's
            segment.
        symbol: Asset name.

    `configure` prices every retest on `oos1`; the cross-timeframe check runs over
    `crosstf.segment` (build..oos1), and its extra timeframes inherit the main test's dates, so
    the main test has to carry that span or every cell is read over the wrong window.
    """
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    from sqx.projects import crosstf, crosstfsolo      # both import this module
    member = member_of(members["config.xml"].decode("utf-8"), CROSSTF["title"])
    text = set_span(members[member].decode("utf-8"), load(symbol), doctrine()["crosstf"]["segment"])
    members[member] = text[0].encode("utf-8")
    # The extra timeframes' tasks exist from the start, so step 11 only rewrites them and a
    # live session takes that without a restart (owner, 2026-10-01: «todas las tareas de golpe»).
    main = crosstf.set_main(text[0], symbol)[0]
    for solo in crosstfsolo.planned(crosstf.main_chart(main)[1]):
        crosstfsolo.write(members, main, solo)
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    apply(cfx, ["build", "oos"])
