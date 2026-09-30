"""Write one asset's Cross Market check — `_markets.yaml`'s `family`/`structural` feeds."""

import yaml
from ruamel.yaml.comments import CommentedMap

from core.assetdata import MARKETS
from core.assetyaml import read, write
from core.paths import ASSETS


def declare_main(symbol: str, sqx_symbol: str) -> dict:
    """Give an asset its own Cross Market block, empty, if it does not have one yet.

    Owner, 2026-09-29 (feedback §1.7): every asset with a card is a main, not only the ones
    someone got around to declaring — the warning was noise, not a finding. `timeframe`
    starts `null`: it is genuinely per-run (which template built it), so it is filled the
    day this asset's Cross Market retest actually configures one, never guessed here.

    Args:
        symbol: The asset, as `assets/symbols/<symbol>.yaml` names it.
        sqx_symbol: Its `sqx_symbol`, to declare as `main`.

    Returns:
        Its block: the existing one, untouched, or the new empty one.
    """
    path = ASSETS / MARKETS
    doc = read(path)
    if symbol not in doc:
        block = CommentedMap({"main": sqx_symbol, "timeframe": None,
                              "categories": CommentedMap({"family": [], "structural": []})})
        doc[symbol] = block
        write(path, doc)
    return doc[symbol]


def set_market(symbol: str, category: str, feeds: list[dict]) -> dict:
    """Make one category of one asset's Cross Market check hold exactly these markets.

    Args:
        symbol: The main asset.
        category: "family" or "structural".
        feeds: Every {feed, data_from} it must hold; a removal is a market left out.

    Returns:
        The category as written. The list is edited in place, not replaced: a market that
        stays keeps its line and its comments, so adding or removing one is a one-line diff.
    """
    path = ASSETS / MARKETS
    doc = read(path)
    cats = doc[symbol]["categories"]
    rows = cats[category]
    wanted = [f["feed"] for f in feeds]
    for i in reversed(range(len(rows))):
        if rows[i]["feed"] not in wanted:
            del rows[i]
    rows.extend([flow(f) for f in feeds if f["feed"] not in {r["feed"] for r in rows}])
    rows.fa.set_block_style() if rows else rows.fa.set_flow_style()
    if not rows and rows.ca.end:   # an emptied list drops the lines after it: its key keeps them
        rows.ca.end[0].value = "\n" + "".join(" " * t.column * t.value.startswith("#") + t.value
                                               for t in rows.ca.end)
        cats.ca.items.setdefault(category, [None] * 4)[2] = rows.ca.end[0]   # keep its comment above
    write(path, doc)
    return {"symbol": symbol, "category": category, "feeds": feeds}


def flow(feed: dict) -> CommentedMap:
    """One market as this file writes them: a flow mapping carrying a real date.

    Args:
        feed: {feed, data_from} as the window sends it, both as text; no date is `null`.

    Returns:
        A one-line mapping, like every market the file already holds: a block mapping
        would make the diff of one added market unreadable.
    """
    since = feed["data_from"] and yaml.safe_load(str(feed["data_from"]))
    one = CommentedMap({"feed": feed["feed"], "data_from": since or None})
    one.fa.set_flow_style()
    return one
