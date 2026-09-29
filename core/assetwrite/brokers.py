"""Write one asset's `costs.commission.brokers` table — the per-broker figures `use` is picked from."""

from core.assetdata import SYMBOLS
from core.assetyaml import read, write


def set_brokers(symbol: str, brokers: dict) -> dict:
    """Replace the whole per-broker commission table of one asset, in one write.

    Args:
        symbol: Asset name.
        brokers: `{broker: {method, value, unit, source, date, confirmed, note?}}` — one entry
            per firm this project prices against (owner, 2026-09-29), never edited by hand:
            a figure this session could not confirm on the firm's own page is `value: null,
            confirmed: false`, with `note` saying what an aggregator claims instead.

    Returns:
        The table as written.
    """
    path = SYMBOLS / f"{symbol}.yaml"
    doc = read(path)
    doc["costs"]["commission"]["brokers"] = brokers
    write(path, doc)
    from core.assetwrite import reindex

    reindex()
    return {"file": str(path), "symbol": symbol, "brokers": brokers}
