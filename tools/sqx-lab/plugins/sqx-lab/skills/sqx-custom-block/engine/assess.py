"""assess.py — edge-HYGIENE linter for generated custom blocks.

`validate.py` answers "is this block correct?" (imports, atoms exist, #Line#, no talib).
`assess.py` answers a different question: "is this block likely to HELP, or quietly hurt,
profitability?" It scores each block on the silent edge-destroyers that a syntactic validator
can't see, and that wreck out-of-sample / live results:

  1. LOOK-AHEAD     — a value atom read on the developing bar (#Shift#=0): unstable, future-peek.
  2. REPAINT        — fractals / ZigZag / HalfTrend / Gann HiLo / SuperTrend-type indicators
                      revise their own recent values as new bars arrive. A backtest on a
                      repainting series is a LIE that dies live. Worse at shift=0.
  3. MIDLINE / POLARITY — an oscillator compared to a constant that is outside its range (the
                      block can never fire) or far from its real midline (likely a polarity bug).
  4. OVERFIT SHAPE  — too many tunable knobs, AND/OR compounding (the single-signal discipline),
                      suspiciously specific thresholds.

It is ADVISORY by default (exit 0) — use `--strict` to fail (exit 1) on any CRITICAL finding so
it can act as a gate. Repaint detection is heuristic: a curated set of known-repainting indicator
families, plus an optional scan of the indicator's Java source when the catalog points at one.

Usage:
  python engine/assess.py blocks.xml --catalog catalog.json
  python engine/assess.py blocks.xml --catalog catalog.json --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

COMPARISON_OPS = {"IsGreater", "IsLower", "CrossesAbove", "CrossesBelow",
                  "IsGreaterCount", "IsLowerCount", "IsGreaterPercentil", "IsLowerPercentil"}
LOGICAL_OPS = {"AND", "OR"}

# Indicators whose HISTORY is provisional — they revise already-printed values as future bars
# arrive (late-confirmed pivots). Even at shift>=1 the most recent prints are not final. Always
# a real look-ahead hazard in a backtest.
REPAINT_HISTORICAL = ("fractal", "zigzag", "zig zag")
# Indicators whose DEVELOPING bar is provisional but whose CLOSED bars are final — safe when read
# at shift>=1, a look-ahead lie at shift=0 (the line can still flip on the current bar).
REPAINT_DEVELOPING = ("halftrend", "half trend", "gannhilo", "gann hi", "gann high low",
                      "supertrend", "super trend", "heikenashi", "heiken ashi", "ssl", "renko")
# Java-source tells of repaint / future reference.
JAVA_REPAINT_PAT = re.compile(
    r"\brepaint\b|\bredraw\b|look[\s-]?ahead|not\s+confirmed|provisional|"
    r"\[\s*\w+\s*\+\s*\d|\.get\([^)]*\+\s*[1-9]",
    re.IGNORECASE)
# A current-period OPEN (Open / OpenD / OpenW / OpenM / OpenY) is fixed the instant its
# period begins and never revises, so reading it at shift=0 is NOT look-ahead — it is the one
# OHLC case emit.py allows (allow_shift0=True) and the skill's documented shift rule blesses.
# Current High/Low/Close are still forming, so they stay flagged.
PERIOD_OPEN_RE = re.compile(r"^Open([DWMY])?$")


def _f(s: str | None):
    if s is None:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


class Finding:
    __slots__ = ("sev", "code", "msg")

    def __init__(self, sev: str, code: str, msg: str):
        self.sev, self.code, self.msg = sev, code, msg


# severity -> score penalty
PENALTY = {"CRITICAL": 35, "WARN": 10, "INFO": 3}


def _repaint_class(key: str, display: str) -> str | None:
    blob = f"{key} {display}".lower()
    if any(t in blob for t in REPAINT_HISTORICAL):
        return "historical"
    if any(t in blob for t in REPAINT_DEVELOPING):
        return "developing"
    return None


def _java_repaint(key: str, snippets_dir: str | None) -> str | None:
    if not snippets_dir:
        return None
    try:
        for j in Path(snippets_dir).rglob(f"{key}.java"):
            t = j.read_text(encoding="utf-8", errors="replace")
            m = JAVA_REPAINT_PAT.search(t)
            if m:
                return m.group(0).strip()
    except OSError:
        return None
    return None


def _atom_items(block: ET.Element) -> list[ET.Element]:
    return [it for it in block.iter("Item") if it.get("categoryType") == "indicator"]


def _shift_of(item: ET.Element) -> str | None:
    for p in item.findall("Param"):
        if p.get("key") == "#Shift#":
            return (p.text or "").strip()
    return None


def _outer_knobs(block: ET.Element) -> list[ET.Element]:
    """Tunable optimizer Params on the CBlock itself (after </Contents>) — not the chart slot."""
    out = []
    for p in block.findall("Param"):
        if p.get("paramType") in ("int", "double") and p.get("controlType") == "jspinnerVar":
            out.append(p)
    return out


def _resolve_value(text: str, block: ET.Element):
    """A Number operand's value may be a literal or a reference to an outer knob (#Double3#);
    in the latter case read the knob's defaultValue."""
    text = (text or "").strip()
    if re.fullmatch(r"#[A-Za-z]\w*#", text):
        for p in block.findall("Param"):
            if p.get("key") == text:
                return _f(p.get("defaultValue"))
        return None
    return _f(text)


def _number_operand(op_item: ET.Element):
    """Return (indicator_item, number_value_text) if this comparison is indicator-vs-Number."""
    operands = []
    for blk in op_item.findall("Block"):
        it = blk.find("Item")
        if it is not None:
            operands.append(it)
    ind = num = None
    for it in operands:
        if it.get("key") == "Number":
            np = it.find("Param")
            num = (np.text if np is not None else "") or ""
        elif it.get("categoryType") == "indicator":
            ind = it
    return ind, num


def assess_block(block: ET.Element, atoms: dict, snippets_dir: str | None) -> list[Finding]:
    findings: list[Finding] = []
    name = block.get("name", block.get("key", "?"))

    # --- 1. look-ahead + 2. repaint (per atom) ------------------------------------------
    for it in _atom_items(block):
        key = it.get("key", "")
        disp = it.get("display", "") or (atoms.get(key, {}) or {}).get("display", "")
        shift = _shift_of(it)
        shift0 = shift == "0"
        if shift0:
            findings.append(Finding("CRITICAL", "lookahead",
                f"{key}: read on the developing bar (#Shift#=0) — look-ahead/unstable; use shift>=1."))
        rc = _repaint_class(key, disp)
        jev = _java_repaint(key, snippets_dir)
        if rc == "historical":
            findings.append(Finding("CRITICAL", "repaint",
                f"{key}: repaints HISTORY (late-confirmed pivots) — backtest values are provisional even at shift>=1."))
        elif rc == "developing":
            if shift0:
                findings.append(Finding("CRITICAL", "repaint",
                    f"{key}: repaints the developing bar AND read at shift=0 — look-ahead. Read it at shift>=1."))
            else:
                findings.append(Finding("WARN", "repaint",
                    f"{key}: developing bar can flip (repaint family) — OK at shift>=1, never use shift=0."))
        if jev and rc is None:
            findings.append(Finding("WARN", "repaint",
                f"{key}: Java source hints at repaint/forward-reference (matched '{jev}') — verify it doesn't future-peek."))

    # --- 1b. OHLC / price atoms on the developing bar (look-ahead) ----------------------
    # SQX's default and MT-style engines must read OHLC on the last CLOSED bar; only
    # TradeStation's intrabar engine makes shift=0 OHLC safe. A price / priceValue /
    # priceRange atom (Close/Open/High/Low, HighD, BarRange, ...) at #Shift#=0 is the
    # developing bar = look-ahead. (Time atoms — BarHour/BarTime, categoryType "other" —
    # are deterministic clock values and are NOT flagged.)
    for it in block.iter("Item"):
        if it.get("categoryType") not in ("priceValue", "priceRange"):
            continue
        if _shift_of(it) == "0":
            if PERIOD_OPEN_RE.match(it.get("key", "")):
                continue  # current-period open is fixed at period start — not look-ahead
            findings.append(Finding("CRITICAL", "lookahead",
                f"{it.get('key')}: OHLC read on the developing bar (#Shift#=0) — only valid on "
                f"TradeStation; SQX default must be shift>=1 (last closed bar)."))

    # --- 3. midline / polarity (oscillator vs constant) ---------------------------------
    for op in block.iter("Item"):
        if op.get("key") not in COMPARISON_OPS:
            continue
        ind, numtext = _number_operand(op)
        if ind is None or not numtext:
            continue
        e = atoms.get(ind.get("key", ""), {})
        if not e:
            continue
        val = _resolve_value(numtext, block)
        lo, hi, mid = _f(e.get("indicatorMin")), _f(e.get("indicatorMax")), _f(e.get("middleValue"))
        is_osc = e.get("isOscillator") == "true" or e.get("middleValue") not in (None, "")
        if val is None or not is_osc:
            continue
        if lo is not None and hi is not None and not (lo <= val <= hi):
            findings.append(Finding("CRITICAL", "threshold",
                f"{ind.get('key')}: compared to {val:g}, outside its range [{lo:g},{hi:g}] — block can never fire."))
        elif mid is not None and lo is not None and hi is not None:
            span = hi - lo
            if span > 0 and abs(val - mid) < 0.02 * span and op.get("key") in ("IsGreater", "IsLower"):
                findings.append(Finding("INFO", "midline",
                    f"{ind.get('key')}: leveled at its midline {mid:g} — a midline state filter (intended?)."))

    # --- 4. overfit shape ---------------------------------------------------------------
    knobs = _outer_knobs(block)
    if len(knobs) > 3:
        findings.append(Finding("WARN", "overfit",
            f"{len(knobs)} tunable knobs — each one the optimizer turns is overfit surface; prefer <=2."))
    contents = block.find("Contents")
    if contents is not None:
        for lg in contents.iter("Item"):
            if lg.get("key") in LOGICAL_OPS:
                nclauses = len(lg.findall("Block"))
                if nclauses >= 2:
                    findings.append(Finding("WARN", "compound",
                        f"{lg.get('key')} of {nclauses} clauses — compounding adds overfit surface; "
                        f"keep one signal unless the mechanism is genuinely a conjunction."))
    # suspiciously specific frozen thresholds
    for op in block.iter("Item"):
        if op.get("key") not in COMPARISON_OPS:
            continue
        _, numtext = _number_operand(op)
        numtext = (numtext or "").strip()
        if re.fullmatch(r"-?\d+\.\d{3,}", numtext):
            findings.append(Finding("INFO", "precision",
                f"threshold {numtext} has many decimals — looks curve-fit; round it."))

    for f in findings:
        f.msg = f"[{name}] {f.msg}"
    return findings


def grade(score: int) -> str:
    return "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"


def main(argv) -> int:
    try:                                    # never crash on a non-UTF-8 console codepage
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Edge-hygiene linter for generated custom blocks.")
    ap.add_argument("xml", help="the generated block XML")
    ap.add_argument("--catalog", help="catalog.json (enables midline + Java-repaint checks)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any block has a CRITICAL finding")
    args = ap.parse_args(argv)

    atoms, snippets_dir = {}, None
    if args.catalog:
        data = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
        atoms = data.get("atoms", {})
        snippets_dir = (data.get("meta") or {}).get("snippets_dir")

    root = ET.parse(args.xml).getroot()
    blocks = [it for it in root.iter("Item") if it.get("categoryType") == "Custom blocks"]
    if not blocks:
        print("no custom blocks found in", args.xml)
        return 0

    total_crit = total_warn = 0
    grades = []
    print(f"edge-hygiene assessment — {len(blocks)} block(s)\n" + "=" * 68)
    for b in blocks:
        findings = assess_block(b, atoms, snippets_dir)
        score = 100
        for f in findings:
            score -= PENALTY[f.sev]
        score = max(0, score)
        grades.append(score)
        name = b.get("name", b.get("key", "?"))
        crit = sum(1 for f in findings if f.sev == "CRITICAL")
        warn = sum(1 for f in findings if f.sev == "WARN")
        total_crit += crit
        total_warn += warn
        print(f"\n{grade(score)}  ({score:3d}/100)  {name}")
        if not findings:
            print("     -- clean: no edge-hygiene issues")
        for f in sorted(findings, key=lambda x: {"CRITICAL": 0, "WARN": 1, "INFO": 2}[x.sev]):
            tag = {"CRITICAL": "CRIT", "WARN": "WARN", "INFO": "info"}[f.sev]
            # strip the leading "[name] " for per-block listing
            msg = re.sub(r"^\[[^\]]*\]\s*", "", f.msg)
            print(f"     [{tag}] {msg}")

    avg = sum(grades) // len(grades)
    print("\n" + "=" * 68)
    print(f"batch grade {grade(avg)} (avg {avg}/100) | "
          f"{total_crit} critical | {total_warn} warnings across {len(blocks)} blocks")
    print("legend: CRIT = will distort backtest/live (fix before import) | "
          "WARN = overfit/robustness risk | info = nit")
    if args.strict and total_crit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
