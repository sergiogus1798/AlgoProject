"""Run the screens in the order the config gives, each one over what the last one left."""

import pandas as pd

from studies.screening.gate.screens import SCREENS


def population(data: dict) -> pd.DataFrame:
    """Everyone the build databank held, named on both sides.

    Args:
        data: What inputs.load returned.

    Returns:
        A frame indexed by identity with `strategy` (its name in the retest databank) and
        `strategy_build` (its name in the build one). They differ whenever SQX renamed on
        collision, which is why nothing here is keyed on a name.
    """
    matched = data["metrics"][["strategy", "strategy_build"]]
    missing = data["missing"].set_index("identity").reindex(columns=["strategy_build"])
    return pd.concat([matched, missing.assign(strategy=None)])


def run(data: dict, cfg: dict, say: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The whole cascade over one harvest.

    Args:
        data: What inputs.load returned, plus `bars` and `null_cfg`.
        cfg: What inputs.config() returned.
        say: Print the funnel line by line while it runs.

    Returns:
        The scorecard — one row per identity, three columns per screen plus `died_at` —
        and the funnel, one row per screen with how many entered, passed and died.

        A strategy that dies in a hard screen is not handed to the next one, so its later
        columns stay null. That is the point: the null says the monkey was never spent on
        it, which is what makes the expensive screens affordable.
    """
    scores = population(data)
    scores["died_at"] = None
    alive, funnel = scores.index, []
    for row in cfg["screens"]:
        name, hard = row["name"], row["kind"] == "hard"
        data["scores"] = scores
        out = SCREENS[name](data, alive, row)
        for column in ("value", "passed", "note", "p"):
            if column in out:
                scores.loc[alive, f"{name}_{column}"] = out[column]
        killed = out.index[~out["passed"].astype(bool)] if hard else pd.Index([])
        scores.loc[killed, "died_at"] = name
        funnel.append({"screen": name, "kind": row["kind"], "entered": len(alive),
                       "passed": int(out["passed"].astype(bool).sum()), "died": len(killed)})
        if say:
            print(f"{name:14s} {row['kind']:5s} entran {len(alive):5d} "
                  f"pasan {funnel[-1]['passed']:5d} mueren {len(killed):5d}")
        alive = alive.difference(killed) if hard else alive
    scores["survives"] = scores["died_at"].isna()
    return scores, pd.DataFrame(funnel)


def verdict(scores: pd.DataFrame, side: str) -> pd.DataFrame:
    """The scorecard as the CSV `sqx.curate.apply_verdict` already knows how to apply.

    Args:
        scores: What run() returned.
        side: "strategy" to write it against the retest databank, "strategy_build" against
            the build one. A verdict names one databank's strategies, because that is what
            apply_verdict checks the files of — and a strategy SQX dropped from the retest
            has no name there at all, so only the build side can carry it.

    Returns:
        `strategy`, `verdict`, `identity`, `reason`. DESCARTAR for anything that died in a
        hard screen, MANTENER for the rest; the reason names the screen and the number that
        killed it, so a cut can be read a month later without rerunning anything.
    """
    named = scores[scores[side].notna()]
    reason = named.apply(
        lambda r: "" if r["survives"]
        else f"{r['died_at']} = {r[r['died_at'] + '_value']:.4g} | {r[r['died_at'] + '_note']}",
        axis=1)
    return pd.DataFrame({"strategy": named[side].values,
                         "verdict": named["survives"].map({True: "MANTENER",
                                                           False: "DESCARTAR"}).values,
                         "identity": named.index, "reason": reason.values})
