#!/usr/bin/env python3
"""Golden-file test for sqx.inspect.strategymeta: the fields the strategy panel shows."""

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, sqxfile
from sqx.inspect.strategymeta import read
from sqx.structural import logic
from sqx.variants.build import rewrite, stoploss

HERE = Path(__file__).parent / "fixtures"
TEMPLATE = HERE / "strategy.sqx"                 # AlgoWizard short, SL/PT ATR, trailing
OOS = HERE / "strategymeta_oos.sqx"              # XAUUSD Strategy 10.13.25, results stripped
GENERIC = HERE / "strategymeta_generic.sqx"      # GBPJPY generic build: bare-Item AND, exits
# XAUUSD's config.xml cut to its OOS retest, plus tasks that all claim OOS: an inactive twin
# priced at spread 7, AUDJPY's CustomAnalysis (no setup), EURUSD's WFM AutomaticRetest
# relabelled to OOS (costs under CustomData, no swap), and a task whose member is missing.
CFX = HERE / "strategymeta_task.cfx"
GOLDEN = HERE / "strategymeta.golden.json"
SIDE = {1: "long", -1: "short"}


def grafted(folder: Path) -> Path:
    """The OOS fixture with an ATR stop of 2.5 grafted, written where the test runs."""
    parts = rewrite.members(OOS)
    parts[rewrite.PORTFOLIO] = stoploss.graft(parts[rewrite.PORTFOLIO].decode("utf-8"),
                                              2.5).encode("utf-8")
    out = folder / "grafted.sqx"
    with zipfile.ZipFile(out, "w") as z:
        for name, blob in parts.items():
            z.writestr(name, blob)
    return out


def parse(folder: Path) -> dict:
    """read() on every fixture, the asset card hash dropped: it moves with assets/."""
    bank = folder / "OOS"
    bank.mkdir()
    shutil.copy(OOS, bank / OOS.name)
    found = {"template": read(TEMPLATE), "oos_with_cfx": read(bank / OOS.name, CFX),
             "generic": read(GENERIC), "grafted": read(grafted(folder))}
    return {k: {f: v for f, v in m.items() if f != "asset_card_sha256"} for k, m in found.items()}


def invariants(result: dict) -> list[str]:
    """What must hold whatever the golden file says."""
    bad = []
    for key, path in (("template", TEMPLATE), ("oos_with_cfx", OOS), ("generic", GENERIC)):
        sides = {SIDE[d] for d in logic.direction(sqxfile.rules(path))}
        if result[key]["direction"] != ("both" if len(sides) == 2 else sides.pop()):
            bad.append(f"{key}: la dirección no coincide con logic.direction")
    for key, path in (("template", TEMPLATE), ("oos_with_cfx", OOS)):
        mine = [[r[k] for k in ("signal", "operator", "index", "block")]
                for r in result[key]["entries"]]
        theirs = [[r[k] for k in ("signal", "operator", "index", "block")]
                  for r in logic.conditions(sqxfile.rules(path))]
        if mine != theirs:
            bad.append(f"{key}: las entradas no son las de logic.conditions")
    if result["grafted"]["orders"][0]["stop_loss"] != {"formula": "ATRBasedValue",
                                                       "Value": "2.5", "AtrPeriod": "20"}:
        bad.append("el stop injertado no se lee como ATRBasedValue 2.5 x ATR(20)")
    if result["oos_with_cfx"]["orders"][0]["stop_loss"] is not None:
        bad.append("la madre sin stop lee un stop")
    if len(result["generic"]["entries"]) < 3 or not result["generic"]["exits"]:
        bad.append("el AND del builder genérico no se lee término a término")
    backtest = result["oos_with_cfx"]["backtest"]
    if [t["type"] for t in backtest] != ["Retest", "Retest", "CustomAnalysis",
                                         "AutomaticRetest", "Retest"]:
        bad.append("no salen las cinco tareas que escriben (o podrían escribir) OOS")
    else:
        if backtest[0]["costs"] != result["oos_with_cfx"]["last_test"]["costs"]:
            bad.append("la tarea activa no tiene los costes del último test guardado")
        if backtest[2]["costs"] is not None:
            bad.append("el CustomAnalysis lee unos costes que no tiene")
        if backtest[3]["setup_from"] != "CustomData" or backtest[3]["costs"]["swap"] is not None:
            bad.append("el AutomaticRetest no lee sus costes de CustomData")
        if "error" not in backtest[4]:
            bad.append("la tarea sin fichero no sale con su error")
    card = read(OOS)["asset_card_sha256"]
    if card != hashlib.sha256((assetdata.SYMBOLS / "XAUUSD.yaml").read_bytes()).hexdigest():
        bad.append("asset_card_sha256 no es el sha256 de assets/symbols/XAUUSD.yaml")
    return bad


def main() -> None:
    """Compare against the golden file, or write it when run with --bless."""
    with tempfile.TemporaryDirectory() as tmp:
        result = parse(Path(tmp))
    bad = invariants(result)
    if "--bless" in sys.argv and not bad:
        GOLDEN.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"blessed {GOLDEN}")
        return
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if result != expected:
        bad.append("sqx.inspect.strategymeta ya no lee estas estrategias igual que el golden")
    if bad:
        print("test_strategymeta: FAILED\n  " + "\n  ".join(bad))
        sys.exit(1)
    print("test_strategymeta: ok")


if __name__ == "__main__":
    main()
