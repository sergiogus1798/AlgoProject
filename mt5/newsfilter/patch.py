"""Insert a prop firm's news filter into the MQL5 source SQX exports, at the four places it needs."""
import re
from pathlib import Path
from string import Template

MQL = Path(__file__).parent / "mql"
MARKERS = ("NEWS FILTER", "newsBlock")
ENTRY_RULE = re.compile(r"^// Rule: (Long|Short) entry")
ENTRY_GUARD = "      &&   !newsBlock   // NEWS FILTER: no entry inside a release window"
CALL = ["   // ===== NEWS FILTER: START - call =====",
        "   bool newsBlock = handleNewsCompliance();",
        "   // ===== NEWS FILTER: END =====", ""]


def country_lines(country_of: dict) -> str:
    """The MQL lines of newsMovesSymbol() that give an index or a commodity its country's currency."""
    out = []
    for currency, fragments in country_of.items():
        out.append(f'   if(currency == "{currency}"){{')
        out += [f'      if(StringFind(sym, "{f}") >= 0) return true;' for f in fragments]
        out.append("   }")
    return "\n".join(out)


def event_lines(events: dict | None) -> str:
    """The body of newsTag(): every HIGH event under its currency, or only the firm's listed codes."""
    if events is None:
        return "   return importance == CALENDAR_IMPORTANCE_HIGH ? currency : \"\";"
    out = ['   string key = country + ":" + code;']
    for tag, keys in events.items():
        cond = "\n      || ".join(f'key == "{k}"' for k in keys)
        out.append(f'   if({cond}) return "{tag}";')
    return "\n".join(out + ['   return "";'])


def blocks(firm: dict) -> tuple[list[str], list[str]]:
    """The inputs block and the helper-functions block for one firm, as lines."""
    values = {**firm, "mt5_calendar": str(firm["mt5_calendar"]).lower(),
              "forex_factory": str(firm["forex_factory"]).lower(),
              "country_of": country_lines(firm["country_of"]), "events": event_lines(firm["events"]),
              "mt5_what": "HIGH importance" if firm["events"] is None else f"{firm['label']}'s restricted list"}
    render = [Template((MQL / f).read_text()).substitute(values).split("\n")[:-1]
              for f in ("inputs.mqh.tpl", "helpers.mqh.tpl")]
    return render[0], render[1]


def line_of(lines: list[str], text: str) -> int:
    """Index of the one line that is exactly `text` once stripped; refuses zero or several."""
    hits = [i for i, ln in enumerate(lines) if ln.strip() == text]
    assert len(hits) == 1, f"expected one line '{text}' in the SQX source, found {len(hits)}"
    return hits[0]


def entry_closers(lines: list[str]) -> list[int]:
    """Index of the ')' that closes each entry rule's condition — the new guard goes just before it.

    Refuses an entry rule whose condition does not close on a line of its own before the next rule:
    that is not the shape SQX writes, and guessing would put the guard in another rule.
    """
    heads = [i for i, ln in enumerate(lines) if ln.startswith("// Rule: ")]
    closers = []
    for k, i in enumerate(heads):
        if ENTRY_RULE.match(lines[i]):
            end = heads[k + 1] if k + 1 < len(heads) else len(lines)
            hit = next(j for j in range(i, end) if lines[j].strip() == ")")
            closers.append(hit)
    assert closers, "no '// Rule: Long entry' or '// Rule: Short entry' in the SQX source"
    return closers


def patch(text: str, firm: dict) -> str:
    """The SQX EA source with the firm's news filter in it; everything else byte for byte.

    Args:
        text: An .mq5 exactly as SQX wrote it (CRLF kept).
        firm: One entry of firms.FIRMS.

    Returns:
        The patched source, same line endings. Refuses a source that already carries a filter.
    """
    assert not any(m in text for m in MARKERS), "this EA already carries a news filter"
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    inputs, helpers = blocks(firm)
    "\n".join(inputs + helpers).encode("ascii")   # MetaEditor reads the rest as SQX wrote it
    money = line_of(lines, "// Money Management variables")
    functions = line_of(lines, "// -- Functions")
    options = line_of(lines, "openingOrdersAllowed = sqHandleTradingOptions();")
    assert lines[functions + 2].strip() == "" and lines[options + 1].strip() == "", \
        "the SQX source is not laid out as the export this was written against"
    inserts = [(money - 1, inputs), (functions + 3, helpers), (options + 2, CALL)]
    inserts += [(j, [ENTRY_GUARD]) for j in entry_closers(lines)]
    for at, block in sorted(inserts, key=lambda x: -x[0]):
        lines[at:at] = block
    return eol.join(lines)
