"""Level 0 of the gate: in the retest, readable and not a clone, net of oos1, trades per year of the build."""

import pandas as pd

from core.surface import dedupe

# What `run` gives, read off the harvest alone (levels.py).
FACTS = (
    "presencia_passed",
    "sanidad_passed",
    "sanidad_value",
    "estaticas_value",
    "is_trades_per_year",
)
NET = "Net profit [OOS]"  # `estaticas_value`: the retest databank's own net of oos1


def result(
    value: pd.Series, passed: pd.Series, note: pd.Series | None = None
) -> pd.DataFrame:
    """One screen's answer, in the shape the cascade expects.

    Args:
        value: The number this screen measured, per strategy.
        passed: Whether it cleared the screen, same index.
        note: Why it did not, where a number does not say it.

    Returns:
        A frame indexed by identity with `value`, `passed` and `note`.
    """
    frame = pd.DataFrame({"value": value, "passed": passed})
    frame["note"] = "" if note is None else note
    return frame


def sanidad(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Enough out-of-sample trades to measure, and not another strategy's trades again.

    Args:
        data: What inputs.load returned.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is the out-of-sample trade count. Duplicates are found on the trades
        themselves, never on the name or the file hash: two databanks of this project were
        found holding entirely different strategies under one name, and clone pairs with
        identical trades under different hashes turn up in every population looked at. The
        first of a duplicate group survives, so a clone never costs a second monkey run.
    """
    oos = data["trades"][data["trades"]["sample"] == "OOS"]
    oos = oos[oos["identity"].isin(alive)]
    count = oos.groupby("identity", observed=True).size().reindex(alive, fill_value=0)
    clone = dedupe.trade_duplicates(oos, by="identity").reindex(alive, fill_value=False)
    passed = (count >= cfg["min_trades"]) & ~clone
    note = pd.Series("", index=alive)
    note[count < cfg["min_trades"]] = f"menos de {cfg['min_trades']} trades OOS"
    note[clone] = "trades identicos a otra estrategia"
    return result(count.astype(float), passed, note)


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Level 0: in the retest, readable and not a clone, net of oos1, trades per year of the build.

    Args:
        data: The harvest as `inputs.load` gives it, plus `market` (inputs.market).
        alive: Identities still in the cascade: at level 0, everyone the build databank held.
        cfg: The gate's config; reads the `sanidad` row of `screens`.

    Returns:
        One row per identity, one column per fact of `FACTS`, the two `_passed` as 1 / 0.
        A strategy the retest databank does not hold has `presencia_passed` 0 and nothing
        else but its build's `is_trades_per_year`; every paired one has all five, whatever it
        fails, so `sanidad_value` (the oos1 trade count) is there for everybody.
    """
    facts = pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    if not data:  # tests/test_gate_rules.py runs every level on an empty harvest
        return facts
    row = {s["name"]: s for s in cfg["screens"]}
    paired = alive[alive.isin(data["metrics"].index)]
    clean = sanidad(data, paired, row["sanidad"])
    build = data["trades"][data["trades"]["sample"] == "IS"]
    facts["presencia_passed"] = alive.isin(paired).astype(float)
    facts.loc[paired, "sanidad_passed"] = clean["passed"].astype(float)
    facts.loc[paired, "sanidad_value"] = clean["value"]
    facts.loc[paired, "estaticas_value"] = (
        data["metrics"].loc[paired, NET].astype(float)
    )
    facts["is_trades_per_year"] = (
        build.groupby("identity").size().reindex(alive) / data["market"]["years"]["IS"]
    )
    return facts
