# assets — the blocking preflight

SQX's own spread, commission and swap for an instrument are frequently **not** what the broker
charges. Those differences decide whether a backtest is honest, so they are recorded here, per
asset, and consulted before anything is authored.

## The rule

**Before creating or modifying any project, task or template for a symbol, run:**

```bash
python3 -m core.assets <SYMBOL>
```

Read its output back to the owner, saying which values you are applying and where they differ from
SQX. It exits non-zero when the asset has no file, or when `spread` or `commission` still carry
`use: null` — that means the owner has not decided yet. **Stop and ask. Do not pick a value.**

## What a file holds

One YAML per asset, named after the instrument (`XAUUSD.yaml`, `USATEC.yaml`). Each cost field has:

- `sqx_default` — what SQX carries today, read from the live projects, never edited by hand.
- `use` — what to actually apply. `null` means undecided and blocks authoring.
- `why` — one line on why it differs. This is the part that stops the same discussion recurring.

The rest (tick size, minimum distance, point value, which projects use it) is context, read from the
same source. Regenerate the `sqx_default` side with `python3 1_sqx/inspect/instruments.py`, which
lists every instrument configured across the master's projects.

## Special cases

`special/` holds cases that cross assets: session filters, news windows, broker quirks, anything that
is not one instrument's cost. Every file there is surfaced by the preflight, so a case written once
is seen by every future session.

## Adding an asset

Copy the closest existing file, fill `sqx_default` from `instruments.py`, leave `use: null`, and ask
the owner for the real numbers. A file with invented values is worse than no file: it looks decided.
