#!/usr/bin/env python3
"""Golden-file test for the stop-loss graft: a stop written wrong trades unprotected in silence."""

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants.build import rewrite, stoploss

HERE = Path(__file__).parent / "fixtures"
NOSTOP = HERE / "nostop_portfolio.xml"          # XAUUSD Strategy 19.8.78, built without a stop
WITHSTOP = HERE / "strategy.sqx"                # built by SQX with SL = X * ATR(20)
GOLDEN = HERE / "stoploss.golden.json"
X = 2.5
PT_PARAM = re.compile(r'key="#ProfitTarget\.ProfitTarget#".*?</Param>', re.S)


def formula(portfolio: str) -> str:
    """The stop's <Formula> of the first entry, whitespace folded, for comparing two writers."""
    at = portfolio.index('key="#StopLoss.StopLoss#"')
    inner = re.compile(r"<Formula[^>]*/>|<Formula.*?</Formula>", re.S).search(portfolio, at).group(0)
    return re.sub(r">\s+<", "><", inner)


def parse() -> dict:
    """What the graft produces from the fixture."""
    text = stoploss.graft(NOSTOP.read_text(encoding="utf-8"), X)
    return {"sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
            "declared": rewrite.declared(text)[stoploss.VARIABLE],
            "value": rewrite.values(text)[stoploss.VARIABLE],
            "formula": formula(text)}


def invariants() -> list[str]:
    """What must hold whatever the golden file says."""
    bad = []
    before = NOSTOP.read_text(encoding="utf-8")
    after = stoploss.graft(before, X)
    with zipfile.ZipFile(WITHSTOP) as z:
        built = z.read(rewrite.PORTFOLIO).decode("utf-8")
    if formula(after) != formula(built):
        bad.append("el stop injertado no es el bloque que SQX escribe para SL = X*ATR(20)")
    if PT_PARAM.findall(after) != PT_PARAM.findall(before):
        bad.append("el injerto ha tocado el ProfitTarget")
    if after.count("SQ.Formulas.SLPT.None") != before.count("SQ.Formulas.SLPT.None") - 1:
        bad.append("no se ha cambiado exactamente un SLPT.None (hay una entrada)")
    # Everything the graft does not own is byte-identical: take its two insertions out and
    # the original comes back.
    undone = re.sub(r'<variable makeExternal="true">\s*<id>StopLossCoef1</id>.*?</variable>\s*',
                    "", after, count=1, flags=re.S)
    undone = re.sub(r'<Formula key="SQ\.Formulas\.SLPT\.ATRBasedValue">.*?</Formula>',
                    '<Formula key="SQ.Formulas.SLPT.None" />', undone, count=1, flags=re.S)
    if undone != before:
        bad.append("el injerto cambia algo más que el stop y su variable")
    moved = rewrite.set_values(after, {stoploss.VARIABLE: 3.1})
    if rewrite.values(moved)[stoploss.VARIABLE] != "3.1":
        bad.append("la fábrica de variantes no puede mover la X injertada")
    try:
        stoploss.graft(after, X)
        bad.append("injertar dos veces no se niega")
    except ValueError:
        pass
    return bad


def main() -> None:
    """Compare against the golden file, or rewrite it with --bless."""
    bad = invariants()
    if bad:
        raise SystemExit("\n".join(bad))
    got = parse()
    if "--bless" in sys.argv:
        GOLDEN.write_text(json.dumps(got, indent=2) + "\n", encoding="utf-8")
        print(f"blessed {GOLDEN.name}")
        return
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if got != want:
        raise SystemExit(f"test_stoploss: {got} != {want}")
    print("test_stoploss: ok")


if __name__ == "__main__":
    main()
