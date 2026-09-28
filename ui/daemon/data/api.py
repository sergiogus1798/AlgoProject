"""The Datos zone's routes: the catalogue of the data root, the assets, their bars and their step-4 studies."""

from fastapi import APIRouter

from ui.daemon.data import catalogue as tree
from ui.daemon.data import market

ROUTER = APIRouter()


def _refused(feed: str, known: list) -> dict | None:
    """The sentence for a feed no data tree holds, None for a known one.

    Args:
        feed: What the window sent.
        known: The feeds of the tree asked for.

    Returns:
        `{"error": sentence}` or None. Checked against the listing, so a name can never
        climb out of the data root.
    """
    return None if feed in known else {"error": f"No conozco el feed «{feed}» en este árbol."}


@ROUTER.get("/api/data/catalogue")
def catalogue() -> dict:
    """Every tree of AlgoData with its size, newest write, files and manifests.

    Returns:
        As `catalogue.catalogue`, or `{"error": sentence}`.
    """
    try:
        return tree.catalogue()
    except Exception as e:  # noqa: BLE001 — the boundary with a person: a sentence, never a 500
        return {"error": f"No pude leer el catálogo de AlgoData: {type(e).__name__}: {e}"}


@ROUTER.get("/api/data/assets")
def assets() -> dict:
    """Every asset with its bar, spread and feed-quality feed.

    Returns:
        `{"assets": [...]}` as `market.assets`, and the timeframes the zone offers, or
        `{"error": sentence}`.
    """
    try:
        return {"assets": market.assets(), "timeframes": list(market.TIMEFRAMES)}
    except Exception as e:  # noqa: BLE001 — the boundary with a person
        return {"error": f"No pude listar los activos de AlgoData: {type(e).__name__}: {e}"}


@ROUTER.get("/api/data/bars")
def bars(feed: str = "", tf: str = "D1", since: str = "") -> dict:
    """One feed's OHLC at D1, H4 or H1 from the bar library.

    Args:
        feed: A feed of `bars/`, e.g. "XAUUSD_DukasM1_Infinox".
        tf: "D1", "H4" or "H1".
        since: First day as YYYY-MM-DD, empty for the whole history.

    Returns:
        As `market.bars`, or `{"error": sentence}`.
    """
    refused = _refused(feed, [a["bars"] for a in market.assets()])
    if refused:
        return refused
    if tf not in market.TIMEFRAMES:
        return {"error": f"Timeframe «{tf}» no ofrecido aquí: {', '.join(market.TIMEFRAMES)}."}
    try:
        return market.bars(feed, tf, since)
    except Exception as e:  # noqa: BLE001 — the boundary with a person
        return {"error": f"No pude leer las velas de {feed} {tf}: {type(e).__name__}: {e}"}


@ROUTER.get("/api/data/spread")
def spread(feed: str = "", part: str = "spread") -> dict:
    """One tick feed's spread report or its band, as `studies.data.spread` wrote them.

    Args:
        feed: A folder of `spread/`, e.g. "XAUUSD_DarwTick_Infinox".
        part: "spread" (the scan) or "band" (the MC Retest band).

    Returns:
        `{"result": contract dict}` or `{"error": sentence}`.
    """
    if part not in ("spread", "band"):
        return {"error": f"Parte «{part}» no válida: spread o band."}
    return _refused(feed, market.feeds("spread")) or market.study(part, feed)


@ROUTER.get("/api/data/feedquality")
def feedquality(feed: str = "") -> dict:
    """One M1 feed's quality report, as `studies.data.feedQuality.scan` wrote it.

    Args:
        feed: A folder of `feedQuality/`, e.g. "XAUUSD_DukasM1_Infinox".

    Returns:
        `{"result": contract dict}` or `{"error": sentence}`.
    """
    return _refused(feed, market.feeds("feedQuality")) or market.study("feedQuality", feed)
