# crossmarket/verdict — given those numbers, what is there to distrust?

The inference layer: the statistics that are not simulations, and every reason a number should be
read with suspicion. It **computes none of the numbers it judges**, it imports nothing from
`simulate/` or `render/`, and — the property that distinguishes this study from most — **it issues no
verdict and never drops a market.** It locates a result, names what is wrong with it, and stops. The
decision is the owner's, made outside here.

**Imports from:** `model/` (for the bootstrap) and itself
**Consumed by:** `simulate/exposure.py` (one declared exception, for `fieller`), `render/`,
`explorer/`
**Must not contain:** a simulation, an equity path, a priced trade, or any HTML beyond `alerts.py`'s
four fields

| file | what it does | run it | in → out |
|---|---|---|---|
| `inference.py` | Every reason to distrust a market, which test a result actually is, whether a sweep point has the power to be read, and which way a sweep curve goes. **It decides nothing** | imported | row, blocks, points → warnings, power, trend |
| `significance.py` | Minimum track-record length and bootstrap CIs on PF and expectancy. No DSR — see `POSSIBLE_IMPROVEMENTS.md` | imported | returns → moments, CI |
| `fieller.py` | The interval of a ratio whose denominator can be zero: unbounded when it is, instead of a number that looks decided | imported | moments → interval |
| `breadth.py` | Breadth, worst-market floor and PF dispersion across one strategy's markets | imported | per-market rows → breadth, floor, CV |
| `alerts.py` | Every warning in four parts: what fired it, what it affects, what it does **not**, and what to do | imported | row → HTML |

A `grep` is the proof that the direction holds:

```bash
grep -rn "from studies.transfer.crossmarket" verdict/ | grep -vE "crossmarket\.(model|verdict)"   # empty
```

## A gate that excludes evidence is a decision, and it belongs to the owner

🔬 The first build turned every diagnostic into a gate: a market with fewer than 30 trades, or with
under 95% of entries on a bar open, was dropped from the study entirely, and a strategy measured on
fewer than four surviving markets came out NO EVALUABLE. Two things followed, both bad.

- **It threw away real results.** `Strategy 24.14.35` came out NO EVALUABLE despite p = 0.005 on
  Brent under every null model, because 8.6% of its Brent entries were pending fills. Losing 100% of
  a market's evidence over 8% of its trades is not conservatism, it is discarding the measurement.
- **It was structurally unreachable.** `MIN_MARKETS = 4` against the two markets the retest actually
  ran made NO EVALUABLE the only possible outcome for XAUUSD, for every strategy, forever — and
  nothing in the code or the report said so.

The replacement is this layer as it stands: the study reports every market it measured and names,
beside each one, every reason to distrust it (`inference.warnings()`). Nothing is hidden and nothing
is decided. **A threshold that removes data is a decision about what counts as evidence; it is the
owner's, not the analysis's.**

Thresholds themselves are read from `config.yaml` through `inputs/config.py` — `diagnostics.alpha`,
`diagnostics.min_trades`, `diagnostics.min_on_grid`, `sweep.min_trades` and the rest. Nothing here
hard-codes one.

## A warning says what it does *not* affect

Each of the seven is four fields instead of one sentence: what fired it **with the number that fired
it**, what it affects, what it does *not*, and what to do. The missing half was the third one.

- `bad_hold_fit` touches exactly one null model — the other three reuse the real holds and are
  immune.
- `no_drift` touches exactly one number — A and A per unit of risk are unaffected, and Brent, which
  fires it, has the strongest A of the three.
- `pending_fills` touches Test 1a only; 1b and 1c use no null model at all.
- `fill_mismatch` is the one that touches **everything**, and the only one whose answer is "fix the
  input" rather than "read the number carefully".

🔬 **Two of the nine were measuring the wrong quantity until 2026-09-21**, and both fired constantly
on data that had nothing wrong with it:

- `pending_fills` read the entry **clock** — is the timestamp on a bar boundary. Over 960,705 trades
  the 4,613 entries stamped mid-bar are priced *identically* to the 956,092 stamped on it, so it was
  reporting a stamping quirk as a price-conditional fill. It now reads the entry **price** against
  its own bar's, discounting the market's constant spread (`pricing.fill_profile`). The clock figure
  is still reported as `on_bar_open`, and warns on nothing.
- `fill_mismatch` fired on `fill_error > 0`. A constant offset is a **spread**, absorbed by the
  per-trade cost `backtest.setting()` recovers and therefore paid by every random run too — the
  comparison is symmetric and there is nothing wrong. It now fires above `max_fill_error` in
  median-ATR units, which is what a wrong feed or a wrong timeframe inflates.

Both were verified to still fire: a feed displaced 3 ATR trips `fill_mismatch`; H1 bars under an M30
backtest drop `on_open_price` to 0.566; 6% of entries moved half an ATR off their bar trips
`pending_fills` while 3% does not.

Read as one sentence, all three looked like they invalidated the market. `inference.py` decides
**whether** a warning fires; `alerts.py` says what it means, and `alerts.TRIGGER` is what puts the
firing number into the sentence.

## Contracts and traps

- **E is never a bare number.** It divides by the market's own drift, so where that drift is not
  distinguishable from zero the ratio has no finite interval at all. `fieller.interval()` returns the
  unbounded one and says so, beside the share of bootstrap replicates whose denominator changed sign.
  Measured on Brent: E = +17.4, CI *no acotado*, 54.5% of replicates with a drift at or below zero.
  The number the panel leads with is **A per unit of risk**, which divides by the market's typical
  bar move and is therefore defined everywhere. `fieller.UNBOUNDED = 1.0` is not a threshold anyone
  chose — it falls out of the algebra, where g crossing 1 stops the quadratic having two real roots
  on the same side.
- **A confidence interval brackets the estimator it is an interval for.** A's bootstrap is weighted
  by holds because A itself is pooled over occupied bars; unweighted, it sat 9% away from its own
  point estimate.
- **Any metric shaped "strategy over market" inherits the drift problem.** 🔬 Measured over M30 bars,
  gold `t = +3.13`, silver `t = +1.61`, **Brent `t = −0.11`** — and on Brent E came out **−69.4**, for
  the market with the *strongest* A of the three. Check the denominator's own significance before
  reporting any such ratio.
- **No Deflated Sharpe, and there will be none here.** It needs the count of trials made during
  generation, which does not exist at this stage; fabricating one would produce a credible, false
  number. Recorded with its reason in `POSSIBLE_IMPROVEMENTS.md`.
- **`inference.warnings()` never removes a row.** It returns a list of keys. Anything that filters on
  them is doing something this study deliberately does not.
- **The English/Spanish mirror is a contract, not duplication.** `inference.WARNINGS` is the code's
  vocabulary; `render/panel.WARNINGS_ES` and `alerts.TEXTS` are the owner's. A key added here without
  a row there renders as a missing entry, not as a fallback.
- **`breadth.py` excludes no market either** — a row that collected warnings still counts, and the
  warnings are what say how much to trust it.
