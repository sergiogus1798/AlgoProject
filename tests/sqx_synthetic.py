"""Tiny synthetic .sqx strategies for the tests that only move files about: not a test itself.

Each file is a ZIP with the one XML `core.sqxfile` hashes plus a `Results/` entry that names its feed, so
identity, symbol and feed read as for a real strategy. Deterministic (the seed is the content) and built in
a few hundred bytes, so no strategy of the owner's has to sit in git (rule 7).
"""

import zipfile
from pathlib import Path

FEED = "USDJPY_DukasM1_the5ers_LOM_M30"
NAMES = ("Strategy 9.25.72", "Strategy 10.11.79", "Strategy 9.27.83")


def write(path: Path, seed: int, feed: str = FEED) -> Path:
    """Write one strategy; two seeds give two identities.

    Args:
        path: The `.sqx` to create.
        seed: Any int; it sets the one period the strategy carries.
        feed: The `<SYMBOL>_<feed>_LOM_<TF>` name its Results entry carries.

    Returns:
        `path`.
    """
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<StrategyFile Version="3.9.133" AppVersion="SQX Build 144.2953">\n'
        f"  <options><StrategyName>synthetic{seed}</StrategyName></options>\n"
        '  <Strategy name="New strategy" engine="MetaTrader">\n'
        f'    <Param name="Period" type="int" paramType="ParamTypePeriod" key="#Int1#">{20 + seed}</Param>\n'
        "  </Strategy>\n"
        "</StrategyFile>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("strategy_Portfolio.xml", xml)
        z.writestr(f"Results/Main: {feed}/dailyEquity.bin", bytes(8))
    return path


def databank(folder: Path, count: int = 3) -> list[Path]:
    """Fill a databank folder with `count` synthetic strategies named like SQX's own."""
    return [write(folder / f"{NAMES[k]}.sqx", k) for k in range(count)]
