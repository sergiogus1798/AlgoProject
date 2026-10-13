"""Whole databanks written from a live session's memory by the AlgoBank snippet, one `.abk` each."""

import shutil

from core import bankfile, sqxstats
from core.paths import bank_dir
from sqx.projects import live
from sqx.snippets import install, toolproject

# The sample types a stored result carries statistics for (🔬 2026-10-13, the five of every
# result of a WFM strategy on the conductor). The snippet asks SQX for exactly these.
SAMPLES = (10, 11, 20, 21, 127)
# The statistics a blob stores under their own name, with their type (🔬 2026-10-13, same file).
NAMED = {"i": ("DataLength",), "l": ("MaxNewHighDurationTo", "MaxNewHighDurationFrom"), "f": (
    "AvgDrawdown", "AddMarketsSharpeRatioMedian", "SortinoRatio", "AddMarketsRetDDMedian",
    "MaxNewHighDurationPct", "TRLRatio", "EquityAngle", "RecoveryFactor",
    "AddMarketsProfitFactorMedian", "DrawdownPctOnInitial", "UlcerPerformanceIndex",
    "EdgeRatioInPips", "BestWF", "TSWinLossRatio", "AvgPctDrawdown", "UlcerIndex", "Outlier2",
    "TotalMFE", "MaxNewHighDuration", "ExitQuality", "ExposurePosition",
    "AddMarketsNetProfitMedian", "MaxTSIntradayDrawdown", "EdgeDecayRatio",
    "Parameters", "GiniOOS", "Outlier", "ProbSharpeRatio", "ReturnOpenDDRatio", "EquitySlope",
    "SlopeRatio")}


def keys() -> list[str]:
    """The statistics the snippet asks SQX for, one "name<TAB>type" each.

    Returns:
        Every statistic this project knows SQX's name of: the id-keyed ones `core.sqxstats`
        names without doubt, then the ones stored under their own name. The 34 id-keyed
        slots nobody has named and the two named with a "?" cannot be asked for by name.
    """
    known = [f"{name}\t{slot[0]}" for slot, name in sqxstats.COLUMNS.items() if not name.endswith("?")]
    return known + [f"{name}\t{kind}" for kind, names in NAMED.items() for name in names]


def run(role: str, project: str, banks: list[str], data: str = "main") -> dict[str, int]:
    """Write each databank's `.abk` from the live session's memory, all in one task run.

    Args:
        banks: Databanks of `project`. They need not be synced to disk: the snippet reads memory.
        data: "main" for the main result's orders, "all" for every result's (a cross-market
            or WFM databank read per market).

    Returns:
        Strategies written per databank, each file at `core.paths.bank_dir(project, role) /
        "<databank>.abk"`, opened and validated (`bankfile.load`, CRC checked). Nobody deletes them yet: no
        conversion step exists, and the owner's answer is «borrado al convertir» — whoever
        converts a `.abk` deletes it once converted; the next `run` clears the folder anyway.
        Empty when the install has no tool project
        or its snippets are not compiled (`sqx.snippets.install`): the caller reads the
        databank its next way.
    """
    if not banks or not toolproject.cfx(role).exists() or install.pending(role):
        return {}
    out = bank_dir(project, role)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    (out / "_keys.tsv").write_text("\n".join(keys()) + "\n", encoding="utf-8")
    args = "|".join([project, ";".join(banks), str(out), str(out / "_keys.tsv"), data,
                     ",".join(map(str, SAMPLES))])
    live.call(role, "updateTaskXML", projectName=toolproject.NAME, taskXMLFile=toolproject.MEMBER,
              xmlConfig=toolproject.settings("AlgoBank", args))
    end = live.run(role, toolproject.NAME, toolproject.CONFIG)
    if not (out / "_done.tsv").exists():         # `live.run` already raised on an aborted run
        raise SystemExit(f"{project}: «AlgoBank» no escribió sus databanks: {end}")
    held = live.records(role, project)
    wrote = {}
    for bank in banks:
        got = bankfile.load(out / f"{bank}.abk", check=True)
        wrote[bank] = len(got["names"])
        if len(set(got["stats"]["strategy"].tolist())) != wrote[bank]:      # statistics not computed yet: the snippet skips them
            raise SystemExit(f"{project}/{bank}: hay estrategias sin estadísticas en el .abk (¿una tarea llena el databank?)")
        if wrote[bank] != held[bank]:
            raise SystemExit(f"{project}/{bank}: el .abk lleva {wrote[bank]} estrategias y la "
                             f"memoria de SQX tiene {held[bank]}")
    return wrote
