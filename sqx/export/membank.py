"""Whole databanks written from a live session's memory by the AlgoBank snippet, one `.abk` each."""

from core import bankfile, bankframes, sqxfile, sqxstats
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


def run(role: str, project: str, banks: dict[str, str]) -> dict[str, int]:
    """Write each databank's `.abk` from the live session's memory, one task run per data mode.

    Args:
        banks: Databank -> data mode, of `project`. They need not be synced to disk: the snippet
            reads memory. "main" is the main result's orders, "all" every result's (a
            cross-market or WFM databank read per market).

    Returns:
        Strategies written per databank, each file at `core.paths.bank_dir(project, role) /
        "<databank>.abk"`, opened and validated (`bankfile.load`, CRC checked). Only the named
        banks' files are replaced; `take` deletes each one it reads. Empty when the install has no tool project or its snippets are not compiled
        (`sqx.snippets.install`): the caller reads the databank its next way.
    """
    if not banks or not toolproject.cfx(role).exists() or install.pending(role):
        return {}
    out = bank_dir(project, role)
    out.mkdir(parents=True, exist_ok=True)
    for bank in banks:
        (out / f"{bank}.abk").unlink(missing_ok=True)
    (out / "_keys.tsv").write_text("\n".join(keys()) + "\n", encoding="utf-8")
    for data in dict.fromkeys(banks.values()):
        names = [b for b, d in banks.items() if d == data]
        (out / "_done.tsv").unlink(missing_ok=True)
        args = "|".join([project, ";".join(names), str(out), str(out / "_keys.tsv"), data,
                         ",".join(map(str, SAMPLES))])
        live.call(role, "updateTaskXML", projectName=toolproject.NAME, taskXMLFile=toolproject.MEMBER,
                  xmlConfig=toolproject.settings("AlgoBank", args))
        end = live.run(role, toolproject.NAME, toolproject.CONFIG)
        if not (out / "_done.tsv").exists():         # `live.run` already raised on an aborted run
            raise SystemExit(f"{project}: «AlgoBank» no escribió sus databanks: {end}")
    held = live.records(role, project)
    if missing := [b for b in banks if b not in held]:
        raise SystemExit(f"{project}: SQX no tiene {missing} cargado(s); tiene {sorted(held)}")
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


def take(project: str, role: str, bank: str, ids: dict[str, str], data: str) -> dict | None:
    """The databank's `.abk` loaded, when it is this databank's and whole; the file is consumed.

    Args:
        ids: File stem -> identity (`core.sqxfile._hashed` of the strategy's XML) of every
            strategy the databank holds on disk, exactly.
        data: The data mode the caller needs, "main" or "all".

    Returns:
        The loaded bank, or None (one line saying why, none when there is no file) so the caller
        reads the databank its next way. Names, mode and identities say «same strategies», never
        «same backtest»: the caller binds the trades to the .sqx's own result with
        `core.bankframes.unbound`. The file is deleted once loaded, whatever the answer: an `.abk`
        serves one read.
    """
    path = bank_dir(project, role) / f"{bank}.abk"
    if not path.exists():
        return None
    try:
        got = bankfile.load(path, check=True)
        path.unlink(missing_ok=True)         # the memory map stays valid
        why = (f"modo {got['data']}, se pide {data}" if got["data"] != data
               else f"nombres distintos ({len(set(got['names']) ^ set(ids))} de diferencia)"
               if set(got["names"]) != set(ids)
               else "una identidad no coincide" if any(
                   sqxfile._hashed(t) != ids[n] for n, t in bankframes.texts(got).items()) else "")
    except (OSError, bankfile.Unreadable) as err:
        got, why = None, str(err)
    if why:
        print(f"{project}/{bank}: {path.name} no vale: {why}")
        return None
    return got
