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
