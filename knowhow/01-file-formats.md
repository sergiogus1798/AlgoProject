# File formats

## `.sqx` — a strategy

🔬 It is a **ZIP**. Members: `META-INF/MANIFEST.MF`, `settings.xml`, `strategy_Portfolio.xml`,
`lastSettings.xml`, `version.txt`, `orders.bin` and one `Results/Main: <SYMBOL>_<feed>/dailyEquity.bin`.

- 🔬 **They are not all multi-MB.** Measured over the 15,971 `.sqx` on the master, 2026-09-04:
  min **28 KB**, median **226 KB**, p90 870 KB, max 15.4 MB. The size is `orders.bin` plus the daily
  equity curve — how much *result* the strategy carries, not how complex it is. `settings.xml` and
  `strategy_Portfolio.xml` stay in the tens of KB throughout. The old "a `.sqx` is about 6 MB" note
  was generalising from one large file, and it was the stated reason `core.sqxfile` had no golden
  test; `tests/fixtures/strategy.sqx` is a real 28 KB one.

- **Never hash the file to compare strategies.** The ZIP embeds timestamps, so identical strategies
  produce different file hashes. **Identity = SHA-256 of the inner `strategy_Portfolio.xml`.** Using
  file hashes inflated a 13,288-strategy corpus into 17,754 "unique" ones.
- **Get the symbol without parsing anything.** ZIP entry names contain
  `Results/Main: <SYMBOL>_<feed>/…` — e.g. `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`. Regex the
  namelist; do not open the 5.8 MB `settings.xml`.
- `strategy_Portfolio.xml` is plain XML, readable with no SQX running.
- 🔬 Indexing all 17,754 `.sqx` on this box takes **1.5 s** with 48 processes. It is cheap; do it
  rather than guessing. Tool: `sqx/inspect/index_sqx.py`.
- 📓 Do **not** try to parse `orders.bin` — private versioned format inside Java serialization. SQX
  exports the same data natively (`-tools action=orderstocsv`, see `04-export.md`).

## `project.cfx` — a project

🔬 Also a **ZIP**: `config.xml` + one `<TaskType>-Task<N>.xml` per task. Reading is safe at any time —
no SQX process needed, no state touched. `sqx/inspect/dump_project.py` renders one as Markdown.

- 🔬 **SQX rewrites the whole `project.cfx` on save and on exit.** All 14 project files were restamped
  within the same second (`14:33:43`, 2026-09-02). **Any on-disk edit to a project a running instance
  holds is silently discarded.** No error. Use the `-project` API instead (`03-driving-sqx.md`).
- 🔬 `config.xml`'s `<Task title=>` is a **display label only**. The task's real output databank lives
  inside the task XML at `<Databank name="Output" value=>`. Clone a task without changing that and
  every clone writes to the same databank.
- 🔬 `<Databank … value="null">` is not a bug — `null` is SQX's literal for "use the task type's
  default databank". Build tasks ship this way.
- 🔬 A `.cfx` with **only `config.xml`** is not a loadable project template. Both
  `~/Desktop/Benchmark.cfx` and anything `saveconfig` produces are single-file and rejected.
- 🔬 **The opposite failure exists too: a `config.xml` declaring task files the archive does not
  hold.** The GUI then drops the project with no error at all. Scan every project for it with
  `sqx/inspect/project_health.py`; heal one with `sqx/repair/graft_tasks.py`.
- 🔬 **`<Project templateFile=>` in `config.xml` is dead metadata, and is not the strategy template.**
  It records the `.cfx` the project was imported from. On this install it is a Windows path on every
  project imported off Windows, re-encoded UTF-8-as-CP1252 **seven times over**; decoded it reads
  `C:\Users\Rubén Martínez\OneDrive\Escritorio\FILTROS\Build strategies.cfx`. The strategy
  template that actually matters is `<StrategyType templateFile=>` inside the Build task.
  `project_health.py` decodes any such field.
