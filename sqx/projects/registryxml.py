"""A task's resources as SQX's data registry defines them today, in the exact text SQX writes."""

import re
import sqlite3
import zipfile
from pathlib import Path

from sqx.projects import sessiondb

SYMBOL = re.compile(r'<Symbol\b[^>]*?name="([^"]+)"[^>]*?>.*?</Symbol>', re.S)
INSTRUMENT = re.compile(r'<InstrumentInfo\b[^>]*?instrument="([^"]+)"[^>]*?/>')
DAY = 86_400_000   # a <Symbol> range is in epoch milliseconds, on midnights


def _java(x: float) -> str:
    """A double as Java's Double.toString writes it: SQX compares instrument XML as text."""
    x = float(x)
    if x == 0 or 1e-3 <= abs(x) < 1e7:
        return repr(x)
    mantissa, exp = f"{x:e}".split("e")
    mantissa = repr(float(mantissa))
    return f"{mantissa}E{int(exp)}"


def _esc(v: object) -> str:
    """An attribute value escaped as SQX writes it (`&quot;`, never single quotes)."""
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _registry(sql: str, args: tuple) -> dict | None:
    """One row of SQX's data registry, read-only, off the data root's copy of the master's."""
    with sqlite3.connect(f"file:{sessiondb.copy()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        r = db.execute(sql, args).fetchone()
    return dict(r) if r else None


def instrument_xml(name: str) -> str:
    """`<InstrumentInfo/>` exactly as SQX's InstrumentInfo.getXML() writes it from its registry.

    SQX checks every `<Instruments>` entry against that text, character for character, before a
    task may start (ProjectResources.checkTaskResources, 🔬 2026-10-01): attribute order, Java's
    number format (1.0E-5), `decimals` = the tick step's decimals, exchange/country/sector only
    when the registry holds them, a null swap written "null".
    """
    i = _registry("SELECT * FROM INSTRUMENTS WHERE INSTRUMENT = ?", (name,))
    step = float(i["TICKSTEP"])
    decimals = max(0, -int(f"{step:e}".split("e")[1])) if step < 1 else 0
    pairs = [("instrument", i["INSTRUMENT"]), ("description", i["DESCRIPTION"] or ""),
             ("tickSize", _java(i["TICKSIZE"])), ("tickStep", _java(step)),
             ("minDistance", _java(i["MIN_DISTANCE"] or 0)), ("tickValueInMoney", "0.0"),
             ("dateFrom", 0), ("dateTo", 0), ("rows", 0), ("totalDays", 0),
             ("defaultSpread", _java(i["DEFAULTSPREAD"] or 0)),
             ("defaultSlippage", _java(i["DEFAULTSLIPPAGE"] or 0)), ("decimals", decimals),
             ("commissions", i["COMMISSIONS"]), ("pointValue", _java(i["POINTVALUE"])),
             ("dataType", i["DATATYPE"]), ("recognizedFromOrders", "false")]
    pairs += [(k, i[k.upper()]) for k in ("exchange", "country", "sector") if i[k.upper()] is not None]
    pairs += [("swap", i["SWAP"] if i["SWAP"] is not None else "null"),
              ("orderSizeMultiplier", _java(i["ORDERSIZEMULTIPLIER"])),
              ("orderSizeStep", _java(i["ORDERSIZESTEP"])), ("broker", i["BROKER_ID"])]
    return "<InstrumentInfo " + " ".join(f'{k}="{_esc(v)}"' for k, v in pairs) + " />"


def broker_xml(broker_id: int) -> str | None:
    """`<Broker/>` of SQX's registry; SQX only compares its timezone."""
    b = _registry("SELECT * FROM BROKER WHERE ID = ?", (broker_id,))
    if not b:
        return None
    return (f'<Broker id="{b["ID"]}" name="{_esc(b["NAME"])}" description="{_esc(b["DESC"] or "")}" '
            f'timezone="{_esc(b["MT_TIMEZONE"])}" postfix="{_esc(b["POSTFIX"] or "")}" '
            f'mtUse="{str(bool(b["MT_USE"])).lower()}" spUse="{str(bool(b["STOCKPICKER_USE"])).lower()}" />')


def definitions(feed: str) -> tuple[str, str, str] | None:
    """One feed's three resource blocks written from the registry, for a feed no project carries.

    Args:
        feed: SQX symbol name, e.g. "DAX40_M1".

    Returns:
        (the <Symbol> block, its <InstrumentInfo>, its <Broker>), or None when the registry
        holds no such feed. The dates are the data's own range; `setups` rewrites them to the
        task's window, as it does for a block borrowed from a project.
    """
    d = _registry("SELECT * FROM DATA WHERE SYMBOL = ?", (feed,))
    if not d:
        return None
    info = instrument_xml(d["INSTRUMENT"])
    head = " ".join(f'{k}="{_esc(v)}"' for k, v in (
        ("name", d["SYMBOL"]), ("source", d["SOURCE"]), ("barType", d["DATATYPE"]),
        ("precision", d["TIMEFRAME"]), ("timezone", d["TIMEZONE"]), ("dateFrom", d["DATEFROM"]),
        ("dateTo", d["DATETO"]), ("uSymbol", d["USYMBOL"]), ("uSymbolName", d["USYMBOLNAME"]),
        ("removeWeekends", str(bool(d["REMOVE_WEEKENDS"])).lower()), ("broker", d["BROKER_ID"])))
    return f"<Symbol {head}>\n        {info}\n      </Symbol>", info, broker_xml(d["BROKER_ID"])


def refresh(text: str) -> str:
    """Bring every feed a task names up to SQX's registry today: its <Symbol>, its instrument, its broker.

    A project written before 2026-10-01 — the frozen donor included — carries each feed as it
    was then: another instrument, another timezone, another data broker. SQX refuses to start
    such a task («Project has unresolved resources»). Each <Symbol> keeps its own dates; the
    rest comes from data.db, and the instrument and broker it names are put in <Instruments>
    and <Brokers> when missing.
    """
    def symbol(m: re.Match) -> str:
        """One <Symbol> block brought up to its registry row; unknown feeds pass unchanged."""
        d = _registry("SELECT * FROM DATA WHERE SYMBOL = ?", (m.group(1),))
        if not d:
            return m.group(0)
        head = re.match(r"<Symbol\b[^>]*>", m.group(0)).group(0)
        for k, v in (("source", d["SOURCE"]), ("timezone", d["TIMEZONE"]), ("uSymbol", d["USYMBOL"]),
                     ("uSymbolName", d["USYMBOLNAME"]), ("broker", d["BROKER_ID"])):
            head = re.sub(rf'\b{k}="[^"]*"', f'{k}="{_esc(v)}"', head)
        wanted.add((d["INSTRUMENT"], d["BROKER_ID"]))
        return f"{head}\n        {instrument_xml(d['INSTRUMENT'])}\n      </Symbol>"

    wanted: set = set()
    text = SYMBOL.sub(symbol, text)
    # <Instruments> holds exactly the instruments its <Symbol>s use, as the registry writes them:
    # an entry left behind by a market dropped from the Setups, or written before a change, can
    # alone keep the task unresolved. Feeds the registry does not know keep their own entry.
    if "<Instruments>" in text:
        block = text.split("<Instruments>")[1].split("</Instruments>")[0]
        used = {n for n, _ in wanted} | {i for f in SYMBOL.finditer(text)
                                          if not _registry("SELECT 1 FROM DATA WHERE SYMBOL = ?", (f.group(1),))
                                          for i in [INSTRUMENT.search(f.group(0)).group(1)]}
        kept = [m.group(0) for m in INSTRUMENT.finditer(block) if m.group(1) in used and m.group(1) not in
                {n for n, _ in wanted}]
        entries = [instrument_xml(n) for n, _ in sorted(wanted)] + kept
        indent = "\n      "
        text = text.replace(f"<Instruments>{block}</Instruments>",
                            "<Instruments>" + "".join(indent + e for e in entries) + "\n    </Instruments>", 1)
    for name, broker_id in wanted:
        entry = broker_xml(broker_id)
        if entry and "<Brokers>" in text and f'id="{broker_id}"' not in \
                text.split("<Brokers>")[1].split("</Brokers>")[0]:
            text = text.replace("<Brokers>", f"<Brokers>\n      {entry}", 1)
    return text


def refresh_all(members: dict[str, bytes]) -> None:
    """`refresh` every task of a .cfx in place — the main feed and the cross-check markets alike."""
    for member in [m for m in members if m.endswith(".xml") and m != "config.xml"]:
        members[member] = refresh(members[member].decode("utf-8")).encode("utf-8")


def unresolved(cfx: Path, active_only: bool = True) -> list[str]:
    """What SQX would call «unresolved resources» in a project, read off the files — nothing started.

    Args:
        cfx: A project.cfx. Read only.
        active_only: Check only the tasks config.xml has switched on — the ones a start runs.

    Returns:
        One line per mismatch, «member: what», empty when every task agrees with the registry.
        The checks are the ones `action=start` was measured to refuse on
        (`knowhow/sqx-drive/cannot-start-unresolved-past-data.md`): a feed the registry lacks,
        a <Symbol> on another timezone or data broker, a data range outside the feed's bars —
        `dateTo` is the midnight AFTER the last day, so a window may end at most the day before
        the feed's last bar — an <Instruments> entry or a <Session> that is not the registry's
        own text, and a session a task names without defining it.
    """
    with zipfile.ZipFile(cfx) as z:
        config = z.read("config.xml").decode("utf-8")
        tasks = {m.group(2): m.group(1) == "true" for m in re.finditer(
            r'<Task\b[^>]*?active="(\w+)"[^>]*?taskXMLFile="([^"]+)"', config)}
        texts = {n: z.read(n).decode("utf-8") for n, on in tasks.items() if on or not active_only}
    out = []
    for member, text in texts.items():
        for m in SYMBOL.finditer(text):
            head = dict(re.findall(r'(\w+)="([^"]*)"', re.match(r"<Symbol\b[^>]*>", m.group(0)).group(0)))
            d = _registry("SELECT * FROM DATA WHERE SYMBOL = ?", (m.group(1),))
            if not d:
                out.append(f"{member}: feed {m.group(1)} is not in the registry")
                continue
            if (head["timezone"], head["broker"]) != (d["TIMEZONE"], str(d["BROKER_ID"])):
                out.append(f"{member}: {m.group(1)} on timezone {head['timezone']} / broker "
                           f"{head['broker']}, the registry has {d['TIMEZONE']} / {d['BROKER_ID']}")
            if int(head["dateTo"]) > d["DATETO"] or int(head["dateFrom"]) < d["DATEFROM"] // DAY * DAY:
                out.append(f"{member}: {m.group(1)} range {head['dateFrom']}..{head['dateTo']} is "
                           f"outside its bars {d['DATEFROM']}..{d['DATETO']} (end the window at "
                           "most the day before the last bar)")
        for m in INSTRUMENT.finditer(text):
            if _registry("SELECT 1 FROM INSTRUMENTS WHERE INSTRUMENT = ?", (m.group(1),)) \
                    and m.group(0) != instrument_xml(m.group(1)):
                out.append(f"{member}: instrument {m.group(1)} is not the registry's text")
        defined = {name: block for block, name in
                   re.findall(r'(<Session name="([^"]+)">.*?</Session>)', text, re.S)}
        for name, block in defined.items():
            mine = sessiondb.block(name, sessiondb.copy())
            if mine and re.sub(r"\s+", "", mine) != re.sub(r"\s+", "", block):
                out.append(f"{member}: session {name} is not the registry's hours")
        for name in set(re.findall(r'MarketOpenSession">([^<]+)<', text)) - set(defined):
            out.append(f"{member}: names session {name} without defining it")
    return sorted(set(out))

