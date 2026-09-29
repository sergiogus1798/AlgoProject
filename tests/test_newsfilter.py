"""mt5.newsfilter inserts where the hand-made FTMO patch did, only inserts, and refuses what it cannot place."""
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import MT5_DATA
from mt5.newsfilter.firms import FIRMS
from mt5.newsfilter.patch import patch
from mt5.newsfilter.run import safe

REF = MT5_DATA / "newsfilter-reference"


def ops(a: list[str], b: list[str]) -> list[tuple]:
    """difflib opcodes from a to b, without the equal runs."""
    return [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]


def anchor(lines: list[str], i: int) -> int:
    """The first non-blank line at or after i: an insert next to blank lines has no single position."""
    while not lines[i].strip():
        i += 1
    return i


def check_against_hand_patch() -> None:
    """Same insertion points as the 2026-05-17 FTMO patch, on every pair; nothing replaced or deleted."""
    pairs = 0
    for before in sorted((REF / "before").glob("*.mq5")):
        after = REF / "after" / f"{safe(before.stem)}_FTMO.mq5"
        if not after.exists():
            continue
        text = before.read_bytes().decode("utf-8")
        ours = patch(text, FIRMS["ftmo"])
        orig = text.split("\r\n")
        hand_ops = ops(orig, after.read_bytes().decode("utf-8").split("\r\n"))
        hand = {anchor(orig, o[1]) for o in hand_ops if o[0] == "insert"}
        mine = ops(orig, ours.split("\r\n"))
        assert {o[0] for o in mine} == {"insert"}, f"{before.name}: something other than an insert"
        assert {anchor(orig, o[1]) for o in mine} == hand, f"{before.name}: {mine} vs hand {sorted(hand)}"
        entries = len(re.findall(r"^// Rule: (Long|Short) entry", text, re.M))
        assert ours.count("&&   !newsBlock") == entries
        assert "\r\n" in ours and "\n" not in ours.replace("\r\n", "")
        pairs += 1
    assert pairs == 6, pairs


def check_firms_differ() -> None:
    """Hantec: 3-minute rule, Forex Factory, every HIGH event, JP225 on the yen. FTMO: its own event list
    (the ones MT5 rates medium included), crude inventories only on oil, US30 on USD, JP225 free."""
    text = (REF / "before" / "Strategy 13.43.66.mq5").read_bytes().decode("utf-8")
    hantec, ftmo = patch(text, FIRMS["hantec"]), patch(text, FIRMS["ftmo"])
    assert "NewsRuleMinutes        = 3;" in hantec and "NewsUseForexFactory    = true;" in hantec
    assert 'StringFind(sym, "JP225")' in hantec and 'StringFind(sym, "JP225")' not in ftmo
    assert "NewsUseForexFactory    = false;" in ftmo
    assert "importance == CALENDAR_IMPORTANCE_HIGH" in hantec and "CALENDAR_IMPORTANCE_HIGH" not in ftmo
    for key in ("US:fomc-minutes", "AU:cpi-yy", "CA:employment-change", "NZ:gdp-qq"):
        assert f'key == "{key}"' in ftmo, key
    assert 'return "OIL";' in ftmo and 'StringFind(sym, "US30")' in ftmo


def check_refusals() -> None:
    """A second patch and an entry rule not written in SQX's shape both refuse."""
    text = (REF / "before" / "Strategy 13.43.66.mq5").read_bytes().decode("utf-8")
    for bad in (patch(text, FIRMS["hantec"]),
                text.replace("      &&   LongEntrySignal\r\n)", "      &&   LongEntrySignal)", 1)):
        try:
            patch(bad, FIRMS["hantec"])
        except (AssertionError, StopIteration):
            continue
        raise AssertionError("a source it cannot place was patched")


if __name__ == "__main__":
    check_against_hand_patch()
    check_firms_differ()
    check_refusals()
    print("ok")
