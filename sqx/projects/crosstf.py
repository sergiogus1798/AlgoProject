#!/usr/bin/env python3
"""Write the cross-timeframe check: the same asset and costs, one retest per timeframe."""

import argparse
import json
import re
import zipfile
from datetime import date
from pathlib import Path

from core.assetdata import doctrine, load
from core.datapaths import crosstf_dir
from sqx.projects import crosstfsolo
from sqx.projects.configure import running_install
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.setups import set_span, span
from sqx.projects.stage import just, own, titles
from sqx.projects.tasksettings import set_precision

MAIN_CHART = re.compile(r'<Chart symbol="([^"]+)" timeframe="([^"]+)"')
MAIN_DATES = re.compile(r'<Setup dateFrom="([^"]+)" dateTo="([^"]+)"')

# Owner, 2026-09-30: every timeframe runs as a task of its own, never as a block of
# `RetestOnAdditionalMarkets`. SQX's `data=all` export interleaves the blocks by open time, and
# on one symbol nothing tells them apart: the k-th occurrence of a ticket read the blocks by
# how fast each traded (from H1, M30's trades were read as H1's). One task, one databank, one
# unambiguous export — and D1 on MetaTrader 4, which asks for no session.


def main_chart(text: str) -> tuple[str, str]:
    """The feed and timeframe the task's own main test runs on.

    Args:
        text: A task XML.

    Returns:
        (feed, timeframe). Read from the task rather than asked for, because this is the
        block every other block is compared against and guessing it wrong is silent.
    """
    found = MAIN_CHART.search(text)
    return found.group(1), found.group(2)


def main_window(text: str) -> tuple[str, str]:
    """The window the task's own main test runs on, as (dateFrom, dateTo)."""
    found = MAIN_DATES.search(text)
    return found.group(1), found.group(2)


def set_main(text: str, symbol: str) -> tuple[str, int, str]:
    """Put the source task on `crosstf.segment` at `crosstf.precision`, cross-check off.

    Args:
        text: The `CrossTF` task XML.
        symbol: The asset, for its declared costs.

    Returns:
        The task, how many acceptance conditions were silenced, and a warning about the
        window — empty when the task runs the declared span. Every other timeframe's task is
        copied from this one (`crosstfsolo.write`), so it carries the same window and costs.
    """
    study = doctrine()["crosstf"]
    if study["conditions"]:
        raise SystemExit("`crosstf.conditions` de assets/_build.yaml ya no esta vacio: esta "
                         "prueba es una medicion, no una puerta, y escribir condiciones no "
                         "esta implementado. Quitalas o dilo explicitamente.")
    data = load(symbol)
    start, end, _ = span(data, study["segment"])
    text = set_precision(set_span(text, data, study["segment"])[0], study["precision"])
    text = re.sub(r'(<RetestOnAdditionalMarkets\b[^>]*?)use="[^"]*"', r'\g<1>use="false"',
                  text, count=1)
    # Every condition of the task, not only this check's: 🔬 2026-09-25 a clone carried live
    # conditions elsewhere (the OOS copy, with DeleteFailedStrategies true).
    text, silenced = silence(text)
    live = main_window(text)
    warning = ("" if live == (start, end) else
               f"⚠️  la tarea corre {live[0]} a {live[1]}, no {start} a {end}: configura la "
               f"tarea con el segmento `{study['segment']}`.")
    return text, silenced, warning


def wire(cfx: Path, symbol: str, day: str) -> dict:
    """Write `CrossTF` and one task per extra timeframe, and record which databank is which.

    Args:
        cfx: The project's project.cfx, no install holding it.
        symbol: Asset name.
        day: Fabrication day the `blocks.json` is filed under (`core.datapaths.crosstf_dir`).

    Returns:
        `task`, `blocks` (the source timeframe first), `databanks` (in the same order),
        `tasks` (each extra timeframe's row of `crosstfsolo.planned`), `silenced`, `warning`,
        `staged` and `out`.
    """
    held = running_install(cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Paralo: bin/sqx-worker.sh --role {held} stop")
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    task = member_of(members["config.xml"].decode("utf-8"), "CrossTF")
    text, silenced, warning = set_main(members[task].decode("utf-8"), symbol)
    members[task] = text.encode("utf-8")
    source = main_chart(text)[1]
    extra = crosstfsolo.planned(source)
    for solo in extra:
        crosstfsolo.write(members, text, solo)
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    staged = own(cfx, "crosstf")
    just(cfx, titles("crosstf") + [s["title"] for s in extra])
    blocks = [source] + [s["timeframe"] for s in extra]
    databanks = ["CrossTF"] + [s["databank"] for s in extra]
    # The run's own record: assets/_build.yaml can change after this (Q17), and the study
    # must score these cells on the bars this run actually holds (OPEN.md #80).
    out = crosstf_dir(cfx.parent.name, day)
    out.mkdir(parents=True, exist_ok=True)
    (out / "blocks.json").write_text(json.dumps({"blocks": blocks, "databanks": databanks,
                                                 "tasks": extra}, indent=2), encoding="utf-8")
    return {"task": task, "blocks": blocks, "databanks": databanks, "tasks": extra,
            "silenced": silenced, "warning": warning, "staged": staged, "out": out}


def main() -> None:
    """Write the cross-timeframe tasks of one project, and report which databank is which."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--day", default=date.today().isoformat(),
                    help="dia de fabricacion bajo el que se archiva blocks.json "
                         "(core.datapaths.crosstf_dir); por defecto hoy, igual que "
                         "sqx.variants.scale")
    a = ap.parse_args()
    got = wire(a.cfx, a.symbol, a.day)
    print(f"{got['task']}: {got['blocks'][0]}, costes de {a.symbol} a "
          f"`{doctrine()['crosstf']['segment']}`")
    for s in got["tasks"]:
        print(f"«{s['title']}»: {s['timeframe']} con {s['engine']} -> {s['databank']}")
    print(f"{got['silenced']} condiciones de aceptacion apagadas — esto es evidencia, no un filtro")
    if got["warning"]:
        print(got["warning"])
    print(got["staged"])
    print(f"blocks.json -> {got['out']}")


if __name__ == "__main__":
    main()
