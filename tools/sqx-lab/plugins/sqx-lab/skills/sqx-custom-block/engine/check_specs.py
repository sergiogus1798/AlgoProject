"""check_specs.py — gate research output against the catalog before authoring.

The research subagent (reference/research-prompt.md) returns candidate block specs as JSON.
This checks each spec is actually BUILDABLE on the install: every atom it names exists in the
catalog, none are talib_* (Stockpicker NPE), and multi-output atoms are flagged to pick a
#Line#. It turns the "no phantom atoms" lesson into a mechanical gate so nothing un-buildable
reaches the authoring step.

Usage:
  python engine/check_specs.py specs.json --catalog catalog.json

Exit 0 = every spec is buildable; 1 = at least one is blocked (phantom atom or talib).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# value atoms the grammar provides directly (not in the indicator catalog)
GRAMMAR_ATOMS = {"Number", "Close", "Open", "High", "Low"}


def check(specs: list[dict], atoms: dict) -> tuple[list[dict], int]:
    report = []
    blocked = 0
    for s in specs:
        name = s.get("name", "<unnamed>")
        issues, quality, status = [], [], "BUILDABLE"
        for key in s.get("atoms", []):
            if key in GRAMMAR_ATOMS:
                continue
            e = atoms.get(key)
            if e is None:
                issues.append(f"phantom atom '{key}' (not in catalog)")
                status = "BLOCKED"
            elif not e.get("usable_single_symbol", True):
                issues.append(f"'{key}' is talib (unusable single-symbol)")
                status = "BLOCKED"
            elif e.get("multi_output"):
                issues.append(f"'{key}' is multi-output — pick a #Line#")
                if status == "BUILDABLE":
                    status = "BUILDABLE*"
        ni = s.get("needs_indicator")
        if ni:
            issues.append(f"wishes for missing indicator '{ni}' (substituted or to compile)")
            if status == "BUILDABLE":
                status = "NEEDS-INDICATOR"
        # --- cheap QUALITY hints (the real edge-quality gate is the critic + assess.py) ----
        if (s.get("repaint_risk") or "none") == "likely":
            quality.append("repaint-likely: read confirmed (shift>=1) or drop")
        if (s.get("operator") or "") in ("and_op", "or_op"):
            quality.append("compound operator: ensure the mechanism is genuinely a conjunction")
        if len(s.get("params", [])) > 2:
            quality.append(f"{len(s.get('params', []))} knobs (>2): overfit surface")
        if not (s.get("hypothesis") or "").strip():
            quality.append("no falsifiable hypothesis — weak edge justification")
        if status == "BLOCKED":
            blocked += 1
        report.append({"name": name, "status": status, "confidence": s.get("confidence", "?"),
                       "issues": issues, "quality": quality})
    return report, blocked


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", help="JSON file of researcher specs ({specs:[...]} or [...])")
    ap.add_argument("--catalog", required=True, help="catalog.json")
    args = ap.parse_args(argv)

    try:                                    # never crash on a non-UTF-8 console codepage
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    raw = json.loads(Path(args.specs).read_text(encoding="utf-8"))
    specs = raw.get("specs", raw) if isinstance(raw, dict) else raw
    atoms = json.loads(Path(args.catalog).read_text(encoding="utf-8")).get("atoms", {})

    report, blocked = check(specs, atoms)
    print(f"{'spec':32s} {'status':16s} conf        issues")
    print("-" * 90)
    qflags = 0
    for r in report:
        print(f"{r['name'][:32]:32s} {r['status']:16s} {r['confidence'][:11]:11s} "
              + ("; ".join(r["issues"]) if r["issues"] else "-"))
        for q in r.get("quality", []):
            qflags += 1
            print(f"{'':32s} {'  ! quality':16s} {'':11s} {q}")
    ok = len(report) - blocked
    print("-" * 90)
    print(f"{ok}/{len(report)} buildable"
          + (f"  |  {blocked} BLOCKED (drop or fix before authoring)" if blocked else "")
          + (f"  |  {qflags} quality flag(s) — run the critic + assess.py" if qflags else ""))
    print("(* = pick a #Line#;  NEEDS-INDICATOR = substitute or compile;  ! = edge-quality hint)")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
