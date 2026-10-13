#!/usr/bin/env python3
"""Step 14's T1 batch: every mother and her drawn neighbours as `.sqx`, and their retest on the two legs."""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import fanout, worker
from core.paths import worker_dir
from sqx.variants import execute, inputs, legs as legmod, livexec, manifest, neighbours, tuples
from sqx.variants.build import fabricate, rewrite

MOTHER, NEIGHBOUR = "mother", "neighbour"
RAN = "ran.json"
_SHARED: dict = {}    # what write() hands its forked children: members, rows, folder, shape


def plan(mothers: list[Path], cfg: dict) -> pd.DataFrame:
    """Every file to write: per mother herself (neighbour 0) and her drawn neighbours.

    Args:
        mothers: The mothers' `.sqx`; the stem is the strategy's name.
        cfg: The `neighbours` block of config.yaml.

    Returns:
        One row per file with the columns contract C2 carries — `variant_id` (`M003N0042`:
        mother 3, neighbour 42), `stratum`, `origin` (the mother's own row), the canary columns
        empty, `tuple_hash` and one `param_` column per moved parameter of any mother (NaN
        where the mother has none by that name) — plus `strategy`, `mother` (her file),
        `neighbour` and `duplicates`, the draws her rounding collapsed and dropped.

    Raises:
        SystemExit: A mother with no neighbour at all — nothing of hers moves, or every draw
            rounded back onto her.
    """
    rows = []
    for m, path in enumerate(mothers):
        with zipfile.ZipFile(path) as archive:
            portfolio = archive.read(rewrite.PORTFOLIO).decode("utf-8")
        drawn, dropped = neighbours.draw(portfolio, path.stem, cfg)
        if not drawn:
            raise SystemExit(f"{path.stem}: ninguna vecina distinta de la madre "
                             f"({len(neighbours.classes(portfolio, cfg))} parámetros que mover)")
        for k, values in enumerate([neighbours.mother(portfolio, cfg), *drawn]):
            rows.append({"variant_id": f"M{m:03d}N{k:04d}", "strategy": path.stem,
                         "mother": str(path), "neighbour": k, "duplicates": dropped,
                         "stratum": NEIGHBOUR if k else MOTHER, "origin": k == 0,
                         "canary_expect_netprofit": None, "canary_expect_trades": None,
                         "canary_expect_same_as": None,
                         "tuple_hash": tuples.tuple_hash(values), **tuples.columns(values)})
    return pd.DataFrame(rows)


def write(rows: pd.DataFrame, folder: Path, shape: str) -> None:
    """Write every planned file: the mother untouched but renamed, each neighbour with its tuple.

    Args:
        rows: Output of `plan`.
        folder: Where the `.sqx` go; emptied first, because the manifest adopts whatever
            is on disk.
        shape: A key of `rewrite.SHAPES`.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.sqx"):
        stale.unlink()
    groups = {path: own.to_dict("records") for path, own in rows.groupby("mother", sort=False)}
    _SHARED.update(source={path: rewrite.members(Path(path)) for path in groups}, rows=groups,
                   folder=folder, shape=shape)
    # Every file is independent and the time is zlib's: blocks of rows on every core, as
    # `fabricate.batch` does for the factory's variants.
    blocks = {(path, i): fabricate.BLOCK for path, own in groups.items()
              for i in range(0, len(own), fabricate.BLOCK)}
    list(fanout.run(_block, blocks, fanout.CORES))


def _block(task: tuple[str, int]) -> int:
    """Write one block of one mother's rows, in a worker that inherited the parent's members."""
    path, start = task
    got = _SHARED
    for row in got["rows"][path][start:start + fabricate.BLOCK]:
        # The mother's row writes nothing: `%g` would shorten a value of hers with more
        # than six significant digits, and neighbour 0 must be her to the byte.
        wanted = {} if row["origin"] else {name: value for name, value
                                           in tuples.from_columns(row).items()
                                           if value == value}     # NaN: another mother's
        parts = rewrite.variant(got["source"][path], row["variant_id"],
                                fabricate.name_of(row["strategy"], row["variant_id"]), wanted)
        rewrite.save(got["folder"] / f"{row['variant_id']}.sqx", parts, got["shape"])
    return 0


def make(mothers: Path, out: Path) -> pd.DataFrame:
    """Fabricate the batch and its manifest, and refuse one whose files are not the plan.

    Args:
        mothers: Folder of the mothers' `.sqx`.
        out: The batch directory under the data root; holds `sqx/` and `manifest.parquet`.

    Returns:
        The plan. The manifest is contract C2 read back off the disk, with the plan's own
        `strategy`, `mother`, `neighbour` and `duplicates` joined on.
    """
    cfg = inputs.load()["neighbours"]
    rows = plan(sorted(mothers.glob("*.sqx")), cfg)
    write(rows, out / "sqx", cfg["shape"])
    names = [c[len(tuples.PREFIX):] for c in rows.columns if c.startswith(tuples.PREFIX)]
    frame, report = manifest.write(rows, out / "sqx", names)
    frame.merge(rows[["variant_id", "strategy", "mother", "neighbour", "duplicates"]],
                on="variant_id").to_parquet(out / manifest.FILE, compression="zstd", index=False)
    if report["missing"] or report["unexpected"] or report["tuple_mismatch"]:
        raise SystemExit(f"el lote no es el plan: {report}")
    return rows


def retest(work: Path, project: str) -> dict:
    """Load the batch into the project and retest it on the legs `neighbours.legs` names.

    `execute`'s own `awake`/`load`/`run`/`synced` (or `livexec`'s, on this holder's live
    session), as the pilot uses them; only the legs differ. `load` empties the input and all
    three legs' databanks, the one not run included.

    Args:
        work: The batch directory: holds `sqx/`.
        project: The mother's own workflow project (hard rule 10).

    Returns:
        What `ran.json` records: `n_loaded`, `n_returned` and per leg its segment, title,
        databank, folder and files on disk.

    Raises:
        SystemExit: A stock project; or, on the restart route, a project whose active tasks
            are not exactly these legs — `action=start` runs every active task.
    """
    settings = inputs.load()
    if project in execute.STOCK:
        raise SystemExit(f"{project} es un proyecto de serie: regla dura 10")
    cfg = dict(settings["execute"], project=project)
    used = [leg for leg in legmod.legs() if leg["title"] in settings["neighbours"]["legs"]]
    cfg["only"] = [leg["title"] for leg in used]
    folder = work / "sqx"
    n = len(list(folder.glob("*.sqx")))
    be = livexec.backend(cfg)
    cfx = worker_dir(cfg["role"]) / "user/projects" / project / "project.cfx"
    with zipfile.ZipFile(cfx) as z:
        on = re.findall(r'active="true"[^>]*title="([^"]*)"', z.read("config.xml").decode())
    if be is not livexec and sorted(on) != sorted(cfg["only"]):
        raise SystemExit(f"{project} tiene activas {on} y este lote corre {cfg['only']}: "
                         "`action=start` las correría todas (sqx.projects.stage.just)")

    def say(pct: int, line: str) -> None:
        """Fold the retest's own percentage into the stage's, after the load."""
        print(f"PROGRESS {5 + pct * 90 // 100} {line}", flush=True)

    print(f"PROGRESS 2 despertando el {cfg['role']}", flush=True)
    ours = be.awake(cfg)
    # One job, then the install goes back down, but only if this run is what woke it (hard rule 1).
    try:
        print(f"PROGRESS 5 cargando {n} vecinas en {project}/{legmod.source()}", flush=True)
        be.load(folder, cfg)
        done = be.run(n * len(used), cfg, say) // len(used)
        harvest = []
        for leg in used:
            bank, on_disk = be.synced(done, cfg, leg["databank"])
            harvest.append(leg | {"databank_dir": str(bank), "n_on_disk": on_disk})
    finally:
        if ours:
            worker.stop(cfg["role"], export=False)   # only WFC databanks, as `execute`
    ran = {"n_loaded": n, "n_returned": done, "legs": harvest}
    (work / RAN).write_text(json.dumps(ran, indent=2, default=str), encoding="utf-8")
    return ran


def main() -> None:
    """Fabricate the batch (`--mothers`, `--out`) or retest one already made (`--work`, `--project`)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mothers", type=Path, help="folder of the mothers' .sqx: fabricate")
    ap.add_argument("--out", type=Path, help="the batch directory to fabricate into")
    ap.add_argument("--work", type=Path, help="a batch directory already fabricated: retest it")
    ap.add_argument("--project", help="the custom project holding the WFC legs")
    a = ap.parse_args()

    if a.work:
        ran = retest(a.work, a.project)
        print(f"PROGRESS 100 {ran['n_returned']} vecinas, "
              + ", ".join(f"{leg['segment']}: {leg['n_on_disk']} en disco" for leg in ran["legs"]),
              flush=True)
        return
    rows = make(a.mothers, a.out)
    per = rows.groupby("strategy").agg(vecinas=("origin", lambda o: int((~o).sum())),
                                       duplicadas=("duplicates", "first"))
    print(f"{len(per)} madre(s) -> {len(rows)} ficheros en {a.out / 'sqx'}")
    print(per.to_string())


if __name__ == "__main__":
    main()
