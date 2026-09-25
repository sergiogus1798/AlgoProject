#!/usr/bin/env python3
"""Write the WFC/CSCV retest: one task per segment, each at its own costs, markets included."""

import argparse
import json
import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from core.assetdata import doctrine, load
from sqx.projects.configure import running_install
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.crossmarket import SETUPS, chosen, one_market
from sqx.projects.databanks import set_databank
from sqx.projects.perturbations import OUT_OF_SAMPLE
from sqx.projects.setups import bounds, set_costs
from sqx.projects.stage import own

CHECK = "RetestOnAdditionalMarkets"


def retitle(config: str, member: str, title: str) -> str:
    """Name one task of the project and switch it on.

    Args:
        config: The project's config.xml as text.
        member: The task XML file, e.g. "Retest-Task2.xml".
        title: The title the doctrine gives it, e.g. "WFC 2 OOS1".

    Returns:
        The config with that task renamed and active. The title is the contract the Python
        harvest reads the three databanks by, so it is written rather than assumed: a clone
        arrives carrying whatever the donor called its retest tasks.
    """
    tag = re.search(rf'<Task\b[^>]*taskXMLFile="{re.escape(member)}"[^>]*/>', config).group(0)
    named = re.sub(r'title="[^"]*"', f'title="{title}"', tag)
    return config.replace(tag, re.sub(r'active="[^"]*"', 'active="true"', named), 1)


def market_setups(symbol: str, segment: str, timeframe: str,
                  precision: int, engine: str) -> tuple[str, list, list]:
    """The extra markets of `_markets.yaml`, each over this segment at its own costs.

    Args:
        symbol: The main asset.
        segment: Which segment this task runs.
        timeframe: The project's timeframe.
        precision: testPrecision for every extra market.
        engine: Backtest engine name.

    Returns:
        The `<Setup>` elements, the markets written, and the ones left out — a market whose
        own costs are undeclared, or whose first bar is after this segment ends. The second
        list is reported and never guessed at: SQX would run an undeclared market at
        whatever default its instrument registry carries (hard rule 5).
    """
    start, end = bounds(load(symbol), segment)
    used, skipped = [], []
    for m in chosen(symbol):
        first = m["data_from"]
        if not m["costs_from"]:
            skipped.append(m | {"why": "sin costes declarados en assets/symbols/"})
        elif isinstance(first, date) and f"{first:%Y.%m.%d}" > end:
            skipped.append(m | {"why": f"sus datos empiezan en {first} y {segment} acaba "
                                       f"en {end}"})
        else:
            at = max(start, f"{first:%Y.%m.%d}") if isinstance(first, date) else start
            used.append(m | {"window": (at, end)})
    body = "".join(one_market(m["feed"], load(m["costs_from"]), segment, m["window"],
                              precision, engine, timeframe) for m in used)
    return body, used, skipped


def write_task(text: str, symbol: str, spec: dict, timeframe: str,
               study: dict, engine: str) -> tuple[str, dict]:
    """Turn one retest task into this segment's leg of the study.

    Args:
        text: A task XML.
        symbol: The main asset.
        spec: One entry of `wfc.tasks` — its title, segment and output databank.
        timeframe: The project's timeframe.
        study: The `wfc` block of the doctrine.
        engine: Backtest engine name.

    Returns:
        The task and what was written. The task's own window is the segment, whole, and
        `<OutOfSample>` is cleared: a leg that ran one segment IS one sample, and the split
        the studies downstream read is which task a curve came from, not a date inside it.
    """
    data = load(symbol)
    text, setups = set_costs(text, data, spec["segment"])
    text = OUT_OF_SAMPLE.sub('<OutOfSample showGraph="false" />', text, count=1)
    text = set_databank(text, "Input", study["input"])[0]
    text = set_databank(text, "Output", spec["databank"])[0]
    if 'retestSelected="false"' not in text:
        text = text.replace("<Databanks>", '<Databanks retestSelected="false">')

    used, skipped = [], []
    if study["markets"]:
        body, used, skipped = market_setups(symbol, spec["segment"], timeframe,
                                            study["precision"], engine)
        text = SETUPS.sub(rf'\g<1><Setups detailed="true">{body}</Setups>', text, count=1)
    text = re.sub(rf'(<{CHECK}\b[^>]*?)use="[^"]*"',
                  rf'\g<1>use="{str(bool(used)).lower()}"', text, count=1)
    if used:
        text = re.sub(r'<CrossChecks use="(?:true|false)"', '<CrossChecks use="true"',
                      text, count=1)
    # Every condition of the task, not only the market check's: `wfc.conditions` is empty.
    # 🔬 2026-09-25, the donor's build-leg task kept `AnnualPctReturn (OOS) > 0` active; a
    # build leg has no OOS, every variant failed it, and with evaluateAll="false" SQX then
    # never ran the nine markets -- the leg came back with USDJPY alone and no error.
    text, silenced = silence(text)
    window = bounds(data, spec["segment"])
    return text, {"setups": setups, "from": window[0], "to": window[1],
                  "markets": [m["feed"] for m in used], "silenced": silenced,
                  "skipped": {m["feed"]: m["why"] for m in skipped}}


def declare(config: str, names: list[str]) -> str:
    """Register every databank the legs read or write that the project does not declare.

    Args:
        config: The project's config.xml as text.
        names: The input databank and the three outputs.

    Returns:
        The config with one `<Databank>` per missing name, synced to disk like the rest.
        🔬 2026-09-25, on a project cloned from the donor: the tasks named `WFC Variants`
        and the three outputs, the project declared none of them, and SQX only loads the
        databanks its config lists -- the task had nothing to read, and a folder made by
        hand was not picked up either.
    """
    have = set(re.findall(r'<Databank name="([^"]*)"', config))
    last = max(map(int, re.findall(r'<Databank [^>]*position="(\d+)"', config)), default=0)
    new = "".join(f'    <Databank name="{name}" view="Default - Main data" '
                  f'syncType="Auto-sync every 1 hour" position="{last + 100 * i}" />\n'
                  for i, name in enumerate([n for n in names if n not in have], 1))
    return config.replace("</Databanks>", new + "  </Databanks>", 1)


def configure(cfx: Path, symbol: str, timeframe: str, members_in_order: list[str]) -> dict:
    """Write the three legs of the WFC/CSCV retest into one custom project.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install.
        symbol: Asset name, e.g. "XAUUSD".
        timeframe: The project's timeframe.
        members_in_order: Three task XML files, in the doctrine's task order — build, oos1,
            oos2. They are renamed to the doctrine's titles and switched on.

    Returns:
        One row per leg, plus the project name and the input databank they all read. The
        three do NOT chain: the same batch of variants goes into each, so the three panels
        are three readings of one population and not a funnel.
    """
    study = doctrine()["wfc"]
    engine = doctrine()["engine"]
    if study["conditions"]:
        raise SystemExit("`wfc.conditions` de assets/_build.yaml ya no esta vacio: una "
                         "variante descartada y una que perdio dinero son la misma cosa "
                         "para el que cuenta, y el PBO deja de significar nada.")
    if len(members_in_order) != len(study["tasks"]):
        raise SystemExit(f"--tasks pide {len(study['tasks'])} ficheros, en el orden de "
                         f"`wfc.tasks`: {', '.join(t['segment'] for t in study['tasks'])}")

    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    config = members["config.xml"].decode("utf-8")
    rows = []
    for spec, member in zip(study["tasks"], members_in_order):
        if member not in members:
            raise SystemExit(f"{member} no esta en {cfx.name}")
        text, done = write_task(members[member].decode("utf-8"), symbol, spec, timeframe,
                                study, engine)
        members[member] = text.encode("utf-8")
        config = retitle(config, member, spec["title"])
        rows.append({"member": member, **spec, **done})

    config = declare(config, [study["input"]] + [t["databank"] for t in study["tasks"]])
    members["config.xml"] = config.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return {"project": ElementTree.fromstring(config).get("name"),
            "input": study["input"], "tasks": rows}


def main() -> None:
    """Configure the three WFC/CSCV retest tasks of a custom project."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--timeframe", required=True, help="el timeframe del proyecto, e.g. M30")
    ap.add_argument("--tasks",
                    help="tres ficheros de tarea separados por comas, en el orden de "
                         "`wfc.tasks`: build, oos1, oos2. Sin el, las que ya llevan esos "
                         "titulos (un proyecto de `builder --workflow`)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    held = running_install(a.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al "
                         f"salir. Parala: bin/sqx-worker.sh --role {held} stop")
    with zipfile.ZipFile(a.cfx) as z:
        config = z.read("config.xml").decode("utf-8")
    members = (a.tasks.split(",") if a.tasks else
               [member_of(config, t["title"]) for t in doctrine()["wfc"]["tasks"]])
    done = configure(a.cfx, a.symbol, a.timeframe, members)
    staged = own(a.cfx, "wfc")
    if a.json:
        print(json.dumps(done, indent=2, default=str))
        return
    print(staged)

    print(f"{done['project']}  {a.symbol}  <- {done['input']} (las tres leen el MISMO lote)")
    for row in done["tasks"]:
        print(f"  ✓ {row['title']:<12} {row['segment']:<5} {row['from']}→{row['to']}  "
              f"-> {row['databank']:<10} {row['silenced']} condicion(es) apagada(s)")
        print(f"      mercados: {', '.join(row['markets']) or 'ninguno'}")
        for feed, why in row["skipped"].items():
            print(f"      ⚠️ sin {feed}: {why}")
    print("\noos2 se gasta aqui: `_policy.yaml` lo reserva al WFC y a la WFM, y esto es el "
          "WFC.\nEl veredicto se toma en Python (strategies/walkForwardCorrelation/).")


if __name__ == "__main__":
    main()
