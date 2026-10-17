"""The data root's secondary trees: template library, pipeline, permutations, logs, backups, caches, spread.

Split out of core/paths.py, which keeps the installs, the primary exports, `filters_root()`, `funding_dir()` and `portfolio_dir()`."""

from pathlib import Path

from core.paths import DATA, MASTER
from core.symbols import current


def template_dir(name: str) -> Path:
    """Folder of one strategy template in the library.

    Args:
        name: Template name in camelCase, underscores separating roles only, e.g.
            "keltnerCrossClose_atrTrail".

    Returns:
        Path under the data root. Self-contained — the .sqx, its brief and the blocks and
        groups it references — so it installs on any SQX unchanged. A template carries no
        symbol and no timeframe: those belong to a run.
    """
    return DATA / "templates" / "library" / name


def template_registry() -> Path:
    """The CSV of every template in the library, one row each.

    Returns:
        Path under the data root. CSV and not parquet because a human reads it; written by
        code, never hand-edited.
    """
    return DATA / "templates" / "registry.csv"


def template_runs() -> Path:
    """The CSV of every (template, symbol, timeframe) that has been tried.

    Returns:
        Path under the data root. Separate from the registry because one template is tried
        on many markets: "have I run this on NASDAQ H1" is a row here, not a second copy.
    """
    return DATA / "templates" / "runs.csv"


def template_draft(name: str) -> Path:
    """Draft brief of a template the interview composed but nobody has authored yet.

    Args:
        name: Template name in camelCase, as it will appear in the registry.

    Returns:
        Path under the data root, beside the library rather than inside it. A draft is not
        a template: it carries no .sqx and no deps, so a folder in library/ would make the
        catalogue count strategies that do not exist.
    """
    return DATA / "templates" / "drafts" / f"{name}.json"


def vocabulary_snapshot(install: str, day: str) -> Path:
    """Where one install's block-and-group inventory is kept.

    Args:
        install: Folder name of the install, e.g. "SQX_w1".
        day: Snapshot date as YYYY-MM-DD.

    Returns:
        Path under the data root. Dated and kept, not replaced: the point is comparing
        installs and dates, which a single current file cannot answer.
    """
    return DATA / "templates" / "vocabulary" / f"{install}-{day}.json"


def work_dir(project: str, strategy: str) -> Path:
    """Where one mother strategy's ledger and stage outputs live.

    Args:
        project: Project name on the master.
        strategy: Name as SQX shows it, e.g. "Strategy 17.9.39"; spaces become underscores
            and dots hyphens, the spelling sppUltra uses for its brief filenames.

    Returns:
        Path under the data root. It holds kilobytes of ledger next to gigabytes of
        variant data, and outlives the data: the ledger is what makes the deletion
        auditable instead of a loss.
    """
    return pipeline_dir(project, strategy.replace(" ", "_").replace(".", "-"))


def pipeline_dir(project: str, strategy_slug: str) -> Path:
    """One mother strategy's pipeline ledger and stage outputs.

    Args:
        project: Project name on the master.
        strategy_slug: The strategy name as `work_dir` spells it.

    Returns:
        Path under the data root. The ledger outlives the data `pipeline.cleanup` sweeps.
    """
    return DATA / "pipeline" / project / strategy_slug


def variants_dir(project: str, strategy: str) -> Path:
    """One strategy's fabricated permutations and their manifest; rebuilding replaces it.

    Args:
        project: Project name on the master.
        strategy: Strategy name as SQX writes it.

    Returns:
        Path under the data root.
    """
    return DATA / "strategyPermutations" / project / strategy.replace(" ", "_")


def crosstf_dir(project: str, day: str) -> Path:
    """One batch of timeframe-scaled siblings and the manifest of what was rescaled.

    Args:
        project: Project name on the master.
        day: Fabrication date as YYYY-MM-DD.

    Returns:
        Path under the data root. Dated and immutable, like harvest/, because a cross-
        timeframe verdict is only readable against the exact scaling that produced it:
        `scaling.parquet` is the sole record of which parameter was divided and how far
        the rounding moved it, and a `.sqx` without it is indistinguishable from any other.
    """
    return DATA / "crosstf" / project / day


def log_archive(install_name: str) -> Path:
    """One install's SQX logs, gzipped before SQX prunes them; `projects/<P>/` condensed.

    Args:
        install_name: Folder name of the install, e.g. "SQX" or "SQX_w1".

    Returns:
        Path under the data root, mirroring `<install>/user/log`.
    """
    return DATA / "logs" / install_name


def data_update_backups() -> Path:
    """Where `sqx.data.update` records what it saw before touching the master's data.

    Returns:
        Path under the data root, one JSON per run.
    """
    return DATA / "backups" / "data-update"


def projects_backup(name: str) -> Path:
    """A frozen copy: a donor `project.cfx`, mother strategies, install configs.

    Args:
        name: Folder name, e.g. "XAUUSD_base_2026-09-21".

    Returns:
        Path under the data root. SQX rewrites a live `project.cfx` on save and exit, so
        the copy here is the fixed point new projects are cloned from.
    """
    return DATA / "projectsBackup" / name


def cache_dir(name: str) -> Path:
    """A disposable cache, regenerated by whoever reads it.

    Args:
        name: Which cache, e.g. "montecarlo" or "crossmarket".

    Returns:
        Path under the data root. Deleting it costs a recomputation and nothing else.
    """
    return DATA / "cache" / name


def project_registry() -> Path:
    """The CSV of every custom SQX project the builder created, and whether it was retired.

    Returns:
        Path under the data root. CSV because a human reads it; written by
        `sqx.projects.registry`, never hand-edited.
    """
    return DATA / "projects" / "registry.csv"


def retired_project(install: str, name: str, day: str) -> Path:
    """Where a retired project's `project.cfx` (and any databank kept with it) is archived.

    Args:
        install: Install folder name, e.g. "SQX_w2".
        name: Project name.
        day: ISO date of the retirement.

    Returns:
        Path of a .tar.gz under the data root. The databanks are not archived unless named:
        what a run found already lives in `raw/`, `harvest/` and `reports/` as parquet.
    """
    return DATA / "projects" / "retired" / install / f"{name}-{day}.tar.gz"


def retire_queue() -> Path:
    """Projects the owner named for retirement, one `<role> <name>` per line.

    Returns:
        Path under the data root. The weekly cleanup retires what it lists — the only way a
        master project is ever retired unattended — and removes each line once done.
    """
    return DATA / "projects" / "retire-queue.txt"


def tick_file(feed: str) -> Path:
    """The tick history SQX keeps for one tick feed, read in place and never copied.

    Args:
        feed: SQX symbol, e.g. "XAUUSD_TICK".

    Returns:
        The master's `.dat`: several GB of delta-coded ask/bid ticks that only
        `core.tickfile` reads. Read-only; SQX rewrites it on a data update.
    """
    feed = current(feed)  # an older .sqx names the feed as it was before 2026-10-01
    return MASTER / "user" / "data" / "History" / feed / f"{feed}_TICK.dat"


def bar_file(feed: str) -> Path:
    """The M1 history SQX keeps for one bar feed, read in place: `core.tickfile.bars` decodes it."""
    feed = current(feed)
    return MASTER / "user" / "data" / "History" / feed / f"{feed}_M1.dat"


def spread_dir(feed: str = "") -> Path:
    """One tick feed's spread folder (minute table + reports) under the data root; empty feed = the study's own.

    Returns:
        The minute table derives from `tick_file(feed)` and is stamped with its size and date.
    """
    return DATA / "spread" / feed


def tmp_dir() -> Path:
    """The project's own temp folder `<data root>/tmp` (created on first call), off the 3.9 GB `/tmp`.

    Pass it as `dir=` to `tempfile`; `bin/weekly-claude-cleanup.sh` prunes what a crashed run left.
    """
    out = DATA / "tmp"
    out.mkdir(parents=True, exist_ok=True)
    return out


def campaign_dir() -> Path:
    """The campaign's root: `ledger.jsonl`, `batches/<id>.json`, `runs/<workflow>/`, the STOP file."""
    return DATA / "campaign"
