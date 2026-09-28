"""Compile MQL5 sources with MetaEditor under Wine, and install the Sq* indicators SQX's EAs call."""
import re
import shutil
from pathlib import Path

from mt5 import wine

RESULT = re.compile(r"(\d+) errors?, (\d+) warnings?")


def _log(log: Path) -> str:
    """MetaEditor's log text; it writes UTF-16 with a BOM."""
    raw = log.read_bytes()
    return raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "replace")


def compile_path(target: Path) -> dict:
    """Compile one .mq5, or every .mq5 of a folder, where it already sits inside MQL5/.

    Args:
        target: A .mq5 file or a folder under the data folder's MQL5/.

    Returns:
        {"ok", "errors", "warnings", "messages": the error and warning lines, "log": path}.
    """
    log = target.with_suffix(".log") if target.is_file() else target / "compile.log"
    log.unlink(missing_ok=True)
    wine.run(wine.METAEDITOR, [f"/compile:{wine.windows(target)}", f"/log:{wine.windows(log)}"],
             timeout=600)
    text = _log(log)
    totals = RESULT.findall(text)
    errors = sum(int(e) for e, _ in totals)
    warnings = sum(int(w) for _, w in totals)
    messages = [ln.strip() for ln in text.splitlines() if re.search(r"\b(error|warning)\b", ln)
                and not RESULT.search(ln)]
    return {"ok": bool(totals) and errors == 0, "errors": errors, "warnings": warnings,
            "messages": messages[:50], "log": str(log)}


def expert(source: Path) -> dict:
    """Copy an EA source (e.g. saved from SQX as MQL5) into MQL5/Experts/AlgoProject and compile it.

    Args:
        source: The .mq5 on the Linux side.

    Returns:
        compile_path()'s dict plus "expert": the name the tester's ini uses
        (AlgoProject\\<stem>.ex5, relative to MQL5/Experts).
    """
    folder = wine.data_dir() / "MQL5" / "Experts" / wine.EXPERTS_SUB
    folder.mkdir(exist_ok=True)
    target = folder / source.name
    shutil.copy2(source, target)
    out = compile_path(target)
    return {**out, "expert": f"{wine.EXPERTS_SUB}\\{source.stem}.ex5",
            "ex5_exists": target.with_suffix(".ex5").exists()}


def sqx_indicators() -> dict:
    """Copy SQX's MT5 Indicators and Include into the terminal and compile the indicators.

    Returns:
        compile_path()'s dict for the Indicators folder, plus how many sources were copied.
    """
    mql5 = wine.data_dir() / "MQL5"
    copied = 0
    for sub in ("Indicators", "Include"):
        for f in (wine.SQX_MQL5 / sub).rglob("*"):
            if f.is_file() and f.suffix in (".mq5", ".mqh"):
                dest = mql5 / sub / f.relative_to(wine.SQX_MQL5 / sub)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                copied += 1
    return {**compile_path(mql5 / "Indicators"), "copied": copied}
