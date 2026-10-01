"""The three ways data leaves SQX: trades, databank metrics, and bars."""

import re
import shutil
import subprocess
from pathlib import Path

from core import worker
from core.paths import STAGING, VIEWS_REL, WORKER, WORKER_SH, view_file

SAMPLE = {"10": "IS", "20": "OOS", "127": "Full"}
STAGING_PROJECT, STAGING_DATABANK = "Retester", "Results"


def trades(source: Path, out_dir: Path, data: str = "main") -> str:
    """Export every trade of every strategy in a folder or file.

    Args:
        source: A .sqx file, or a folder of them — a folder is exported in one JVM start,
            231 strategies in about four minutes.
        out_dir: Directory the CSVs are written into.
        data: "main" for the strategy's main result only, "all" to add every cross-check
            result. A cross-market retest stores one AdditionalMarket result per market, and
            "all" writes them into the same CSV as contiguous blocks that the Symbol column
            separates; ticket numbering restarts at 1 in each block.

    Returns:
        The command's output. Read-only: it needs no build and touches no project state.
    """
    worker.require_posix()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["-tools", "action=orderstocsv", f"file={source}", f"output={out_dir}", f"data={data}"]
    got = subprocess.run([str(WORKER_SH), "run", *cmd], capture_output=True, text=True)
    if got.returncode:
        # SQX says why on stdout («No plugin loader was able to recognize file …»); a bare
        # CalledProcessError swallowed it and every failed export read the same.
        said = [line for line in (got.stdout + got.stderr).splitlines()
                if "rror" in line or "xception" in line][-5:]
        raise RuntimeError(f"orderstocsv salió con {got.returncode} sobre {source}: "
                           + (" | ".join(said) or (got.stderr or got.stdout).strip()[-800:]))
    return got.stdout


def symbols() -> str:
    """Everything SQX holds data for, as it lists it.

    Returns:
        The raw CSV `-symbol action=list` prints: feed name, base symbol, resolution,
        timezone, first and last date, days and bar count, then source and category. The
        bar count is what tells a sync whether a feed has grown since it was last pulled.
    """
    worker.require_posix()
    return subprocess.run([str(WORKER_SH), "run", "-symbol", "action=list"],
                          capture_output=True, text=True, check=True).stdout


def bars(symbol: str, timeframe: str, out_dir: Path, date_from: str, date_to: str) -> Path:
    """Export OHLC bars for one symbol and timeframe.

    Args:
        symbol: SQX symbol WITHOUT the timeframe suffix, e.g. "XAUUSD_M1".
            Passing the suffixed name fails with "Symbol ... not found."
        timeframe: SQX timeframe code, e.g. "M30".
        out_dir: Directory the CSV is written into.
        date_from, date_to: Window as YYYY.MM.DD.

    Returns:
        Path of the renamed CSV. SQX writes "<symbol>-<TF>-No Session.csv"; run one
        timeframe per invocation, because a second export in the same JVM overwrites it.
    """
    worker.require_posix()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["-data", "action=export", f"symbols={symbol}", f"timeframe={timeframe}",
           f"datefrom={date_from}", f"dateto={date_to}",
           "format=Custom", "cIncludeHeader=true",
           "cHeader=Date,Time,Open,High,Low,Close,Volume",
           "cFormat=[Date:yyyy.MM.dd],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume]",
           f"outputdir={out_dir}"]
    subprocess.run([str(WORKER_SH), "run", *cmd], check=True)
    written = out_dir / f"{symbol}-{timeframe}-No Session.csv"
    target = out_dir / f"bars_{timeframe}.csv"
    written.rename(target)
    return target


def prepare_view(view: str) -> str:
    """Copy a master databank view to the worker, tagging each column by period.

    Args:
        view: The view's name on the master, e.g. "Export Data View".

    Returns:
        The name the copy was written under on the worker.

    Spaces are stripped because the HTTP API splits its command on whitespace, and each
    column name gains an (IS)/(OOS)/(Full) suffix from its sampleType so the exported
    headers are unique.
    """
    xml = view_file(view).read_text(encoding="utf-8")
    xml = re.sub(r'name="([^"]+)" sampleType="(\d+)"',
                 lambda m: f'name="{m.group(1)} ({SAMPLE[m.group(2)]})" '
                           f'sampleType="{m.group(2)}"', xml)
    name = view.replace(" ", "")
    xml = re.sub(r'<View name="[^"]*" originalName="[^"]*"',
                 f'<View name="{name}" originalName="{name}"', xml)
    (WORKER / VIEWS_REL / f"{name}.vw").write_text(xml, encoding="utf-8")
    return name


def stage(source: Path) -> int:
    """Copy a folder of strategies into the worker's staging databank.

    Args:
        source: Folder holding the .sqx — a databank on any install, or a copy of one
            already staged elsewhere, which is what lets one harvest serve two exports.

    Returns:
        How many .sqx were staged.

    Must run with the worker stopped, or its next sync fights the copy. Clears the
    staging databank first so a previous run cannot leak in.
    """
    STAGING.mkdir(parents=True, exist_ok=True)
    for old in STAGING.glob("*.sqx"):
        old.unlink()
    found = sorted(source.glob("*.sqx"))
    for f in found:
        shutil.copy(f, STAGING / f.name)
    return len(found)


def metrics(source: Path, view: str, out: Path) -> int:
    """Export one databank's performance metrics, one row per strategy.

    Args:
        source: Folder holding the databank's .sqx, on whichever install holds it.
        view: Databank view to export through, defining the columns and their sample types.
        out: CSV file to write.

    Returns:
        How many strategies the worker saw. The whole staging dance exists because
        -databank action=export only works on the instance holding the project, and the
        master's CLI is unavailable while its GUI is up.
    """
    worker.require_posix()
    out.parent.mkdir(parents=True, exist_ok=True)
    prepared = prepare_view(view)
    stage(source)
    worker.start()
    seen = worker.wait_ready(STAGING_PROJECT, STAGING_DATABANK)
    worker.call(f"-databank action=export project={STAGING_PROJECT} "
                f"name={STAGING_DATABANK} file={out} view={prepared}")
    worker.stop(export=False)
    return seen
