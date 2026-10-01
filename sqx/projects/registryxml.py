"""A task's resources as SQX's data registry defines them today, in the exact text SQX writes."""

import re
import sqlite3

from core.paths import MASTER

REGISTRY = MASTER / "user" / "data" / "data.db"
SYMBOL = re.compile(r'<Symbol\b[^>]*?name="([^"]+)"[^>]*?>.*?</Symbol>', re.S)
INSTRUMENT = re.compile(r'<InstrumentInfo\b[^>]*?instrument="([^"]+)"[^>]*?/>')


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
    """One row of SQX's data registry, read-only."""
    with sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True) as db:
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
