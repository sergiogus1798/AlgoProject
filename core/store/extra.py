"""What the report folders do not hand a stored strategy: its trades everywhere, its scaled sisters, and which files are the population's."""

import json
import shutil
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import pandas as pd

from core import sqxfile
from core.paths import DATA

FABRICATED = "fabricated_identity"   # scaling.parquet: the identity of the sister's file as written
KEYS = ("strategy", "mother", "name", "sibling", "Strategy Name")   # the columns a table names a strategy by


@lru_cache(maxsize=None)
def table(path: Path) -> pd.DataFrame:
    """A .csv or .parquet, read once per save: a project's tables are cut 41 times over."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, sep=";" if path.name == "metrics.csv" else ",")   # SQX's own export


def _mask(col: pd.Series, test: Callable[[pd.Series], pd.Series]) -> pd.Series:
    """`test` over the text of a column. A categorical is tested once per category, then read by
    code: its `astype(str)` spells out every row, 0.49 s a million (4-5 s a survivor at 9.7 M)."""
    if not isinstance(col.dtype, pd.CategoricalDtype):
        return test(col.astype(str))
    cats = pd.Series([*col.cat.categories.astype(str), "nan"])      # code -1 is a NaN, "nan" as text
    return pd.Series(test(cats).to_numpy()[col.cat.codes.to_numpy()], index=col.index)


def family(frame: pd.DataFrame, name: str, identity: str = "") -> pd.DataFrame:
    """The rows about one strategy or its scaled sisters.

    Args:
        frame: Any table.
        name: The strategy's name in its project; step 12 names a sister `<name>_Scaled<TF>`.
        identity: Its identity, for the tables that carry it (as a column or as the index).

    Returns:
        The rows whose KEYS column is the name or a sister's, or whose identity is this one.
    """
    hit = pd.Series(False, index=frame.index)
    if identity:            # never the empty one: rows that carry no identity are nobody's by it
        hit |= frame.index == identity
        if "identity" in frame:
            hit |= _mask(frame["identity"], lambda said: said.eq(identity))
    for col in KEYS:
        if col in frame:
            hit |= _mask(frame[col], lambda said: said.eq(name) | said.str.startswith(f"{name}_Scaled"))
    return frame[hit]


def population(folder: Path, identity: str, names: list[str], out: Path) -> bool:
    """Move out of a frozen study folder the files that are the same for every strategy.

    Args:
        folder: One study's folder as `core.archive.collect.freeze` left it.
        identity: The strategy.
        names: Its names in that study.
        out: Where the population's files go.

    Returns:
        Whether anything moved: a JSON that is not one strategy's result, and a table with
        rows about somebody else (a funnel, the list of the rejected).
    """
    moved = False
    for path in sorted(p for p in folder.iterdir() if p.is_file()):
        if path.suffix == ".json":
            shared = json.loads(path.read_text(encoding="utf-8")).get("strategy") not in names
        else:
            frame = table(path)
            shared = any(len(family(frame, n, identity)) < len(frame) for n in names)
        if shared:
            out.mkdir(parents=True, exist_ok=True)
            path.rename(out / path.name)
            moved = True
    return moved


def _cut(path: Path, name: str, out: Path, sisters_only: bool = False) -> int:
    """Write the family's rows of one table under `out`; how many there were. `sisters_only`
    leaves out the rows filed under the strategy's own name: its study's zip already has them."""
    rows = family(table(path), name)
    if sisters_only and "strategy" in rows:
        rows = rows[rows["strategy"].astype(str) != name]
    if len(rows):
        out.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".parquet":
            rows.to_parquet(out / path.name, index=False)
        else:
            rows.to_csv(out / path.name, index=False)
    return len(rows)


def named(folder: Path, name: str, identity: str) -> bool:
    """Whether a raw export's `identity.csv` says this name is this strategy there.

    A name is reused from one build of a project to the next (529 names of one project carry
    two identities): trades are filed by name, so the export must vouch for whose they are —
    its `identity.csv`, or its `lineage.csv` naming this identity as the mother.
    """
    for file, col in (("identity.csv", "identity"), ("lineage.csv", "mother")):
        if (folder / file).exists():       # lineage: a task gave it another identity (the WFM)
            said = table(folder / file)
            if ((said["strategy"].astype(str) == name) & (said[col] == identity)).any():
                return True
    return False


def trades(project: str, name: str, identity: str, tmp: Path,
           also: frozenset[str] = frozenset()) -> list[tuple[str, Path, dict]]:
    """The strategy's and its sisters' trades in every databank that was exported.

    Args:
        project: SQX project name.
        name: The strategy's name there.
        identity: Its identity; an export whose `identity.csv` does not pair the two is
            another strategy's under the same name and is left out.
        tmp: A scratch folder.
        also: Identities SQX gave the same strategy later (`late.aliases`).

    Returns:
        (file stem, folder, what the manifest says) per databank and day with trades of it:
        the build, the OOS, every other market (step 10) and every other timeframe (step 12),
        with the `identity.csv` and `timeframes.csv` rows that sit beside them. A databank
        holding the very trades of an earlier one is not written again: `also` names it.
    """
    found, seen = [], {}
    for path in sorted((DATA / "raw" / project).glob("*/*/trades.parquet")):
        databank, day = path.parts[-3:-1]
        rows = family(table(path), name)
        if not len(rows) or not any(named(path.parent, name, i) for i in {identity, *also}):
            continue
        # `Ticket` is SQX's numbering inside one databank, not part of a trade
        print_ = int(pd.util.hash_pandas_object(rows.drop(columns="Ticket", errors="ignore"),
                                                index=False).sum())
        if print_ in seen:      # SQX copies a databank to feed the next task: same trades, kept once
            seen[print_].setdefault("also", []).append(f"{databank}.{day}")
            continue
        out = tmp / databank / day
        for side in [path, *sorted(path.parent.glob("*.csv"))]:
            _cut(side, name, out)
        if (path.parent / "manifest.json").exists():      # what the export was asked for
            shutil.copyfile(path.parent / "manifest.json", out / "manifest.json")
        seen[print_] = {"study": "operaciones", "databank": databank, "day": day, "trades": len(rows)}
        found.append((f"operaciones.{databank}.{day}", out, seen[print_]))
    return found


def sisters(project: str, name: str, identity: str, tmp: Path,
            also: frozenset[str] = frozenset()) -> list[tuple[str, Path, dict]]:
    """What step 12 made of the strategy on other timeframes, enough to make it again.

    Args:
        project: SQX project name.
        name: The mother's name.
        identity: Its identity: a batch whose mother file of that name is another strategy
            is left out.
        tmp: A scratch folder.
        also: Identities SQX gave the same strategy later (`late.aliases`): the mother's file may carry one.

    Returns:
        One entry per day the mother was scaled: its rows of `scaling.parquet` (every
        parameter written and what it was, the ATR ratio used, the file's identity) and its sisters' rows of every
        report table of that day and of every step's verdict. No sister's .sqx is kept (owner, 2026-10-08):
        `python3 -m sqx.variants.rebuild` writes it again from these rows.
    """
    found = []
    for path in sorted((DATA / "crosstf" / project).glob("*/scaling.parquet")):
        day, out = path.parent.name, tmp / path.parent.name
        mother = path.parent / "sqx" / f"{name}.sqx"     # the mothers ride along verbatim
        n = _cut(path, name, out) if mother.exists() and sqxfile.identity(mother) in {identity, *also} else 0
        if n:
            rows = pd.read_parquet(out / path.name)
            # What a rebuilt sister is checked against: SQX's retest gives the same strategy
            # another identity (knowhow/sqx-format/fabricated-variant-identity-differs-from-retest.md).
            rows[FABRICATED] = [sqxfile.identity(Path(f)) if Path(f).exists() else "" for f in rows["path"]]
            rows.to_parquet(out / path.name, index=False)
            for report in sorted((DATA / "reports" / project).glob(f"*/{day}/*/*")):
                if report.suffix in (".csv", ".parquet"):
                    _cut(report, name, out / report.parts[-4] / report.parts[-2], True)
            for said in sorted((DATA / "autopilot" / project).glob("*/paso-*/verdict.csv")):
                _cut(said, name, out / "autopilot" / said.parts[-3] / said.parts[-2], True)
            found.append((f"hermanas.{day}", out, {"study": "hermanas", "day": day, "sisters": n}))
    return found


def metrics(project: str, name: str, tmp: Path) -> list[tuple[str, Path, dict]]:
    """SQX's own metrics of the strategy and its sisters in every databank that was exported.

    Args:
        project: SQX project name.
        name: The strategy's name there.
        tmp: A scratch folder.

    Returns:
        One entry, `metricas`: `<databank>/metrics.csv` cut to the family, for each
        `metrics/<P>/<databank>/metrics.csv` that names it. That tree keeps only the current
        export and by name alone: an export of a later build under the same name is that
        build's, which the trades of `operaciones.*` — paired by identity — are not.
    """
    n = sum(_cut(path, name, tmp / path.parent.name)
            for path in sorted((DATA / "metrics" / project).glob("*/metrics.csv")))
    return [("metricas", tmp, {"study": "metricas", "rows": n})] if n else []



def neighbours(project: str, name: str, tmp: Path) -> list[tuple[str, Path, dict]]:
    """Step 13's T1 batch (`raw/<P>/T1_Neighbours/<day>/neighbours.parquet`) cut to the strategy.

    Returns:
        One entry, `vecinas`: its rows of each day's table, which no `mcRetest` result carries.
    """
    n = sum(_cut(path, name, tmp / path.parent.name)
            for path in sorted((DATA / "raw" / project / "T1_Neighbours").glob("*/neighbours.parquet")))
    return [("vecinas", tmp, {"study": "vecinas", "rows": n})] if n else []
