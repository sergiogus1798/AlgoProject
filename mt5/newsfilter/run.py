"""Turn SQX-exported EAs into two per strategy — one with a firm's news filter, one without — and compile them."""
import argparse
import re
import shutil
from pathlib import Path

from core.paths import MT5_DATA
from mt5.newsfilter.firms import FIRMS
from mt5.newsfilter.patch import patch

OUT = MT5_DATA / "eas"


def sources(paths: list[Path]) -> list[Path]:
    """Every .mq5 named, a folder standing for the .mq5 directly inside it."""
    return [f for p in paths for f in (sorted(p.glob("*.mq5")) if p.is_dir() else [p])]


def safe(stem: str) -> str:
    """'Strategy 13.43.66' -> 'Strategy_13_43_66': MT5 and the tester's ini take it without quoting."""
    return re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_")


def build(firm_key: str, paths: list[Path]) -> list[dict]:
    """Write <name>_<Firm>.mq5 (filtered) and <name>_NoNews.mq5 (SQX's own) per source.

    Returns:
        One row per strategy: name, the two files written, and its entry-rule count.
    """
    firm = FIRMS[firm_key]
    folder = OUT / firm["label"]
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for src in sources(paths):
        text = src.read_bytes().decode("utf-8")
        name = safe(src.stem)
        filtered = folder / f"{name}_{firm['label']}.mq5"
        plain = folder / f"{name}_NoNews.mq5"
        filtered.write_bytes(patch(text, firm).encode("utf-8"))
        shutil.copyfile(src, plain)
        rows.append({"name": name, "filtered": filtered, "plain": plain,
                     "entries": text.count("// Rule: Long entry") + text.count("// Rule: Short entry")})
    return rows


def compile_all(firm_key: str, rows: list[dict]) -> dict:
    """Copy both EAs of every row into MQL5/Experts/AlgoProject/<Firm>/ and compile that folder.

    Needs the MT5 terminal closed (metaeditor.compile_path refuses otherwise).
    """
    from mt5 import metaeditor, wine
    dest = wine.data_dir() / "MQL5" / "Experts" / wine.EXPERTS_SUB / FIRMS[firm_key]["label"]
    dest.mkdir(parents=True, exist_ok=True)
    for r in rows:
        for f in (r["filtered"], r["plain"]):
            shutil.copy2(f, dest / f.name)
            (dest / f.name).with_suffix(".ex5").unlink(missing_ok=True)
    return {**metaeditor.compile_path(dest), "folder": str(dest)}


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.run <firm> <mq5 or folder>... [--compile]."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("firm", choices=sorted(FIRMS))
    ap.add_argument("paths", nargs="+", type=Path, help="SQX-exported .mq5 files, or folders of them")
    ap.add_argument("--compile", action="store_true", help="also compile both EAs in MT5 (terminal closed)")
    a = ap.parse_args()
    rows = build(a.firm, a.paths)
    print(f"{len(rows)} estrategias -> {OUT / FIRMS[a.firm]['label']}")
    for r in rows:
        print(f"  {r['name']:<28} {r['entries']} regla(s) de entrada  ->  {r['filtered'].name}  +  {r['plain'].name}")
    if a.compile:
        c = compile_all(a.firm, rows)
        print(f"compilado en {c['folder']}: {c['errors']} errores, {c['warnings']} avisos")
        for m in c["messages"]:
            print("  " + m)


if __name__ == "__main__":
    main()
