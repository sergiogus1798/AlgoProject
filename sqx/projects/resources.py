#!/usr/bin/env python3
"""Swap a clone's inherited feed for the asset it is meant to trade, borrowing the definition."""

import re
import zipfile
from pathlib import Path

from core.symbols import current

SYMBOL = re.compile(r'<Symbol\b[^>]*?name="([^"]+)"[^>]*?>.*?</Symbol>', re.S)
CHART = re.compile(r'<Chart\b[^>]*?symbol="([^"]+)"')
INSTRUMENT = re.compile(r'<InstrumentInfo\b[^>]*?instrument="([^"]+)"[^>]*?/>')
BROKER = re.compile(r'<Broker\b[^>]*?id="([^"]+)"[^>]*?/>')


def main_feed(members: dict[str, bytes], build_member: str) -> str:
    """The feed a donor project was built around.

    Args:
        members: The .cfx contents by member name.
        build_member: The task whose first <Chart> defines it — the generator's own feed.

    Returns:
        The SQX symbol name, e.g. "XAUUSD_M1". Only this one is replaced, so
        the extra markets a cross-check task carries keep their own feeds.
    """
    return CHART.search(members[build_member].decode("utf-8")).group(1)


def definitions(source: Path, feed: str) -> tuple[str, str, str]:
    """One asset's three resource blocks, read out of a project that already trades it.

    Args:
        source: A project.cfx defining the feed. Read only — never written, so a live
            install may hold it open.
        feed: SQX symbol name to bring over.

    Returns:
        (the <Symbol> block, its <InstrumentInfo>, its <Broker>). The instrument definition
        must agree with SQX's own registry or the project refuses to start with "unresolved
        resources", so it is copied verbatim from a project SQX itself produced.

    Raises:
        SystemExit: When `source` does not define that feed either. Nothing is invented.
    """
    with zipfile.ZipFile(source) as z:
        for name in (n for n in z.namelist() if n.endswith(".xml") and n != "config.xml"):
            # A project written before SQX's feeds were renamed names them the old way.
            text = current(z.read(name).decode("utf-8", "replace"))
            block = next((m.group(0) for m in SYMBOL.finditer(text) if m.group(1) == feed), None)
            if not block:
                continue
            instrument = INSTRUMENT.search(block).group(1)
            broker = re.search(r'broker="([^"]+)"', block).group(1)
            info = next(m.group(0) for m in INSTRUMENT.finditer(text)
                        if m.group(1) == instrument and m.group(0) != block)
            entry = next(m.group(0) for m in BROKER.finditer(text) if m.group(1) == broker)
            return block, info, entry
    raise SystemExit(f"{source} no define el feed {feed} tampoco. Hay que darlo de alta en "
                     "SQX — un símbolo no se inventa.")


def one_task(text: str, donor_feed: str, blocks: tuple[str, str, str]) -> str:
    """Rewrite one task so it trades the borrowed feed instead of the donor's.

    Args:
        text: A task XML.
        donor_feed: The SQX symbol the clone inherited.
        blocks: (Symbol, InstrumentInfo, Broker) as `definitions` returned them.

    Returns:
        The task. The instrument and the broker are appended only when the donor does not
        already carry them, because SQX keys both by name and a duplicate is a conflict.
    """
    symbol, info, broker = blocks
    text = SYMBOL.sub(lambda m: symbol if m.group(1) == donor_feed else m.group(0), text)
    text = CHART.sub(lambda m: m.group(0).replace(donor_feed, SYMBOL.match(symbol).group(1))
                     if m.group(1) == donor_feed else m.group(0), text)
    instrument = INSTRUMENT.search(info).group(1)
    if f'instrument="{instrument}"' not in text.split("<Instruments>")[1].split("</Instruments>")[0]:
        text = text.replace("<Instruments>", f"<Instruments>\n      {info}", 1)
    if f'id="{BROKER.search(broker).group(1)}"' not in text.split("<Brokers>")[1].split("</Brokers>")[0]:
        text = text.replace("<Brokers>", f"<Brokers>\n      {broker}", 1)
    return text


def borrow_symbol(members: dict[str, bytes], feed: str, build_member: str,
                  source: Path) -> str | None:
    """Point every task of a clone at this asset's feed, patched in place.

    Args:
        members: The .cfx contents by member name.
        feed: The SQX symbol the project must trade, from the asset's file.
        build_member: The member whose first <Chart> names the donor's own feed.
        source: A project.cfx that defines `feed`.

    Returns:
        The feed that was replaced, or None when the donor already traded this asset.

    A donor frozen for one asset carries that asset's feed in every task, and `setups.py`
    only prices a <Setup> whose <Chart> already names the target. Without this the clone
    keeps the donor's market, takes the new asset's session and dates, and builds on the
    wrong instrument with nothing in SQX complaining — measured 2026-09-24 on a USDJPY
    clone of the XAUUSD donor, which loaded gold.
    """
    donor_feed = main_feed(members, build_member)
    if donor_feed == feed:
        return None
    blocks = definitions(source, feed)
    for member in [n for n in members if n.endswith(".xml") and n != "config.xml"]:
        members[member] = one_task(members[member].decode("utf-8"), donor_feed,
                                   blocks).encode("utf-8")
    return donor_feed


def refuse(result: dict, final: dict[str, bytes], donor_feed: str, replaced: str | None) -> None:
    """Stop before anything lands in an install when a gate the human summary would miss failed.

    Args:
        result: What `builder.build` is about to return.
        final: The staged .cfx contents by member name, already through `configure`.
        donor_feed: The SQX symbol the clone inherited from the donor before any swap.
        replaced: What `borrow_symbol` actually replaced, or None when no swap ran.

    Raises:
        SystemExit: On a template that would be silently ignored, a task with zero Setups
            costed on the target feed, or the donor's own feed still readable in the output
            after a swap ran. `configure`'s per-task counts can each read as success while
            the project as a whole still trades the wrong market — OPEN.md issues 34-35, the
            USDJPY clone that built on gold with nothing in SQX complaining.
    """
    if result["template_ignored"]:
        raise SystemExit("the template would be IGNORED: " + "; ".join(result["template_ignored"]))
    unpriced = [m for m, n in result["setups"].items() if not n]
    if unpriced:
        raise SystemExit(f"{', '.join(unpriced)} no lleva ningún <Setup> sobre "
                         f"{result['feed']}: esas tareas operarían el mercado del donante a "
                         "sus costes. Pasa --session-from con un proyecto que defina el feed.")
    if replaced:
        stray = sorted(m for m, blob in final.items()
                       if m.endswith(".xml") and donor_feed.encode("utf-8") in blob)
        if stray:
            raise SystemExit(f"{donor_feed} (el feed del donante) sigue apareciendo en "
                             f"{', '.join(stray)} después del swap: el proyecto seguiría "
                             "operando ese mercado en alguna tarea. No se instala nada.")
