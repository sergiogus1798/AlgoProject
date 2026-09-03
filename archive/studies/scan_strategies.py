#!/usr/bin/env python3
"""Scan every .sqx in the XAUUSD databanks and report its EXIT configuration.

Read-only: opens each .sqx (a ZIP) and parses the inner strategy_Portfolio.xml.
No SQX process is required and nothing on disk is modified.
"""
import re, sys, zipfile, json
from pathlib import Path
from collections import Counter

ROOT = Path("/home/sergioguslw/Desktop/SQX/user/projects/XAUUSD/databanks")

def analyse(p: Path):
    """Return a dict describing one strategy's exits, or None if unreadable."""
    try:
        z = zipfile.ZipFile(p)
        names = z.namelist()
        xml = z.read("strategy_Portfolio.xml").decode("utf-8", "replace")
    except Exception as e:
        return {"file": str(p), "error": str(e)}

    # Symbol / timeframe come free from the ZIP entry names — no need to open
    # the 5.8 MB settings.xml (KNOWHOW §1).
    main = re.search(r"Results/Main: ([^/]+)/", "\n".join(names))
    feed = main.group(1) if main else "?"
    tf = feed.rsplit("_", 1)[-1] if main else "?"

    flat = re.sub(r">\s*<", "><", xml)

    def formula_for(param_key):
        """The <Formula key=...> used by a given exit Param, or None."""
        m = re.search(
            r'<Param key="#%s#"[^>]*>(.*?)</Param>' % re.escape(param_key),
            flat, re.S)
        if not m:
            return None
        f = re.search(r'<Formula key="([^"]+)"', m.group(1))
        return f.group(1) if f else None

    def formula_params(param_key):
        """Numeric sub-params of that formula (e.g. the ATR period/multiple)."""
        m = re.search(
            r'<Param key="#%s#"[^>]*>(.*?)</Param>' % re.escape(param_key),
            flat, re.S)
        if not m:
            return {}
        return dict(re.findall(r'<Param key="#([^#]+)#"[^>]*>([^<]*)</Param>',
                               m.group(1)))

    # Signal variables hold the resolved values of #...# placeholders.
    variables = {}
    for vm in re.finditer(r"<variable>(.*?)</variable>", flat, re.S):
        b = vm.group(1)
        vid = re.search(r"<id>([^<]*)</id>", b)
        val = re.search(r"<value>([^<]*)</value>", b)
        if vid and val:
            variables[vid.group(1)] = val.group(1)

    def resolve(v):
        """A param value may be a literal or the name of a signal variable."""
        return variables.get(v, v)

    sl_formula = formula_for("StopLoss.StopLoss")
    pt_formula = formula_for("ProfitTarget.ProfitTarget")
    trail      = formula_for("TrailingStop.TrailingStop")
    sl_params  = formula_params("StopLoss.StopLoss")

    bars_raw = re.search(
        r'<Param key="#ExitAfterBars.ExitAfterBars#"[^>]*>([^<]*)</Param>', flat)
    bars = resolve(bars_raw.group(1)) if bars_raw else None

    # Which directions actually have a populated entry rule
    has_long  = bool(re.search(r'name="Long entry"',  flat))
    has_short = bool(re.search(r'name="Short entry"', flat))

    return {
        "file": str(p),
        "name": p.stem,
        "databank": p.parent.name,
        "feed": feed,
        "tf": tf,
        "sl_formula": sl_formula,
        "sl_params": {k: resolve(v) for k, v in sl_params.items()},
        "pt_formula": pt_formula,
        "trailing": trail,
        "exit_after_bars": bars,
        "long_rule": has_long,
        "short_rule": has_short,
    }

def main():
    files = sorted(ROOT.rglob("*.sqx"))
    rows = [analyse(f) for f in files]
    out = Path("/home/sergioguslw/Desktop/AlgoProject/analysis/strategy_scan.json")
    out.write_text(json.dumps(rows, indent=1))

    print(f"scanned {len(rows)} strategies -> {out}\n")
    for key in ("databank", "tf", "sl_formula", "pt_formula", "trailing",
                "exit_after_bars"):
        c = Counter(str(r.get(key)) for r in rows)
        print(f"{key}:")
        for k, v in c.most_common():
            print(f"    {v:5d}  {k}")
        print()
    # Any stop params seen at all
    sp = Counter(json.dumps(r.get("sl_params")) for r in rows)
    print("stop-loss formula params:")
    for k, v in sp.most_common(10):
        print(f"    {v:5d}  {k}")

if __name__ == "__main__":
    main()
