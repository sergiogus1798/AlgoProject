"""Everything one run of the exposure study reads, assembled once: window, bars, trades."""

from core.study import identity
from strategies.exposure import inputs


def load(project: str, databank: str, feed: str, symbol: str, cfg: dict) -> dict:
    """The inputs one.run() and many.run() read.

    Args:
        project, databank: Where the trades were exported from.
        feed: SQX feed name, e.g. XAUUSD_DukasM1_Infinox.
        symbol: Asset file name, e.g. XAUUSD.
        cfg: What `inputs.config` returned.

    Returns:
        The window from policy, its bars, the point value, the newest export read on the
        configured sample, the strategy names and their identity.
    """
    span = inputs.window(symbol, cfg["study"]["segment"])
    packed = inputs.newest(project, databank)
    frame = inputs.sample(packed, cfg["study"]["sample"])
    names = list(frame["strategy"].unique())
    return {"project": project, "databank": databank, "feed": feed, "symbol": symbol,
            "span": span, "bars": inputs.bars(feed, cfg["study"]["timeframe"], span),
            "point_value": inputs.point_value(symbol), "packed": packed, "frame": frame,
            "strategies": names, "identity": identity.lookup(project, databank, names)}
