"""Which prop firms the bridge can verify on: their saved MT5 account and their symbol names."""
import csv
from pathlib import Path

import yaml

from core.paths import MT5_ACCOUNTS
from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent
SYMBOLS = HERE.parent / "symbols.csv"
CONFIG = HERE / "config.yaml"
# How each firm's key is spelled for the owner (window, reports) — never plain .upper()
# (owner, 2026-09-29: "FTMO" en mayúsculas, "Hantec" con H mayúscula).
LABEL = {"ftmo": "FTMO", "hantec": "Hantec"}


def label(firm: str) -> str:
    """The firm's key spelled the way the owner reads it, e.g. `hantec` -> `Hantec`."""
    return LABEL.get(firm, firm)


def config(overrides: list[str] = ()) -> dict:
    """config.yaml with the ledger's thresholds filled in, then the --set overrides."""
    cfg = thresholds.fill(yaml.safe_load(CONFIG.read_text(encoding="utf-8")))
    return study_config.apply(cfg, list(overrides))


def table() -> dict[str, dict[str, str]]:
    """`mt5/symbols.csv` as {SQX asset: {firm: the firm's symbol}}, empty cells left out.

    The owner's rule (encargo 35 §1 #3): the SQX name is the key, one column per firm, and an
    asset missing from a firm's column stops the job for that firm — never guessed.
    """
    with SYMBOLS.open(encoding="utf-8") as f:
        return {row["sqx"]: {k: v for k, v in row.items() if k != "sqx" and v}
                for row in csv.DictReader(f)}


def usable(asset: str) -> dict[str, dict]:
    """Every firm with a saved account, and whether this asset can be verified on it.

    Returns:
        {firm: {"account", "symbol", "why"}}: `why` is None when both are known, else the
        sentence saying which of the two is missing.
    """
    names = table().get(asset, {})
    out = {}
    for firm, account in MT5_ACCOUNTS.items():
        symbol = names.get(firm)
        why = None if symbol else (f"{asset} no tiene símbolo de {firm} en mt5/symbols.csv: "
                                   "añádelo; nunca se adivina")
        out[firm] = {"account": account, "symbol": symbol, "why": why}
    return out
