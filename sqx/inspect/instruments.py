#!/usr/bin/env python3
"""List the trading costs every project has configured, per instrument."""

import argparse
import html
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER

FIELDS = ("instrument", "tickSize", "minDistance", "defaultSpread", "defaultSlippage",
          "decimals", "pointValue")
# The MC Retest randomize methods that carry a {Min, Max} range, and the `mc_retest.<key>`
# of assets/symbols/<S>.yaml each feeds.
MC_METHODS = {"RandomizeSpread": "spread", "RandomizeSlippage": "slippage"}


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


def mc_ranges(root: Path, sqx_symbol: str) -> dict[str, dict] | None:
    """The MC Retest spread/slippage ranges one install's own projects carry for a symbol.

    Reads whatever `project.cfx` already sits on disk under `root/user/projects/` — never
    starts or queries the install (feedback 2026-09-29 §1.7: MC Retest runs on the custodian,
    so its own carried range is what the Activos card should show, not the master's).

    Args:
        root: An install's folder, e.g. `core.paths.WORKERS["custodian"]["path"]`.
        sqx_symbol: The feed name, as `assets/symbols/<S>.yaml`'s `sqx_symbol` names it.

    Returns:
        {"spread": {min, max}, "slippage": {min, max}} from the first switched-on MC Retest
        task carrying this symbol, missing keys when only one method is on; None when this
        install has no project with one yet.
    """
    projects = root / "user/projects"
    if not projects.is_dir():
        return None
    for d in sorted(projects.iterdir()):
        cfx = d / "project.cfx"
        if not cfx.exists():
            continue
        with zipfile.ZipFile(cfx) as z:
            for name in z.namelist():
                if name == "config.xml":
                    continue
                text = z.read(name).decode("utf-8", "replace")
                if f'instrument="{sqx_symbol}"' not in text or '<MonteCarloRetest use="true"' not in text:
                    continue
                got = {}
                for method, key in MC_METHODS.items():
                    m = re.search(rf'<Method use="true" type="{method}">\s*<Params>\s*'
                                 r'<Param key="Min"[^>]*>([\d.]+)</Param>\s*'
                                 r'<Param key="Max"[^>]*>([\d.]+)</Param>', text)
                    if m:
                        got[key] = {"min": float(m.group(1)), "max": float(m.group(2))}
                if got:
                    return got
    return None


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
