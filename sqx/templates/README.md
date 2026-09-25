# sqx/templates — authoring strategy templates from an idea

| file | what it does | run it | in → out |
|---|---|---|---|
| `build.py` | Fix one concrete block — authored, or native read from the install's AlgoWizard `config.xml` — into a build-confirmed skeleton and emit the template; `--param` fixes what the owner named | `python3 -m sqx.templates.build <name> <blocks.xml\|config.xml> <key> <out.sqx> [--param '#Type#=1'] [--install ROLE]` | a skeleton + one block → an importable `.sqx` |
| `registry.py` | Record a template in the library, and each market it has been tried on | `python3 -m sqx.templates.registry --help` | a template or a run → a row in `registry.csv` / `runs.csv` |
| `holes.py` | Which parts of a template the builder fills at random, which are bound to a group, and which the template fixes | imported | a `.sqx` → its holes and its fixed blocks |

What the owner means by "create a strategy", in his words (2026-09-22). Three steps, in order:

1. **Understand the exact logic.** Usually one simple condition; when it is more, he says so.
2. **Look for it** — SQX's native blocks first, then his own custom blocks. **If it does not exist,
   author the custom block.** Do not approximate it with the nearest native block that already
   exists: "closes above" and "crosses above" are different strategies, not spellings.
3. **Build the template** with that condition fixed in the signal, plus **one random condition**
   unless he says otherwise.

## Defaults — apply them silently, then say which you applied

| unspecified | assume |
|---|---|
| direction | **long** |
| the random condition | **free**: `#Group#` empty, sampling the whole 500-block Conditions vocabulary |
| how many extra conditions | **one** |
| `Shift` | **1**, the last closed bar — SQX's own default |
| indicator periods, deviations and the like | **optimizable**: "the same logic, but flexible" |
| anything he named explicitly (the upper band, say) | **fixed**, never parametrised |

The last row is the one that gets read backwards. His words: *"fix it to what I said, we don't want
the builder building rubbish."* Parametrising what he named widens the search with variants he has
already ruled out; parametrising what he did not name — periods, deviations — is exactly the point.

The one thing never assumed is step 1. State and transition are different logics and reach
different strategies, so that question is always asked, however obvious the phrasing looks.

## What the structure is, and why nothing new has to be invented

`AND(RandomCondition, <concrete block>)` is already build-confirmed on this install — it is the
entry signal of the stock `highest_breakout_template_daily_filter.sqx`, and the `session_market`
shape was derived from it. So a fixed condition beside one random hole needs **no new skeleton**;
only which concrete block sits in the fixed slot varies. Details and the XML in
`knowhow/authoring/`.

Two consequences worth keeping straight, because they look contradictory and are not:

- A **hole** (`RandomCondition`) reaches blocks only through a random group — and with `#Group#`
  left empty it reaches the whole vocabulary instead, which is what the stock template does.
- The **fixed half** reaches any block directly. A block no group pools is perfectly usable there.

So "is it pooled?" is a question about holes only. `python3 -m sqx.inspect.vocabulary <term>`
answers both halves at once: whether the block exists, and which groups pool it.

## Naming

camelCase, `_` separating **roles** and never words: `keltnerUpperCrossUp` for an entry-only
template, `keltnerUpperCrossUp_atrTrail` when it fixes the exit too. No symbol and no timeframe in
the name — a template belongs to no market; that is a row in `runs.csv`.

## Where the artefacts live

Not here. The library is `AlgoData/templates/` (`core.paths.template_dir`), one self-contained
folder per template: the `.sqx`, its brief, and under `deps/` the blocks and groups it references,
so it installs on any SQX unchanged. This folder holds the authoring sources and this contract.
