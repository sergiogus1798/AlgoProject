# pooledProfile — alternatives that were on the table

Argue a change here before making it in code.

- **The combined statistic.** Stouffer's sum weighs every asset alike and looks for one sign in
  all of them: an effect in half the group is diluted. Fisher's product or the higher-criticism
  statistic would name «some asset has it»; a sum weighted by trades would lean on the liquid
  ones. All would be compared with the same joint draws.
- **The groups.** The four classes. Forex mixes USD pairs and JPY crosses, and a long in USDCHF
  is the opposite dollar bet of a long in EURUSD; `tau` and `i2` say when a group is not one.
  Finer groups cost tests (the correction) and assets per group (the power).
- **The shared clock drops bars.** A bar one asset lacks is dropped for the whole group; the
  next bar's gap then carries the missing move. Indices lose 5-24 % of their bars (mostly the
  years before the youngest asset's build starts).
- **Shrinkage ignores the cross-correlation.** DerSimonian-Laird takes the assets' errors as
  independent; correlated assets look more alike than they are, so `tau` is biased down and the
  shrinkage is too strong. The group's p does not have this problem (joint draws).
- **The strict route's filters read the asset's own stability and frequency**, not shrunk ones.
- **Placebo worlds pair draw j of every group**: the groups are taken as independent of each
  other. A joint resampling across groups would need one clock for all 19 assets.
- **Metal and energy are two assets each**: the sum gains a root of two at most, less what
  their correlation takes away.
