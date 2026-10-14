"""One account's deployment package: its .ex5, a .set per EA with its magic, and a chart profile."""

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import openpyxl

from core import fleetpaths
from mt5 import metaeditor, wine
from mt5.fleet import magics
from mt5.verify import firms

PERIOD = {
    "M1": (0, 1),
    "M5": (0, 5),
    "M15": (0, 15),
    "M30": (0, 30),
    "H1": (1, 1),
    "H4": (1, 4),
    "D1": (1, 24),
}
CHART = """<chart>
id={id}
symbol={symbol}
period_type={ptype}
period_size={psize}
digits=2
scale=4
mode=1
grid=0
shift=1
shift_size=20.000000
<expert>
name={name}
path=Experts\\{sub}\\{name}.ex5
expertmode=5
<inputs>
{inputs}
</inputs>
</expert>
<window>
height=100
<indicator>
name=Main
path=
apply=1
show_data=1
</indicator>
</window>
</chart>
"""


def account(workbook: Path, sheet: str) -> tuple[str, int]:
    """The firm and size (thousands of USD) of one account's sheet, from the `Cuentas` sheet."""
    wb = openpyxl.load_workbook(workbook, read_only=True)
    for name, firm, size, *_ in wb["Cuentas"].iter_rows(min_row=2, values_only=True):
        if name == sheet:
            return str(firm), int(size) // 1000  # pyright: ignore[reportArgumentType]  # openpyxl cell value
    raise SystemExit(f"la hoja «{sheet}» no está en Cuentas del Excel")


def stem(strategy: str, firm: str, size: int) -> str:
    """The file name that ties an EA to a firm and size (owner, 2026-10-14): `Strategy_3_29_126_FTMO100k`
    for the Excel's `3.29.126`."""
    return f"Strategy_{strategy.replace('.', '_')}_{firm}{size}k"


def source_for(strategy: str, firm: str, size: int, eas: Path) -> Path | None:
    """The `.mq5` of a strategy for a firm and size in `eas`, case-blind; None when absent."""
    want = stem(strategy, firm, size).lower()
    return next((p for p in eas.glob("*.mq5") if p.stem.lower() == want), None)


def chart(symbol: str, timeframe: str, name: str, magic: int, number: int) -> str:
    """One chart of the profile: the symbol, the period and the EA with its magic attached."""
    ptype, psize = PERIOD[timeframe]
    return CHART.format(
        id=130000000000000000 + number,
        symbol=symbol,
        ptype=ptype,
        psize=psize,
        name=name,
        sub=wine.EXPERTS_SUB,
        inputs=f"MagicNumber={magic}",
    ).replace("\n", "\r\n")


def plan(
    book: Path, sheet: str, firm: str, size: int, eas: Path
) -> tuple[list, list[str]]:
    """The sheet's EAs as (source, asset, firm's symbol, timeframe, strategy) and every problem found."""
    ws = openpyxl.load_workbook(book, read_only=True)[sheet]
    problems, todo = [], []
    for symbol, timeframe, strategy, *_ in ws.iter_rows(min_row=2, values_only=True):
        if not (symbol and timeframe and strategy):
            continue
        src = source_for(str(strategy), firm, size, eas)
        mt5_symbol = firms.names(str(symbol)).get(firm.lower())
        if src is None:
            problems.append(
                f"{strategy}: falta {stem(str(strategy), firm, size)}.mq5 en {eas}"
            )
        if not mt5_symbol:
            problems.append(
                f"{symbol}: sin símbolo de {firm} en assets/symbols/{symbol}.yaml (mt5.{firm.lower()}); no se adivina"
            )
        if timeframe not in PERIOD:
            problems.append(f"{strategy}: temporalidad {timeframe} desconocida")
        todo.append((src, str(symbol), mt5_symbol, str(timeframe), str(strategy)))
    return todo, problems


def compile_all(sources: list[Path]) -> list[str]:
    """Compile each source into the terminal's data folder; the ones that fail, as sentences."""
    bad = []
    for src in sources:
        got = metaeditor.expert(src)  # raises while the terminal is open
        if not got["ok"]:
            bad.append(f"{src.name}: no compila ({got['messages'][:2]})")
    return bad


def build(
    sheet: str, eas: Path, out: Path, workbook: Path | None = None
) -> dict[str, Any]:
    """Compile and lay out the package of one account; nothing is sent anywhere.

    Args:
        sheet: The account's sheet in the workbook (also the profile's name).
        eas: Folder of `.mq5` named `<Strategy_x_y_z>_<Firm><size>k.mq5`.
        out: Folder the package is written into (`<out>/<sheet>/`).
        workbook: The fleet Excel; the owner's by default.

    Returns:
        `{"dir", "eas": [{strategy, symbol, mt5_symbol, timeframe, magic, name}]}`. Stops with
        every problem listed — a missing source, an asset the firm does not name, a failed
        compile — before it writes a single file.
    """
    book = workbook or fleetpaths.workbook()
    firm, size = account(book, sheet)
    todo, problems = plan(book, sheet, firm, size, eas)
    if not problems:
        problems = compile_all([t[0] for t in todo])
    if problems:
        raise SystemExit("paquete detenido:\n- " + "\n- ".join(problems))
    root = out / sheet
    for sub in ("Experts", "Presets", f"Profiles/Charts/{sheet}"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    rows = []
    for i, (src, symbol, mt5_symbol, timeframe, strategy) in enumerate(todo, 1):  # pyright: ignore[reportAssignmentType]
        magic = magics.assign(strategy, symbol, timeframe)
        shutil.copy2(
            wine.data_dir() / "MQL5/Experts" / wine.EXPERTS_SUB / f"{src.stem}.ex5",
            root / "Experts",
        )  # pyright: ignore[reportOptionalMemberAccess]
        (root / "Presets" / f"{src.stem}_{symbol}_{timeframe}.set").write_text(
            f"MagicNumber={magic}\r\n", encoding="utf-16"
        )  # pyright: ignore[reportOptionalMemberAccess]
        (root / f"Profiles/Charts/{sheet}/chart{i:02d}.chr").write_text(
            chart(mt5_symbol, timeframe, src.stem, magic, i),
            encoding="utf-16",  # pyright: ignore[reportArgumentType, reportOptionalMemberAccess]
        )
        rows.append(
            {
                "strategy": strategy,
                "symbol": symbol,
                "mt5_symbol": mt5_symbol,
                "timeframe": timeframe,
                "magic": magic,
                "name": src.stem,
            }
        )  # pyright: ignore[reportOptionalMemberAccess]
    (root / "manifest.json").write_text(
        json.dumps(
            {"sheet": sheet, "firm": firm, "size_k": size, "eas": rows}, indent=1
        ),
        encoding="utf-8",
    )
    return {"dir": root, "eas": rows}


def main() -> None:
    """Build one account's package from the fleet Excel and a folder of EA sources."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sheet", help="la hoja de la cuenta en Flota_de_cuentas.xlsx")
    ap.add_argument(
        "--eas",
        type=Path,
        required=True,
        help="carpeta de los .mq5 (Strategy_x_y_z_<Empresa><tamaño>k.mq5)",
    )
    ap.add_argument("--out", type=Path, default=fleetpaths.FLEET / "packages")
    ap.add_argument("--workbook", type=Path)
    a = ap.parse_args()
    got = build(a.sheet, a.eas, a.out, a.workbook)
    print(f"{len(got['eas'])} EAs en {got['dir']}")
    print(re.sub(r"[{}\[\]]", "", json.dumps(got["eas"], ensure_ascii=False))[:600])


if __name__ == "__main__":
    main()
