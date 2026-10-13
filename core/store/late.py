"""What steps 13 to 20 leave outside the report folders: the rest of each export, and the variant batch."""

import shutil
from datetime import date
from pathlib import Path

from core import sqxfile
from core.datapaths import variants_dir
from core.paths import DATA
from core.store import extra

PAGES = (".html", ".md", ".pdf")     # drawn from the numbers beside them: never stored
TABLES = (".parquet", ".csv")
REBUILT = ("sqx", "pilot", "origin")  # a variant batch's .sqx: the plan and the mother make them again


def mothers(project: str) -> dict[str, str]:
    """Identity a task gave a strategy -> the identity it is stored under.

    Read off every export's `lineage.csv` (`sqx.export.export_trades.lineage`, written while
    the project held both files). A row without a mother pairs nothing; an identity two
    exports give two mothers is dropped too.
    """
    out, clash = {}, set()
    for path in sorted((DATA / "raw" / project).glob("*/*/lineage.csv")):
        said = extra.table(path).dropna(subset=["mother"])
        for own, mother in zip(said["identity"], said["mother"]):
            if out.setdefault(own, mother) != mother:
                clash.add(own)
    return {k: v for k, v in out.items() if k not in clash and k != v}


def aliases(project: str, identity: str, mother: dict[str, str] | None = None) -> frozenset[str]:
    """The identity SQX gave the same strategy later, when the two name each other mother.

    Only a mutual pair counts: a variant has a mother that does not point back, and is another
    strategy (`verdicts` reads the same pairs the same way). `mother`: what `mothers` returned,
    when the caller already has it (a save asks once per survivor, and `mothers` walks every lineage.csv).
    """
    mother = mothers(project) if mother is None else mother
    other = mother.get(identity)
    return frozenset({other} if other and mother.get(other) == identity else ())


def names(project: str, databank: str, day: str, identity: str) -> set[str]:
    """The names a stored strategy goes by in one databank on one day; empty when nobody vouches.

    Args:
        project: SQX project name.
        databank: The databank's folder name under `raw/` and `reports/`.
        day: The export's or report's day folder.
        identity: The stored strategy.

    Returns:
        Names from that export's `identity.csv` (the file has this identity), its `lineage.csv`
        (this identity is its mother) and any report's `verdict.csv` of that day carrying the
        identity (the MC ingest writes none of the first two and drops the `Strategy ` prefix).
        A name alone is never enough: names are reused from one build to the next.
    """
    out: set[str] = set()
    for file, col in (("identity.csv", "identity"), ("lineage.csv", "mother")):
        path = DATA / "raw" / project / databank / day / file
        if path.exists():
            said = extra.table(path)
            out |= set(said.loc[said[col] == identity, "strategy"].astype(str))
    for path in sorted((DATA / "reports" / project / databank / day).glob("*/verdict.csv")):
        said = extra.table(path)
        if {"strategy", "identity"} <= set(said.columns):
            out |= set(said.loc[said["identity"] == identity, "strategy"].astype(str))
    return out


def cut(path: Path, known: set[str], out: Path) -> int:
    """Write the rows of one table that name any of `known` (or its sisters) under `out`."""
    frame = extra.table(path)
    rows = frame[frame.index.isin([i for n in known for i in extra.family(frame, n).index])]
    if len(rows):
        out.mkdir(parents=True, exist_ok=True)
        (rows.to_parquet if path.suffix == ".parquet" else rows.to_csv)(out / path.name, index=False)
    return len(rows)


def exports(project: str, identity: str, tmp: Path) -> list[tuple[str, Path, dict]]:
    """The tables an export keeps in sub-folders: the MC simulations, the SPP runs, the WFM cells.

    Args:
        project: SQX project name.
        identity: The stored strategy.
        tmp: A scratch folder.

    Returns:
        One entry per databank and day that vouches for the strategy (`names`): every table
        below the export's own folder cut to its rows, at the same relative path (a hive
        partition such as `sims/task=bar/` stays in the path), with the export's manifests.
        The top-level `trades.parquet` is `extra.trades`'; `.sqx` copies are not kept.
    """
    found = []
    for folder in sorted(p for p in (DATA / "raw" / project).glob("[!_]*/*") if p.is_dir()):
        databank, day = folder.parts[-2:]
        known = names(project, databank, day, identity)
        out, n = tmp / databank / day, 0
        for path in sorted(p for p in folder.rglob("*") if known and p.parent != folder):
            rel = path.relative_to(folder)
            if any(part.startswith("_") or part == "strategies" for part in rel.parts):
                continue
            if path.suffix in TABLES:
                n += cut(path, known, out / rel.parent)
            elif path.name == "manifest.json" and (out / rel.parent).exists():
                shutil.copyfile(path, out / rel)
        if n:
            found.append((f"exportacion.{databank}.{day}", out,
                          {"study": "exportacion", "databank": databank, "day": day, "rows": n}))
    return found


def variants(project: str, name: str, identity: str, tmp: Path) -> list[tuple[str, Path, dict]]:
    """Step 16.5's batch of a mother and the studies read on it (cloud, 17, 18, 18.5).

    Args:
        project: SQX project name.
        name: The mother's name: the batch's folder is named after it.
        identity: Its identity; the batch's own copy of the mother (`origin/build.sqx`) must
            carry it, or the batch is another strategy's under the same name and is left out.
        tmp: A scratch folder.

    Returns:
        `variantes.<day>` — the design, the plan, every variant's metrics, equity and trades in
        each segment and market — and `optimizacion.<day>` — `estudios/` with its
        distributions. Pages and the variants' `.sqx` are left out (REBUILT).
    """
    folder = variants_dir(project, name)
    origin = folder / "origin" / "build.sqx"
    if not origin.exists() or sqxfile.identity(origin) != identity:
        return []
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix not in PAGES
             and p.relative_to(folder).parts[0] not in REBUILT]
    day = date.fromtimestamp(max(p.stat().st_mtime for p in files)).isoformat()
    found = []
    for stem, study in (("variantes", False), ("optimizacion", True)):
        out = tmp / stem
        for path in files:
            rel = path.relative_to(folder)
            if (rel.parts[0] == "estudios") == study:
                (out / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, out / rel)
        if out.exists():
            found.append((f"{stem}.{day}", out, {"study": stem, "day": day, "batch": folder.name}))
    return found


def leftovers(folder: Path, frozen: Path, pop: Path) -> bool:
    """Copy into `pop` the files of a report folder that `collect.freeze` did not take.

    `freeze` knows a study's tables, its JSON and its per-strategy pages; a study may write
    more beside them (the monkey's `rungs.json`, the SPP's design briefs), the same for every
    strategy of the run. Returns whether anything was copied.
    """
    took = False
    for path in sorted(p for p in folder.iterdir() if p.is_file() and p.suffix not in PAGES):
        if not (frozen / path.name).exists() and not (pop / path.name).exists():
            pop.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, pop / path.name)
            took = True
    return took


def unpaired(project: str, identity: str, frozen: set[str], cannot: set[str],
             tmp: Path) -> list[tuple[str, Path, dict]]:
    """The report folders `collect.freeze` did not pair with the strategy by its identity.

    Args:
        project: SQX project name.
        identity: The stored strategy.
        frozen: `<databank>/<day>/<study>` of the folders `freeze` did take.
        cannot: Those it said cannot name anybody (no row per strategy, or no identity).
        tmp: A scratch folder.

    Returns:
        Per folder where the strategy is vouched for (`names`: the WFM's reports carry the
        identity the WFM gave it), its own entry — its rows of every table and its page of
        `estrategias/` — and a `.poblacion` one with every other table and JSON, whole (the
        same bytes for every strategy of the run: the pool keeps them once). A folder in
        `cannot` goes whole to the population. Any other is another strategy's and is left.
    """
    found = []
    for folder in sorted(p for p in (DATA / "reports" / project).glob("*/*/*") if p.is_dir()):
        databank, day, study = folder.parts[-3:]
        rel = f"{databank}/{day}/{study}"
        known = names(project, databank, day, identity)
        if rel in frozen or not (known or rel in cannot):
            continue
        own, pop = tmp / rel / "own", tmp / rel / "pop"
        for path in sorted(p for p in folder.iterdir() if p.suffix in TABLES and known):
            if cut(path, known, own) == len(extra.table(path)):   # nobody else's rows: not a cut
                (own / path.name).unlink(missing_ok=True)   # a header-only table cut nothing
        for page in (folder / "estrategias" / f"{n}.json" for n in sorted(known)):
            if page.exists():
                (own / "estrategias").mkdir(parents=True, exist_ok=True)
                shutil.copyfile(page, own / "estrategias" / page.name)
        about = {"study": study, "databank": databank, "day": day}
        if own.exists() and any(own.iterdir()):
            found.append((f"{study}.{databank}.{day}", own, about))
        if leftovers(folder, own, pop):
            found.append((f"{study}.{databank}.{day}.poblacion", pop, about | {"population": True}))
    return found
