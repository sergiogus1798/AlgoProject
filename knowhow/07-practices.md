# Working practices and research lessons

## Practices that already bit

- 🔬 **Don't pipe complex Python through `bash -c` heredocs.** Quoting mangles it and you get
  `SyntaxError: '(' was never closed`. Write the script to a file, then run it.
- 🔬 **Verify a write by reading back what SQX stored**, never by trusting the success message. The
  `loadconfig` auto-rename (`03-driving-sqx.md`) makes a successful-looking write land somewhere else
  entirely.
- 🔬 **Session names are not stable.** A session is auto-named (e.g. `algoproject-88 [4d9316]`) and a
  reopened window gets a different name; `ListAgents` shows only sessions running right now. Put
  identity in **files**, not in session names.
- Multiple sessions share all this state and destructive operations are not reversible. One owner per
  lane — see the lanes table in `1_sqx/CLAUDE.md`.
- 🔬 Launch SQX only with `ELECTRON_RUN_AS_NODE` unset. VS Code exports it; inheriting it makes SQX's
  Electron shell run as plain Node and the GUI dies with `bad option: --no-sandbox`.

## Research lessons

- 🔬 **A stop-fill assumption can dominate a stop study's conclusion.** In the ATR-stop study
  (`archive/studies/atr_stop_study.py`), filling exactly at the stop made tight stops look
  excellent (PF 2.09 at 0.5×ATR); allowing 0.25×ATR of slippage erased it (PF 1.49, net −37%), while a
  3×ATR stop lost only 11%. **Never present an MAE-threshold stop simulation without a slippage
  sensitivity — the tighter the stop, the more of the answer is the assumption.**
- 🔬 In this architecture a stop does **not** add round trips: it moves an exit, so total commission is
  constant in the number of trades.
- 🔬 Two structurally different populations can share one databank (`06-locations.md`). Check for that
  before pooling any exit statistic.

- 🔬 **Conditioning on a metric destroys that metric's own remaining signal.** Measured 2026-09-04 on
  the 10,000 strategies of `XAUUSD/OOS` (`AlgoData/metrics/XAUUSD/OOS/metrics.csv`, report in
  `AlgoData/reports/XAUUSD/OOS/2026-09-04/`; reproduce with
  `python3 2_tasks/reports/is_oos.py --project XAUUSD --databank OOS`). Deduplication was **checked,
  not assumed**: 10,000 distinct names and only 2 byte-identical metric vectors, so n stands.
  `Sharpe Ratio (IS)` predicts `Profit factor (OOS)` at ρ +0.223 over the
  whole population, but **inside the top 20% by that same Sharpe it falls to +0.088** and a different
  metric leads the ranking. This is range restriction, and it means a predictor ranking computed on
  the full population **does not tell you what to filter on second**. Any multi-clause filter must
  have its ranking recomputed inside the surviving subset — which is why
  `2_tasks/reports/panel.html` recomputes rather than showing stored numbers.
- 🔬 **At n≈10,000 the single-test significance floor carries no information.** |r| > 0.020 clears the
  ordinary two-tailed 5% level, so 19 of 21 in-sample metrics "pass" against OOS profit factor. Report
  a family-wise or FDR correction (`2_tasks/analysis/correlations.py:discoveries`) and then argue from
  **effect size**, never from p. A p-value at this sample size only says the population is large.
- 🤔 The XAUUSD population these two lessons came from is **generic strategies**, not template-driven
  ones — see the owner's 2026-09-04 decision in `03-driving-sqx.md`. Whether the same relationships
  hold for a template-built population is untested.
