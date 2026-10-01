"""Everything one run of the ATR stop study reads, assembled once: trades, bars, ATR, windows, batch."""

from pathlib import Path

from core import sqxfile
from core.study import identity
from engines.market import atr as sqx_atr
from studies.closing.atrCalculator import inputs


def load(project: str, databanks: list[str], feed: str, symbol: str, timeframe: str,
         work: Path | None, cfg: dict) -> dict:
    """The inputs one.run() reads.

    Args:
        project: Where the trades were exported from.
        databanks: One or more databanks of that project — the three WFC legs of a retest,
            or one export that already spans the windows. The newest export of each.
        feed: SQX feed name of the main market, e.g. XAUUSD_M1.
        symbol: Asset file name, e.g. XAUUSD.
        timeframe: The strategy's timeframe; the ATR is read on its bars.
        work: The stop-loss batch (`sqx.variants.stopgrid`) the exports came from, or None
            when the exports hold the strategies themselves.
        cfg: What `inputs.config` returned.

    Returns:
        `trades` (every exported trade on the main market, with `segment`), `bars_index` and
        `atr` on the strategy's timeframe, `point_value`, `spans`, `batch` (the manifest or
        None), `strategies` (mother names), `reference` (mother -> the export name holding
        its trades without a stop), `identity`, and the `packed` files read.
    """
    spans = inputs.windows(symbol)
    packed = [inputs.newest(project, d) for d in databanks]
    trades = inputs.trades(packed, feed, spans)
    bars = inputs.bars(feed, timeframe)
    batch = inputs.batch(work) if work else None
    if batch is None:
        names = sorted(trades["strategy"].unique())
        reference = {n: n for n in names}
        ids = identity.lookup(project, databanks[0], names)
    else:
        refs = batch[batch["stratum"] == "reference"]
        reference = dict(zip(refs["strategy"], refs["variant_id"]))
        names = sorted(reference)
        ids = {r.strategy: sqxfile.identity(Path(r.mother)) for r in refs.itertuples()}
    return {"project": project, "databanks": databanks, "feed": feed, "symbol": symbol,
            "timeframe": timeframe, "spans": spans, "packed": packed, "trades": trades,
            "bars_index": bars.index, "atr": sqx_atr.sqx(bars, cfg["stop"]["atr_period"]),
            "point_value": inputs.point_value(symbol), "batch": batch, "work": work,
            "strategies": names, "reference": reference, "identity": ids}
