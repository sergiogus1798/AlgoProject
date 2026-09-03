#!/usr/bin/env python3
"""List the trading costs every project has configured, per instrument."""

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.paths import MASTER

FIELDS = ("instrument", "tickSize", "minDistance", "defaultSpread", "defaultSlippage",
          "decimals", "pointValue")


def commission(raw: str) -> str:
    """Readable form of the commission method stored as escaped XML.

    Args:
        raw: The InstrumentInfo commissions attribute, HTML-escaped XML.

    Returns:
        "<Method> <amount>", e.g. "SizeBased 8", or "" when no method is in use.
    """
    node = ElementTree.fromstring(html.unescape(raw))
    if node.get("use") != "true":
        return ""
    param = node.find(".//Param")
    return f"{node.get('type')} {param.text if param is not None else ''}".strip()


def instruments(cfx: Path) -> dict[str, dict]:
    """Every instrument one project configures, with its costs.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        SQX symbol to its InstrumentInfo fields plus a readable commission and swap flag.
        Costs live per symbol inside each task, not once per project.
    """
    found = {}
    with zipfile.ZipFile(cfx) as z:
        for name in z.namelist():
            if name == "config.xml":
                continue
            text = z.read(name).decode("utf-8", "replace")
            for block in re.findall(r"<Symbol name=\"([^\"]+)\"[^>]*>\s*<InstrumentInfo([^>]*)>", text):
                symbol, attrs = block
                info = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
                found[symbol] = {k: info.get(k) for k in FIELDS}
                found[symbol]["commission"] = commission(info["commissions"])
                found[symbol]["swap"] = 'use="true"' in html.unescape(info.get("swap", ""))
    return found


def main() -> None:
    """Print one row per instrument found across every project on the master."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    a = ap.parse_args()

    rows = {}
    for d in sorted((MASTER / "user/projects").iterdir()):
        cfx = d / "project.cfx"
        if cfx.exists():
            for symbol, info in instruments(cfx).items():
                rows.setdefault(symbol, {**info, "projects": []})["projects"].append(d.name)

    if a.json:
        print(json.dumps(rows, indent=2))
        return
    print(f"{'symbol':34} {'spread':>8} {'point':>8} {'tick':>8} {'commission':22} swap")
    for symbol, r in sorted(rows.items()):
        print(f"{symbol:34} {r['defaultSpread'] or '':>8} {r['pointValue'] or '':>8} "
              f"{r['tickSize'] or '':>8} {r['commission']:22} {r['swap']}")


if __name__ == "__main__":
    main()
