---
q: where per-task costs live SQX project; Setup vs InstrumentInfo; different spread IS OOS per task; commission method flip use; project unresolved resources; instrument edit defaultslippage; setups.py
tag: 🔬  date: 2026-09-23  see: costs/commission-methods, costs/swap-types, conditions/retest-additional-markets
---
# Per-task costs live in each task's `<Setup>`; never edit `<Resources><Symbol><InstrumentInfo>`
- Every task carries its own window, slippage, spread, commission and swap in `<Setup>` → spread_is on the build task, spread_oos on the rest. A cost fixed in one task is unchanged in the others.
- `sqx/projects/setups.py` writes them from `assets/`; skips Setups whose `<Chart>` is another symbol (cross-market keeps its own costs). Load with `-project action=loadconfig`.
- Choose the commission method by flipping `use` on the two `<Method>` SQX always ships; never add one.
- ⚠️ `InstrumentInfo` is the instrument DEFINITION: any disagreement with the registry (`-instrument action=list`) → `Project has unresolved resources`.
  Not: "per-task costs are in InstrumentInfo" / "a worker cannot be priced from assets/" (a clean bisection over the wrong element).

## Evidence
```xml
<Setup dateFrom="2018.01.01" dateTo="2022.12.31" slippage="5" minDist="10" …>
  <Chart symbol="XAUUSD_DukasM1_Infinox" timeframe="M30" spread="10.0" />
  <Commissions>
    <Method type="SizeBased" use="false">…8…</Method>
    <Method type="PercentageBased" use="true">…0.001…</Method>
  </Commissions>
  <Swap use="true" type="percent" long="-7" short="-7" tripleSwapOn="WEDNESDAY" rolloutHour="23:00" />
</Setup>
```
- Setup dates are `YYYY.MM.DD`; `<Resources>` `<Symbol>` data range uses epoch ms.
- Verified: one project, Build on `build` (2008–2017, spread 5.0, slippage 2.5) + 14 Retests on `oos1` (2018–2022, spread 10.0, slippage 5), `loadconfig` + start; stored `.cfx` shows those values per task.
- Changing `defaultSpread`/`defaultSlippage` inside `InstrumentInfo` makes the project unresolvable; rewriting the same value is fine.
- `-instrument action=edit` works; `defaultslippage` works though `internal/web/SQUANT/help.txt` (12 params) omits it; `commissions=` and `swap=` did not take in three forms.
- Registry = `user/data/data.db`; `bin/sqx-worker.sh start` copies it from the master only when the master fingerprint changed (`--force-sync` overrides).
- Dropping a `.cfx` on disk also loads; `loadconfig` is the supported path (`docs/project-config-workflow.md`).
