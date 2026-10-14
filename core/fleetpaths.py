"""Where the live MT5 fleet's files are, and each account's plan from machine.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml

from core.paths import DATA, ROOT

# The fleet's tree under the data root. MetaTracker's `--root` points it at a fixture folder.
FLEET = DATA / "fleet"


def live_dir() -> Path:
    """The collector's copy of what the VPS wrote: `<login>.json`, `<login>.history.json`, `vps.json`."""
    return FLEET / "live"


def history_dir(login: int) -> Path:
    """One account's minute history: `<server day>.parquet` and `excursions.json`."""
    return FLEET / "history" / str(login)


def workbook() -> Path:
    """The owner's Excel of which EA goes on which account."""
    return FLEET / "Flota_de_cuentas.xlsx"


@lru_cache(maxsize=1)
def _accounts(mtime_ns: int) -> dict[int, dict]:
    """The `fleet.vps.accounts` of machine.yaml as of one modification time."""
    cfg = yaml.load(
        (ROOT / "config" / "machine.yaml").read_text(encoding="utf-8"),
        Loader=yaml.CSafeLoader,
    )
    return ((cfg.get("fleet") or {}).get("vps") or {}).get("accounts") or {}


def accounts() -> dict[int, dict]:
    """Each fleet account's plan by login — `{firm, plan, size, phase}` — which no file of the firm carries."""
    return _accounts((ROOT / "config" / "machine.yaml").stat().st_mtime_ns)
