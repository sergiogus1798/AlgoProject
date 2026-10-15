#!/usr/bin/env python3
"""Write the MT5 bridge's check into a custom project: one retest per prop firm, and the EA's export."""

import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from core import assetdata, sqxfile
from core.assetdata import doctrine
from sqx.inspect.strategymeta import rules
from sqx.projects import cfxio, charts
from sqx.projects.crosschecks import silence
from sqx.projects.databanks import set_databank
from sqx.projects.perturbations import OUT_OF_SAMPLE
from sqx.projects.setups import SETUP, set_data_range, write_setup
from sqx.projects.tasksettings import set_money_management
from sqx.projects.wfc import declare, retitle
from typing import Any, TypedDict
from collections.abc import Mapping

SAVE_MEMBER = "SaveToFiles-Task1.xml"
METHODS = ("FixedSize", "FixedAmount")  # what the EA can be given on both sides


def _ms(day: str, end: bool) -> int:
    """YYYY-MM-DD as the epoch milliseconds a <Resources><Symbol> range carries, the end day
    whole — `core.assetdata._ms`'s convention: UTC, the closing bound the next midnight."""
    return assetdata._ms(date.fromisoformat(day), end)


class Sizing(TypedDict):
    """The sizing method a strategy file carries and its parameters, as XML text."""

    method: str
    params: dict[str, str]


def own_sizing(strategy: Path) -> Sizing:
    """The sizing the strategy file itself carries, as `tasksettings.set_money_management` takes it.

    Returns:
        {"method", "params"} from `strategy_Portfolio.xml`'s <MoneyManagement>, e.g.
        {"method": "FixedSize", "params": {"Size": "0.1"}}. FixedSize and FixedAmount (owner,
        2026-10-15, encargo 61-4a: the sizing lives in the strategy); another method is
        refused rather than translated by guess into the EA.
    """
    with zipfile.ZipFile(strategy) as z:
        xml = z.read("strategy_Portfolio.xml").decode("utf-8")
    found = re.search(
        r'<MoneyManagement type="(\w+)">(.*?)</MoneyManagement>', xml, re.S
    )
    assert found is not None
    params = dict(
        re.findall(r'<Param key="#?(\w+?)#?"[^>]*>([^<]*)</Param>', found.group(2))
    )
    if found.group(1) not in METHODS:
        raise SystemExit(
            f"{strategy.stem} se dimensiona con {found.group(1)}: sólo {' y '.join(METHODS)} "
            "se copian a los dos lados (dueño, 2026-09-29: el de la estrategia)"
        )
    return {"method": found.group(1), "params": params}


def mode_sizing(mode: str, value: float) -> Sizing:
    """The sizing one concordance mode trades on both sides (encargo 61-4d).

    Args:
        mode: "lot" (a fixed lot) or "risk" (a fixed risk per trade from the stop).
        value: Lots for "lot", USD risked per trade for "risk".

    Returns:
        FixedSize {"Size"} or FixedAmount {"RiskedMoney"}, as `own_sizing` returns them.
    """
    if mode == "lot":
        return {"method": "FixedSize", "params": {"Size": f"{value:g}"}}
    if mode == "risk":
        return {"method": "FixedAmount", "params": {"RiskedMoney": f"{value:g}"}}
    raise ValueError(f"modo de dimensionado desconocido: {mode!r} (lot o risk)")


def has_stop(strategy: Path) -> bool:
    """Whether any entry order of the strategy carries a stop loss: `risk` mode sizes from it."""
    root = sqxfile.xml(strategy)
    return any(o["stop_loss"] for o in rules.orders(root))


def write_task(
    text: str,
    feed: str,
    costs: dict,
    window: tuple[str, str],
    databanks: tuple[str, str],
    sizing: Mapping[str, Any],
) -> str:
    """Turn one of the donor's retests into one firm's backtest of the strategy.

    Args:
        text: A retest task XML.
        feed: The SQX feed the task trades, the asset's.
        costs: The firm's costs, as `mt5.verify.conditions.for_sqx` returns them.
        window: (from, to) as YYYY-MM-DD, both days included.
        databanks: (input, output).
        sizing: `own_sizing()`: the strategy's own method, which the EA is also given.

    Returns:
        The task: the firm's costs over the window, no out-of-sample split, every cross-check
        off and every acceptance condition silenced, and the strategy's own sizing (owner,
        2026-09-29). ⚠️ `customSettings="false"` does NOT mean «the strategy's own»: the task's
        <MoneyManagement> method flags are what SQX applies (🔬 2026-09-29, the donor's ATR
        sizing traded 0.07-0.47 lots on a strategy that stores FixedSize 0.1).
    """
    a, b = (w.replace("-", ".") for w in window)
    chart = f'<Chart symbol="{feed}"'
    text = SETUP.sub(
        lambda m: (
            write_setup(m.group(0), costs, a, b) if chart in m.group(0) else m.group(0)
        ),
        text,
    )
    text, _ = set_data_range(
        text, {"sqx_symbol": feed}, (_ms(window[0], False), _ms(window[1], True))
    )
    text = OUT_OF_SAMPLE.sub('<OutOfSample showGraph="false" />', text, count=1)
    text = set_databank(text, "Input", databanks[0])[0]
    text = set_databank(text, "Output", databanks[1])[0]
    if 'retestSelected="false"' not in text:
        text = text.replace("<Databanks>", '<Databanks retestSelected="false">')
    text = re.sub(
        r'<CrossChecks use="(?:true|false)"', '<CrossChecks use="false"', text, count=1
    )
    text = set_money_management(text, {**doctrine()["money_management"], **sizing})
    return silence(text)[0]


def save_task(input_bank: str, dest: Path, generator: str, magic: int) -> str:
    """A SaveToFiles task that writes the input's strategies as EA source code and nothing else.

    Args:
        input_bank: The databank holding the strategy as loaded — its own settings.
        dest: Folder the .mq5 lands in.
        generator: SQX's internal name for the MQL5 generator,
            "Expert Advisor for MetaTrader5 (*.MQ5)" — not the GUI's «MetaTrader 5 (*.mq5)».
        magic: The first magic number; SaveToFiles numbers the EAs from it.

    Returns:
        The task XML. `sqcli` has no verb that writes code
        (`knowhow/sqx-drive/export-mql5-source-headless.md`); this task is the way.
    """
    return f"""<Settings>
  <SaveToFiles>
    <DestDirectorySqx />
    <DestDirectoryStr />
    <SaveInSqxFormat>false</SaveInSqxFormat>
    <SaveInStrFormat>false</SaveInStrFormat>
    <DestDirectoryDatabank />
    <DestDirectoryTrades />
    <DestDirectoryHtml />
    <DestDirectoryPdf />
    <DestDirectorySC>{dest}</DestDirectorySC>
    <ExportDatabank>false</ExportDatabank>
    <ExportTrades>false</ExportTrades>
    <SaveInHtmlFormat>false</SaveInHtmlFormat>
    <SaveInPdfFormat>false</SaveInPdfFormat>
    <SaveSourceCode type="{generator}">true</SaveSourceCode>
    <OverwriteFiles>true</OverwriteFiles>
    <MNActive>true</MNActive>
    <MNValue>{magic}</MNValue>
    <Data>all</Data>
    <Format>csv</Format>
    <UseComma>false</UseComma>
    <SetNoteActive>false</SetNoteActive>
    <SetNoteType>custom</SetNoteType>
    <SetNoteCustom />
  </SaveToFiles>
  <Databanks>
    <Databank label="Input databank" name="Input" value="{input_bank}" />
  </Databanks>
  <CrossChecks>
    <RetestOnAdditionalMarkets />
    <WhatIf />
    <MonteCarloManipulation use="false" />
    <MonteCarloRetest />
    <OptProfileSysParamPermutation />
    <WalkForwardOptimization />
    <WalkForwardMatrix />
    <SequentialOptimization />
    <RetestWithHigherPrecision />
  </CrossChecks>
  <Resources>
    <Symbols />
    <Brokers />
    <Instruments />
    <Sessions />
    <CustomIndicators />
    <CustomBlocks />
  </Resources>
</Settings>
"""


class Configured(TypedDict):
    """What `configure` set on the step-26 tasks."""

    project: str | None
    input: str
    tasks: list[dict[str, Any]]
    export: str


def configure(
    cfx: Path,
    feed: str,
    window: tuple[str, str],
    firms: dict[str, dict],
    mq5_dir: Path,
    cfg: dict,
    sizing: Mapping[str, Any],
    strategy: Path | None = None,
) -> Configured:
    """Write one retest per firm, and the EA's export, into a project the builder just cloned.

    Args:
        cfx: The project.cfx, not held by a running install (hard rule 4).
        feed: The asset's SQX feed.
        window: (from, to) as YYYY-MM-DD.
        firms: {firm: costs}, in the order the tasks are written.
        mq5_dir: Where SaveToFiles writes the EA.
        cfg: The `sqx` block of `mt5/verify/config.yaml`.
        sizing: `own_sizing()` of the strategy.
        strategy: The .sqx under test; each retest gets the extra charts it reads.

    Returns:
        {"project", "input", "tasks": [{firm, title, member, output}], "export": title}.
        Every task switched on, and only these: `action=start` runs the active ones.
    """
    members = cfxio.members(cfx)
    config = members["config.xml"].decode("utf-8")
    retests = [m for m in cfg["donor_members"] if m in members]
    if len(retests) < len(firms):
        raise SystemExit(
            f"{cfx.parent.name} tiene {len(retests)} retests del donante y hacen "
            f"falta {len(firms)}: {', '.join(cfg['donor_members'])}"
        )
    config = re.sub(r'(<Task\b[^>]*?)active="true"', r'\g<1>active="false"', config)
    rows, extra = [], charts.wanted(strategy) if strategy else []
    for (firm, costs), member in zip(firms.items(), retests):
        output = cfg["output_prefix"] + firm
        task = write_task(
            members[member].decode("utf-8"),
            feed,
            costs,
            window,
            (cfg["input"], output),
            sizing,
        )
        members[member] = charts.ensure(task, extra)[0].encode("utf-8")
        title = cfg["task_title"].format(firm=firm.upper())
        config = retitle(config, member, title)
        rows.append({"firm": firm, "title": title, "member": member, "output": output})

    # The EA is exported from the first firm's retest, not from the strategy as loaded: SQX
    # writes the sizing its last backtest ran, and a strategy built on the doctrine carries
    # ATRRiskBasedSizingFixedRisk — a user snippet with no MetaTrader 5 template, so the
    # export wrote nothing (📓 2026-09-30). The retest ran the strategy's own FixedSize.
    members[SAVE_MEMBER] = save_task(
        rows[0]["output"], mq5_dir, cfg["generator"], cfg["magic"]
    ).encode("utf-8")
    config = re.sub(rf'\s*<Task\b[^>]*taskXMLFile="{SAVE_MEMBER}"[^>]*/>', "", config)
    config = config.replace(
        "</Tasks>",
        f'    <Task name="Save to files" type="SaveToFiles" '
        f'taskXMLFile="{SAVE_MEMBER}" active="true" '
        f'title="{cfg["export_title"]}" />\n  </Tasks>',
        1,
    )
    config = declare(config, [cfg["input"]] + [r["output"] for r in rows])
    members["config.xml"] = config.encode("utf-8")
    cfxio.write(cfx, members)
    return {
        "project": ElementTree.fromstring(config).get("name"),
        "input": cfg["input"],
        "tasks": rows,
        "export": cfg["export_title"],
    }
