# File formats

## `.sqx` — a strategy

🔬 It is a **ZIP**. Members: `META-INF/MANIFEST.MF`, `settings.xml` (~5.8 MB),
`strategy_Portfolio.xml` (~25 KB), and many `Results/…Orders.bin`.

- **Never hash the file to compare strategies.** The ZIP embeds timestamps, so identical strategies
  produce different file hashes. **Identity = SHA-256 of the inner `strategy_Portfolio.xml`.** Using
  file hashes inflated a 13,288-strategy corpus into 17,754 "unique" ones.
- **Get the symbol without parsing anything.** ZIP entry names contain
  `Results/Main: <SYMBOL>_<feed>/…` — e.g. `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`. Regex the
  namelist; do not open the 5.8 MB `settings.xml`.
- `strategy_Portfolio.xml` is plain XML, readable with no SQX running.
- 🔬 Indexing all 17,754 `.sqx` on this box takes **1.5 s** with 48 processes. It is cheap; do it
  rather than guessing. Tool: `1_sqx/inspect/index_sqx.py`.
- 📓 Do **not** try to parse `orders.bin` — private versioned format inside Java serialization. SQX
  exports the same data natively (`-tools action=orderstocsv`, see `04-export.md`).

## `project.cfx` — a project

🔬 Also a **ZIP**: `config.xml` + one `<TaskType>-Task<N>.xml` per task. Reading is safe at any time —
no SQX process needed, no state touched. `1_sqx/inspect/dump_project.py` renders one as Markdown.

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
