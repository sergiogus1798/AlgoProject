"""Give a cross-check task the feed definitions of its extra markets, from SQX's registry."""

import re
from datetime import datetime, timedelta, timezone

from sqx.projects import registryxml, resources


def _ms(day: str, end: bool) -> int:
    """A YYYY.MM.DD bound as the epoch milliseconds a <Symbol> carries, `end` inclusive."""
    at = datetime.strptime(day, "%Y.%m.%d").replace(tzinfo=timezone.utc)
    return int((at + timedelta(days=1 if end else 0)).timestamp() * 1000)


def with_feeds(text: str, used: list[dict]) -> str:
    """Give the task every extra market's feed definition, loading the window it trades.

    Args:
        text: A task XML, its Setups already written.
        used: The markets written, each with `feed` and `window`.

    Returns:
        The task with one <Symbol> per extra market, its <InstrumentInfo> and <Broker>
        beside it. A feed the task lacks is written from SQX's data registry, the builder's
        own route for the main feed (`resources.definitions`), and refused when the registry
        lacks it. Each <Symbol> loads exactly its Setup's window (`setups.set_data_range`),
        and `registryxml.refresh` brings every block to the registry's text of today.
    """
    for m in used:
        if not any(k.group(1) == m["feed"] for k in resources.SYMBOL.finditer(text)):
            symbol, info, broker = resources.definitions(None, m["feed"])
            text = text.replace("</Symbols>", f"  {symbol}\n    </Symbols>", 1)
            if info not in text.split("<Instruments>")[1].split("</Instruments>")[0]:
                text = text.replace("<Instruments>", f"<Instruments>\n      {info}", 1)
            held = text.split("<Brokers>")[1].split("</Brokers>")[0]
            if f'id="{resources.BROKER.search(broker).group(1)}"' not in held:
                text = text.replace("<Brokers>", f"<Brokers>\n      {broker}", 1)
        a, b = _ms(m["window"][0], False), _ms(m["window"][1], True)
        text = resources.SYMBOL.sub(
            lambda k, a=a, b=b, feed=m["feed"]: k.group(0) if k.group(1) != feed else re.sub(
                r'dateTo="\d+"', f'dateTo="{b}"',
                re.sub(r'dateFrom="\d+"', f'dateFrom="{a}"', k.group(0), count=1), count=1),
            text)
    return registryxml.refresh(text)
