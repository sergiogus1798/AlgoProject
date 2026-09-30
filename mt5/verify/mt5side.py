"""The MT5 half of a check: compile the EA SQX exported, and backtest it on each firm's account."""
import re
import time
from pathlib import Path

import pandas as pd

from mt5 import metaeditor, tester, wine


def fixed_lots(source: str, lots: str) -> str:
    """The EA's source with its sizing switched to a fixed lot: `UseMoneyManagement = false`
    makes every sizing function return `mmLotsIfNoMM`, which is set to `lots`.

    SaveToFiles writes the EA with a sizing of its own (🔬 2026-09-29: «Fixed Amount» 100 USD
    for a strategy that stores FixedSize 0.1), and the tester cannot pass inputs: the default
    in the source is what runs. Raises when either input is missing rather than guess.
    """
    out, n = re.subn(r"input bool UseMoneyManagement = \w+;", "input bool UseMoneyManagement = false;",
                     source)
    out, m = re.subn(r"input double mmLotsIfNoMM = [\d.]+;", f"input double mmLotsIfNoMM = {lots};", out)
    if (n, m) != (1, 1):
        raise SystemExit("el EA exportado no trae UseMoneyManagement y mmLotsIfNoMM: no se le "
                         "puede fijar el tamaño de la estrategia")
    return out


def compile_ea(mq5: Path, stem: str, lots: str) -> dict:
    """Compile the exported EA under a name with no space, trading the strategy's fixed lot.

    Args:
        mq5: What SaveToFiles wrote, e.g. «Strategy 3.48.75.mq5».
        stem: The name it is compiled under: Wine splits a command-line argument at its
            first space (`wine.run`), so «Strategy 3.48.75» would never reach MetaEditor whole.
        lots: The strategy's own FixedSize, the one SQX's retest trades too.

    Returns:
        `metaeditor.expert`'s dict. Raises when it did not compile.
    """
    if not wine.close_terminal():
        raise SystemExit("el terminal de MT5 sigue abierto y MetaEditor no compila con él")
    safe = mq5.with_name(re.sub(r"\W+", "_", stem) + ".mq5")
    safe.write_text(fixed_lots(mq5.read_text(encoding="utf-8"), lots), encoding="utf-8")
    got = metaeditor.expert(safe)
    if not got["ok"] or not got["ex5_exists"]:
        raise SystemExit(f"{safe.name} no compila: {got['errors']} errores\n"
                         + "\n".join(got["messages"][:10]))
    return got


def backtest(expert: str, symbol: str, timeframe: str, window: tuple[str, str], model: str,
             deposit: float, leverage: int, account: dict, tag: str, cfg: dict) -> dict:
    """One tester pass on one firm's account, waited for.

    Args:
        expert: The compiled EA as the tester names it.
        symbol: The firm's symbol.
        timeframe: The strategy's.
        window: (from, to) YYYY-MM-DD.
        model: A key of `tester.MODELS`, chosen by the owner for each check.
        deposit: The balance SQX's retest starts from.
        leverage: The account's own.
        account: `{login, server}`.
        tag: The firm, in the run's id.
        cfg: The `mt5` block of config.yaml.

    Returns:
        {"trades": frame, "summary": the report's figures, "dir": the run's folder}.
    """
    if not wine.close_terminal():
        raise SystemExit("el terminal de MT5 sigue abierto y el tester no arranca con él")
    started = tester.start(expert, symbol, timeframe, window[0], window[1], model, deposit,
                           leverage, account, tag)
    deadline = time.monotonic() + cfg["max_minutes"] * 60
    while True:
        time.sleep(cfg["collect_every_s"])
        got = tester.collect(started["run"])
        if got["state"] == "done":
            return {"trades": pd.read_parquet(got["trades_file"]), "summary": got["summary"],
                    "dir": got["dir"]}
        if got["state"] == "no_report":
            raise SystemExit(f"el tester de {account['server']} acabó sin informe: {got['hint']}")
        if time.monotonic() > deadline:
            wine.close_terminal()
            raise SystemExit(f"el tester de {account['server']} no acabó en {cfg['max_minutes']} min")
