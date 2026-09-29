"""The cribas themselves: one function per screen, and the registry the cascade reads."""

import pandas as pd

from core.surface import dedupe
from studies.screening.analysis import decay
from studies.screening.gate.monkey import familia, mono
from studies.screening.gate.redundancy import redundancia


def result(value: pd.Series, passed: pd.Series, note: pd.Series = None) -> pd.DataFrame:
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


def presencia(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Did this strategy survive to the retest databank at all?

    Args:
        data: What inputs.load returned.
        alive: Everything the build databank holds.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is 1 where the retest databank holds it and 0 where it does not. SQX drops
        a strategy from a retest when one of its own red flags fires there — too many
        ambiguous trades, and the rest — and that is a decision SQX already took, not a
        gap in the data. The owner's rule (2026-09-23): out it goes.
    """
    present = alive.isin(data["metrics"].index)
    return result(pd.Series(present.astype(float), index=alive),
                  pd.Series(present, index=alive),
                  pd.Series("SQX no la dejo en el databank OOS", index=alive))


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


def estaticas(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """The floor of static metrics on the out-of-sample period.

    Args:
        data: What inputs.load returned.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml, whose `keep` is a pandas query over the
            joined metrics: every metric appears twice, `[IS]` from the build databank and
            `[OOS]` from the retest one, and the names carry spaces, so backticks.

    Returns:
        `value` is the column named in `value`, and passing is the query.
    """
    frame = data["metrics"].loc[alive]
    passed = pd.Series(False, index=alive)
    passed[frame.query(cfg["keep"]).index] = True
    return result(frame[cfg["value"]], passed, pd.Series("no pasa: " + cfg["keep"], index=alive))


def degradacion(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """How much of the in-sample edge survived, and whether what is left beats its error.

    Args:
        data: What inputs.load returned.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is the retention of the Sharpe ratio. The four numbers come from
        `studies/screening/analysis/decay.py` unchanged — retention, the t of Lo (2002) on the
        out-of-sample stretch, how many of its years were profitable, and the share of its
        profit owed to one quarter — read off the curve `inputs.load` glued together, so
        each half carries the costs its own SQX task charged.
    """
    curves = {name: data["curve"][name].dropna() for name in alive}
    table = decay.table(curves, data["split"], data["end"]).set_index("name").reindex(alive)
    passed = ((table["retention"] >= cfg["min_retention"])
              & (table["t"] >= cfg["min_t"])
              & (table["years_positive"] >= cfg["min_years_positive"])
              & (table["concentration"] <= cfg["max_concentration"]))
    note = ("t=" + table["t"].round(2).astype(str)
            + " anos+=" + table["years_positive"].astype(str)
            + " conc=" + table["concentration"].round(2).astype(str))
    return result(table["retention"], passed.fillna(False), note)


def forma(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Whether the out-of-sample drawdown fits inside what in-sample made one expect.

    Args:
        data: What inputs.load returned.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is the out-of-sample maximum drawdown divided by the in-sample one, both
        in account currency off the same glued curve. A strategy whose worst stretch out of
        sample is many times the worst it ever showed in sample was not tested on it.
    """
    def worst(curve: pd.Series) -> float:
        """Largest peak-to-trough fall of one stretch, in account currency."""
        return float((curve.cummax() - curve).max())

    ratio = {}
    for name in alive:
        curve = data["curve"][name].dropna()
        before, after = curve[:data["split"]][:-1], curve[data["split"]:data["end"]]
        ratio[name] = worst(after) / worst(before)
    value = pd.Series(ratio).reindex(alive)
    return result(value, value <= cfg["max_dd_ratio"],
                  pd.Series("DD OOS / DD IS", index=alive))


SCREENS = {"presencia": presencia, "sanidad": sanidad, "estaticas": estaticas,
           "degradacion": degradacion, "forma": forma, "mono": mono, "familia": familia,
           "redundancia": redundancia}
