"""Which prop firms the bridge can verify on: their saved MT5 account and their symbol names."""
from pathlib import Path

import yaml

from core import assetdata
from core.paths import MT5_ACCOUNTS
from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent
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


def names(asset: str) -> dict[str, str]:
    """The asset's symbol at each firm, `mt5:` of `assets/symbols/<asset>.yaml` — versioned
    with the asset and edited in the Activos zone (owner, 2026-09-30; it was a git-ignored
    `mt5/symbols.csv`). The owner's rule (encargo 35 §1 #3): a firm the asset does not name
    stops the job for that firm — never guessed.
    """
    return dict(assetdata.load(asset).get("mt5") or {})


def usable(asset: str) -> dict[str, dict]:
    """Every firm with a saved account, and whether this asset can be verified on it.

    Returns:
        {firm: {"account", "symbol", "why"}}: `why` is None when both are known, else the
        sentence saying which of the two is missing.
    """
    known = names(asset)
    out = {}
    for firm, account in MT5_ACCOUNTS.items():
        symbol = known.get(firm)
        why = None if symbol else (f"{asset} no tiene símbolo de {label(firm)} en "
                                   f"assets/symbols/{asset}.yaml (mt5.{firm}): añádelo en "
                                   "Activos; nunca se adivina")
        out[firm] = {"account": account, "symbol": symbol, "why": why}
    return out
