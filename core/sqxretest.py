"""Read a Monte Carlo Retest result out of a .sqx: its simulation P/L vectors and its level table."""

import re
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import numpy as np

from core import sqxstats

HEADER = 4
RESULTS = "MonteCarloRetest_Results.xml"
ORIGINAL = "RobustnessOriginalOrders.bin"
# SQX produces these eleven and no others. Asking for any other level returns nothing at all.
CONFIDENCE = (50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100)

_MEMBER = re.compile(r"MonteCarloRetest_Simulation(\d+)Orders\.bin$")
_LEVEL = re.compile(r'<LevelStat level="(\d+)">\s*<SQStats[^>]*>([^<]+)</SQStats>')
_REFERENCE = re.compile(r'<RobustnessOriginalResults>\s*<SQStats[^>]*>([^<]+)</SQStats>')


def _orders(raw: bytes, member: str) -> np.ndarray:
    """Decode one orders member into the P/L of every trade it holds.

    Args:
        raw: The member's bytes.
        member: Its name, for the assertion message.

    Returns:
        P/L per trade in cents, chronological. The layout is a big-endian int32 trade count
        followed by that many big-endian int32 values, and four bytes per trade is the whole
        record -- there is no date, price, size or excursion in this file.
    """
    count = struct.unpack_from(">i", raw, 0)[0]
    assert len(raw) == HEADER + 4 * count, (
        f"{member}: {len(raw)} bytes but {count} trades needs {HEADER + 4 * count}")
    return np.frombuffer(raw, dtype=">i4", count=count, offset=HEADER).astype(np.int32)


def _prefix(archive: zipfile.ZipFile) -> str:
    """The one result folder holding this strategy's retest.

    Args:
        archive: An open .sqx.

    Returns:
        The folder every retest member sits in, e.g.
        "Results/Main: XAUUSD_M1_LOM_M30". Asserting there is exactly one is
        what stops two silent failures: a .sqx with no retest at all -- most robustness
        files on this machine are Monte Carlo *Manipulation* and carry an orders member but
        no retest -- and a multi-market strategy whose level table and P/L could otherwise
        be read from two different result folders.
    """
    found = {n.rsplit("/", 1)[0] for n in archive.namelist() if n.endswith(RESULTS)}
    assert len(found) == 1, f"{archive.filename}: {len(found)} retest results, expected one"
    return found.pop()


def _results(path: Path) -> str:
    """The retest result XML of one strategy.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        The text of MonteCarloRetest_Results.xml.
    """
    with zipfile.ZipFile(path) as archive:
        return archive.read(f"{_prefix(archive)}/{RESULTS}").decode("utf8", errors="replace")


def simulations(path: Path) -> dict:
    """Every simulation's P/L, in the ragged layout the metric reconstruction consumes.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        {"pnl": every simulation concatenated, cents; "offsets": where each one starts,
        length sims + 1; "index": the simulation number each slice came from, ascending}.
        Simulation lengths differ -- randomising parameters changes how many trades there
        are -- so a rectangular matrix would not hold them and the offsets are the contract.
    """
    with zipfile.ZipFile(path) as archive:
        prefix = _prefix(archive)
        members = {}
        for name in archive.namelist():
            found = _MEMBER.search(name)
            if found and name.startswith(prefix):
                members[int(found.group(1))] = name
        index = np.array(sorted(members), dtype=np.int32)
        vectors = [_orders(archive.read(members[i]), members[i]) for i in index]
    offsets = np.zeros(len(vectors) + 1, dtype=np.int64)
    offsets[1:] = np.cumsum([v.size for v in vectors], dtype=np.int64)
    return {"pnl": np.concatenate(vectors), "offsets": offsets, "index": index}


def original(path: Path) -> np.ndarray:
    """The P/L of the backtest the simulations were perturbed away from.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        P/L per trade in cents, chronological, same format as a simulation. This is the
        bridge to the stored metrics: summing it reproduces NetProfit to within the cent
        rounding, which is what calibrates every reconstructed formula.
    """
    with zipfile.ZipFile(path) as archive:
        member = f"{_prefix(archive)}/{ORIGINAL}"
        return _orders(archive.read(member), member)


def levels(path: Path) -> dict[int, dict]:
    """The confidence table SQX stored, decoded.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        {confidence level: {metric name: value}}, 148 metrics per level. Each value is a
        marginal order statistic of its own metric, so two metrics at one level come from
        two different simulations and the pair is not a scenario.
    """
    return {int(level): sqxstats.records(blob) for level, blob in _LEVEL.findall(_results(path))}


def reference(path: Path) -> dict:
    """The original backtest's metrics as SQX computed them, from the retest result.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        All 152 statistics of the unperturbed run. Four of them -- DataLength and the three
        MaxNewHighDuration fields -- are absent from the level blobs, which carry 148.
    """
    return sqxstats.records(_REFERENCE.search(_results(path)).group(1))


def meta(path: Path) -> dict:
    """What the retest declares about itself.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        Declared simulation count, instrument, timeframe, date range, and the prose line
        SQX writes for each active method. `declared` is what was asked for, not what was
        stored: a run cut short leaves fewer files and the level table is then shifted.
        `instrument` is symbol and feed run together, "XAUUSD_M1" -- it is not
        a symbol and does not compare equal to one. `core.sqxfile.symbol` splits them.
    """
    xml = _results(path)
    return {"declared": int(re.search(r"<NumberOfSimulations>(\d+)", xml).group(1)),
            "instrument": re.search(r"<Symbol>(.*?)</Symbol>", xml).group(1),
            "timeframe": re.search(r"<TimeFrame>(.*?)</TimeFrame>", xml).group(1),
            "date_range": re.search(r"<DateRange>(.*?)</DateRange>", xml).group(1),
            "methods": re.findall(r"<Method>(.*?)</Method>", xml)}


def settings(path: Path) -> dict:
    """The retest configuration as it was actually set, method by method.

    Args:
        path: A .sqx file carrying a Monte Carlo Retest result.

    Returns:
        {"methods": {SQX method type: {parameter: value}} for the active ones only,
        "simulations", "full_sample", "precision"}. This is the provenance of a databank:
        the prose in `meta` says what ran, this says with which numbers.
        `full_sample` being true does not mean the run saw out-of-sample data -- it widens
        the retest to whatever the strategy's own split is, and an IS-only strategy has none.
        `lastSettings.xml` is the last state of the whole cross-check dialog and holds every
        block whether it ran or not, so the retest's own use attribute is asserted: without
        it a Monte Carlo *Manipulation* strategy returns a full, plausible, wrong config.
    """
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("lastSettings.xml"))
    retest = root.find(".//MonteCarloRetest")
    assert retest.get("use") == "true", f"{path}: lastSettings.xml says no retest ran"
    block = retest.find("Settings")
    methods = {m.get("type"): {p.get("key"): (p.text or "").strip()
                               for p in m.findall("./Params/Param")}
               for m in block.findall("./Methods/Method") if m.get("use") == "true"}
    return {"methods": methods,
            "simulations": int(block.findtext("NumberOfSimulations")),
            "full_sample": block.findtext("MCUseFullSample") == "true",
            "precision": block.findtext("MCBacktestPrecision")}
