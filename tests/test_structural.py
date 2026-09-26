#!/usr/bin/env python3
"""Golden-file test for the structural factory: an ablation or an inversion written wrong runs in silence."""

import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.structural import logic, make, plan
from sqx.variants.build import rewrite

HERE = Path(__file__).parent / "fixtures"
FLAT = HERE / "structural_portfolio.xml"          # USDJPY Strategy 23.1.53: MA above AND QQE cross
NESTED = HERE / "structural_nested_portfolio.xml"  # USDJPY Strategy 6.1.69: MA above AND ATR > ATR
ARMED = HERE / "strategy.sqx"                      # short-only, with an ATR stop and a target;
                                                   # also the donor of the non-XML members
GOLDEN = HERE / "structural.golden.json"


def read(path: Path) -> str:
    """A fixture as SQX wrote it: CRLF kept, which `read_text` would silently fold."""
    return path.read_bytes().decode("utf-8")


def digest(text: str) -> str:
    """First 16 hex of the text's SHA-256."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def parse() -> dict:
    """What the factory writes from the fixture SQX ran on 2026-09-26, minus the stamp."""
    flat = read(FLAT)
    return {"conditions": [c["block"] for c in logic.conditions(flat)],
            "nested": [c["block"] for c in logic.conditions(read(NESTED))],
            "ablate_0": digest(logic.ablate(flat, "LongEntrySignal", 0)),
            "ablate_1": digest(logic.ablate(flat, "LongEntrySignal", 1)),
            "invert": digest(logic.invert(flat))}


def invariants() -> list[str]:
    """What must hold whatever the golden file says."""
    bad = []
    for fixture in (FLAT, NESTED):
        text = read(fixture)
        found = logic.conditions(text)
        for c in found:
            cut = logic.ablate(text, c["signal"], c["index"])
            # A deletion and nothing else: one contiguous span gone, every variable kept.
            left = [d["block"] for d in logic.conditions(cut)]
            if left != [d["block"] for d in found if d is not c]:
                bad.append(f"{fixture.name}: ablar {c['block']} deja {left}")
            head = next(i for i, (x, y) in enumerate(zip(text, cut)) if x != y)
            if text[head + len(text) - len(cut):] != cut[head:]:
                bad.append(f"{fixture.name}: ablar {c['block']} toca algo más que un bloque")
            if rewrite.declared(cut) != rewrite.declared(text):
                bad.append(f"{fixture.name}: ablar {c['block']} cambia las variables")
            try:
                logic.ablate(cut, c["signal"], 0)
                bad.append(f"{fixture.name}: ablar la última condición no se niega")
            except ValueError:
                pass
        flipped = logic.invert(text)
        if logic.direction(flipped) != [-d for d in logic.direction(text)]:
            bad.append(f"{fixture.name}: la inversión no cambia el signo de cada entrada")
        if logic.conditions(flipped) != found:
            bad.append(f"{fixture.name}: la inversión toca las condiciones")
        if logic.invert(flipped) != text:
            bad.append(f"{fixture.name}: invertir dos veces no devuelve la madre")
        if "MarketPositionIsShort" not in flipped or 'Rule name="Short exit"' not in flipped:
            bad.append(f"{fixture.name}: la salida no pasa a cerrar cortos")
    with zipfile.ZipFile(ARMED) as z:
        armed = z.read(rewrite.PORTFOLIO).decode("utf-8")
    try:
        logic.invert(armed)
        bad.append("invertir una estrategia con stop no se niega")
    except ValueError:
        pass
    bad += factory()
    return bad


def factory() -> list[str]:
    """The whole write and read-back on a copy of the fixture, in a temporary folder."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = rewrite.members(ARMED) | {rewrite.PORTFOLIO: FLAT.read_bytes()}
        mother = tmp / "Strategy 23.1.53.sqx"
        rewrite.save(mother, parts, "minimal")
        rows = plan.build([mother])
        make.write(rows, tmp / "sqx", "minimal")
        checked = make.verify(rows, make.read_back(tmp / "sqx"))
        kinds = sorted(rows["kind"])
        out = []
        if kinds != ["ablation", "ablation", "identity", "inversion"]:
            out.append(f"el plan no es identidad + 2 ablaciones + inversión: {kinds}")
        if not (checked["ok"] & (checked["stamp"] == checked["variant_id"])).all():
            out.append(f"la relectura no es el plan:\n{checked.to_string()}")
        with zipfile.ZipFile(tmp / "sqx" / "S00O00.sqx") as z:
            if z.read(rewrite.PORTFOLIO).decode("utf-8").split("-->", 1)[1] != \
                    read(FLAT).split("?>", 1)[1]:
                out.append("la identidad no es la madre byte a byte (salvo el sello)")
            if b"<Fingerprint" in z.read(rewrite.SETTINGS):
                out.append("la identidad hereda el Fingerprint")
    return out


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
        raise SystemExit(f"test_structural: {got} != {want}")
    print("test_structural: ok")


if __name__ == "__main__":
    main()
