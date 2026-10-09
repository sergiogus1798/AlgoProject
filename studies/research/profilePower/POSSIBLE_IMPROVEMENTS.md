# profilePower — alternatives that were on the table

Argue a change here before making it in code.

- **The base world.** Sign-flipped bars have no drift, so a long measure never earns the drift
  the real asset has; the profile's null keeps the drift, so the power on a trending asset is
  the same but the `pays` filter is easier there than here. Alternatives: the real bars as they
  are (one world, no replication: detection is 0 or 1), or a block resample of them (keeps the
  drift, loses the volatility clustering, which is what the profile's null also loses).
- **A plant in a nearly-always-long measure is drift.** `look48_hold16` holds most bars; the
  planted return becomes the series' drift, the null keeps it, and nothing is detected at any
  size. That is the profile's design (the null carries the drift), not a fault of the plant.
- **A plant large enough is drift too.** On noise bars, 20 costs per trade in `channel20` (held
  30 % of the bars) is detected always and 60 costs never: the planted return lifts the whole
  series, every resampled series breaks out upwards as well, and the null's t rises with the
  real one (18 against 20). The curve is read at its first crossing for that reason.
- **The measure moves under its own plant.** The edge follows the condition read on the base;
  the test reads the condition again on the planted series. A fixed point (plant, re-read,
  re-plant) would hold the effect exactly; the realised multiple is stored instead.
- **One measure carries the family.** The other measures of the family are not run on the
  planted series (each replication tests one measure, to cost 1/99 of a cell). Whether a
  neighbour sees the same edge is in `analytic.widened`, not in the simulation.
- **The cut is fixed at today's.** Benjamini-Hochberg's threshold moves with what the map finds;
  a map with more true effects would be more lenient. The curve at `single` (5 %, uncorrected)
  is the other bound.
- **The single-level test reads the first chunk only** (250 draws): a valid test at 5 %, a
  little less powerful than one at 3,000 draws.
- **The approximation takes the t as normal** with the null's spread. It misses the plant's
  feedback on the entries and the skew of few trades; `calibration.csv` shows by how much.
- **Short side.** On a directionless base short is the mirror of long and is not run;
  `plant.directions` takes `short` for a check.
