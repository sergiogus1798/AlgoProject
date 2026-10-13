#!/usr/bin/env python3
"""Export one databank's trades into the data root, as one typed Parquet per export."""

import argparse
import glob
import random
import shutil
import time
from datetime import date
from pathlib import Path

from core import phases
from core import bankfile, bankframes, exportdrv, fanout, identities, manifest, sqxfile, sqxstats, sqxview, tradepack
from core.paths import MASTER, bank_dir, databank_dir, export_dir, project_dir, worker_dir
from sqx.export import membank


SAMPLE_SEED = 20260914   # a subset export is a sample, and a sample has to be reproducible
_LINEAGE: tuple = ()     # (project, databank, install) lineage() hands its forked children


def stage(project: str, databank: str, dest: Path, limit: int = 0,
          install: Path = MASTER, prefix: str = "") -> dict[str, str]:
    """Copy a databank's strategies aside and read each one's timeframe.

    Args:
        project: Project name.
        databank: Databank name.
        dest: Directory to copy the .sqx files into.
        limit: Stage a random sample of this many instead of all of them; 0 means all.
            Random rather than the first N, because a databank is written in build order
            and its first strategies come from one generation run.
        install: Which install holds the project. Defaults to the master, which is where
            it lived before builds moved to the headless workers — a project built on the
            custodian is invisible from here without this.
        prefix: Put before each copy's file name, so several databanks can share one
            folder and one export.

    Returns:
        Strategy name to timeframe, e.g. {"Strategy 1.2.3": "M30"}. Copies rather than
        exporting in place so SQX never opens the live files.
    """
    dest.mkdir(parents=True, exist_ok=True)
    found = sorted(databank_dir(project, databank, install).glob("*.sqx"))
    if limit and limit < len(found):
        found = sorted(random.Random(SAMPLE_SEED).sample(found, limit))
    timeframes = {}
    for f in found:
        shutil.copy(f, dest / f"{prefix}{f.name}")
        timeframes[f.stem] = sqxfile.symbol(f)[1].rsplit("_", 1)[-1]
    return timeframes


def sign(staged: Path, out: Path, prefix: str = "") -> int:
    """Write `out/identity.csv` (strategy, identity) from the staged .sqx before they go.

    Args:
        staged: The staged copies, named after their strategies.
        out: The export directory.
        prefix: Only the copies carrying it, named without it (export_retest stages
            several databanks in one folder as `<i>__<name>.sqx`).

    Returns:
        Rows written. A few KB in place of the files, which weigh six times the Parquet;
        `core.study.identity.from_export` reads it once no install holds the databank.
    """
    found = sorted(staged.glob(f"{prefix}*.sqx"))
    known = identities.many(found, fanout.CORES)
    (out / "identity.csv").write_text(
        "strategy,identity\n" + "".join(f"{f.stem[len(prefix):]},{known[f]}\n" for f in found),
        encoding="utf-8")
    return len(found)


def lineage(project: str, databank: str, install: Path, staged: Path, out: Path) -> int:
    """Write `out/lineage.csv` (strategy, identity, mother): whose each exported strategy is.

    A task that rewrites the strategy (the WFM optimises its parameters) gives it another
    identity, and a name alone does not say whose it is: names are reused from one build of
    a project to the next. This is read while the project still holds both ends: `mother` is
    the one identity the files of that name carry in the project's other databanks, the
    strategy's own when none differs, and EMPTY when two differ (a databank left over from
    another build) — an empty mother is never paired (`core.store.extra.named`).

    Args:
        project: Project name.
        databank: The databank being exported.
        install: The install holding the project.
        staged: The staged copies, named after their strategies.
        out: The export directory.

    Returns:
        Rows left without a mother.
    """
    global _LINEAGE
    _LINEAGE = (project, databank, install)
    found = sorted(staged.glob("*.sqx"))
    got = dict(fanout.run(_mother, {f: 1 for f in found}, fanout.CORES))
    rows = [f"{f.stem},{got[f][0]},{got[f][1]}\n" for f in found]
    orphans = sum(not got[f][1] for f in found)
    (out / "lineage.csv").write_text("strategy,identity,mother\n" + "".join(rows), encoding="utf-8")
    return orphans


def _mother(f: Path) -> tuple[str, str]:
    """(identity, mother) of one staged copy, read in a fanout child off `_LINEAGE`."""
    project, databank, install = _LINEAGE
    own = sqxfile.identity(f)
    others = {sqxfile.identity(o)
              for o in project_dir(project, install).glob(f"databanks/*/{glob.escape(f.name)}")
              if o.parent.name != databank} - {own}
    return own, own if not others else others.pop() if len(others) == 1 else ""


def held(a: argparse.Namespace, staged: Path) -> dict | None:
    """The databank's `.abk` from a live session, when it is this databank's and its trades are the .sqx's own result.

    Only trades come from it (identity, metrics, equity stay read off the .sqx); None when there is
    none or it does not bind, and the caller reads the databank with orderstocsv.
    """
    if not (a.role and (bank_dir(a.project, a.role) / f"{a.databank}.abk").exists()):
        return None
    files = sorted(staged.glob("*.sqx"))
    ids = {f.stem: v for f, v in identities.many(files, fanout.CORES).items()}
    if not (bank := membank.take(a.project, a.role, a.databank, ids, "main")):
        return None
    stats = {f.stem: s for f, s in fanout.run(sqxstats.stats, {f: 1 for f in files}, fanout.CORES)}
    try:
        why = bankframes.unbound(bank, stats, sqxview.measured(stats))
    except SystemExit as err:       # both sample blocks filled: no single result to bind to
        why = str(err)
    if why:
        print(f"{a.project}/{a.databank}: .abk no vale: {why}")
        phases.note("fallback", f"{a.project}/{a.databank}: {why}")
    return None if why else bank


def main() -> None:
    """Stage a databank, export every trade of it, and pack them into one Parquet."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    # --symbol is load-bearing, not decoration: the packed trades drop the constant Symbol
    # column, so the manifest is the only record of which feed the backtest ran on.
    ap.add_argument("--symbol", required=True, help="SQX symbol without the timeframe suffix")
    ap.add_argument("--role", help="headless install holding the project, e.g. custodian; "
                                   "the master if absent")
    a, began = ap.parse_args(), time.time()
    install = worker_dir(a.role) if a.role else MASTER
    if not any(databank_dir(a.project, a.databank, install).glob("*.sqx")):   # before any write
        raise SystemExit(f"{a.project}/{a.databank}: ningún .sqx en disco, no hay operaciones que exportar")

    out = export_dir(a.project, a.databank, date.today().isoformat())
    # Both are this command's intermediates. A run that failed half-way leaves them, and a
    # second export the same day then handed SQX a folder with a stray file: «No plugin
    # loader was able to recognize file …/strategies/manifest.json» (📓 2026-09-29). Its
    # own names: `strategies/` is `export_spp`'s product in the same day folder (the mothers
    # the variant factory opens), and this command used to delete it (📓 2026-09-30).
    staged, csvs = out / "_trades_sqx", out / "_trades_csv"
    for scratch in (staged, csvs):
        shutil.rmtree(scratch, ignore_errors=True)
    timeframes = stage(a.project, a.databank, staged, install=install)
    (out / "timeframes.csv").write_text(
        "strategy,timeframe\n" + "".join(f"{k},{v}\n" for k, v in timeframes.items()))
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    bank = held(a, staged)
    if bank:
        packed = bankfile.pack(bank, out / "trades.parquet", per_market=False)
    else:
        exportdrv.trades(staged, csvs)
        # The CSVs are an intermediate, not the export: nine tenths of their bytes are quoting,
        # repeated text and four columns that are derivable back. Bars are not copied here at
        # all — they live once in the M1 library, which covers more history than this window did.
        packed = tradepack.pack(sorted(csvs.glob("*.csv")), out / "trades.parquet", per_market=False)
        shutil.rmtree(csvs)
    # The staged .sqx are copies of what the databank holds; the manifest names the
    # databank, and 757 of them weighed 119 MB beside a 20 MB Parquet. Their identities
    # stay, in identity.csv.
    sign(staged, out)
    orphans = lineage(a.project, a.databank, install, staged, out)
    if orphans:
        print(f"lineage: {orphans} strategies carry two other identities in this project")
    shutil.rmtree(staged)

    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "symbol": a.symbol},
                   f"export_trades.py --project {a.project} --databank {a.databank} "
                   f"--symbol {a.symbol}",
                   {**packed, "timeframes": sorted(set(timeframes.values()))}, since=began)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
