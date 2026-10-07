"""Run the gate's levels in order, the step-8 rules of each right after it, each over what the last left."""

import pandas as pd

from pipeline.autopilot import criteria
from studies.screening.gate import inputs, level3ab
from studies.screening.gate.levels import LEVELS

PREFIX = "gate.scorecard."     # a scorecard column as the fact criteria.yaml names


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


def placed(rules: list[dict]) -> dict[int, list[dict]]:
    """Each rule under the position in LEVELS of the last module that gives one of its facts.

    A rule on a fact no level produces (another study's) is the judge's alone: left out.
    """
    at = {PREFIX + fact: i for i, (_, module) in enumerate(LEVELS) for fact in module.FACTS}
    out: dict[int, list[dict]] = {}
    for rule in rules:
        facts = criteria.reads([rule])
        if facts <= at.keys():
            out.setdefault(max(at[f] for f in facts), []).append(rule)
    return out


def label(rule: dict) -> str:
    """A rule in the funnel: its `name`, else the facts it reads and its pass line."""
    facts = sorted(f.removeprefix(PREFIX) for f in criteria.reads([rule]))
    return rule.get("name") or " ".join([*facts, rule.get("pass", "")]).strip()


def said(scores: pd.DataFrame, rule: dict, who: pd.Index) -> dict[str, tuple[str, str]]:
    """One rule over the strategies `who`, by `criteria.judged`: id → (state, `fact=value`)."""
    cols = {f: scores[f.removeprefix(PREFIX)] for f in criteria.reads([rule])}
    medians = pd.Series({f: col[who].median() for f, col in cols.items()})
    return {w: criteria.judged(rule, cols, w, medians) for w in who}


def run(data: dict, cfg: dict, rules: list[dict], start: str = "0",
        say: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The cascade over one harvest: level by level, the step-8 rules of each right after it.

    Args:
        data: What `inputs.staged` returned.
        cfg: What `inputs.config()` returned.
        rules: Step 8's rules, resolved (`criteria.resolved`): the judge's own.
        start: The level to start at. Past "0" the scorecard, the funnel and the per-trade
            table of an earlier run are read back from `data["out"]` and the levels before
            it are kept as they were.
        say: Print the funnel line by line while it runs.

    Returns:
        The scorecard — one row per identity, one column per fact, `cayo_nivel` and
        `cayo_regla` (the level it fell at and the rule, as `fact=value`; empty for whoever
        stands), `survives`, and `limbo`: for whoever stands, the rules that left it in
        limbo, "; "-joined ("" = it passes them all) — and the funnel, one row per level and
        rule in the order judged: `level`, `screen` (the rule), `kind` (hard), `entered`,
        `passed` (entered - died: a limbo goes on), `limbo` and `died`. Both are written
        into `data["out"]` after every level.

        A rule is judged by `criteria.judged`, as the judge will; a strategy leaves at its
        first Fail. With `cascade.on` it is not handed to the next level, so its later
        facts stay empty; without it every level runs on everybody and the fall is only
        recorded — same facts, same verdict.
    """
    out, order = data["out"], [level for level, _ in LEVELS]
    first, rules_at = order.index(start), placed(rules)
    if first:
        kept = [fact for _, module in LEVELS[:first] for fact in module.FACTS]
        scores = pd.read_parquet(out / "scorecard.parquet")[
            ["strategy", "strategy_build", "cayo_nivel", "cayo_regla", *kept]]
        scores.loc[scores["cayo_nivel"].isin(order[first:]), ["cayo_nivel", "cayo_regla"]] = None
        funnel = pd.read_csv(out / "funnel.csv")
        funnel = funnel[funnel["level"].astype(str).isin(order[:first])].to_dict("records")
        data["oos"] = pd.read_parquet(out / "operaciones.parquet")
    else:
        scores, funnel = population(data).assign(cayo_nivel=None, cayo_regla=None), []
    standing = scores.index[scores["cayo_nivel"].isna()]
    for i, (level, module) in enumerate(LEVELS[first:], first):
        alive = standing if cfg["cascade"]["on"] else scores.index
        if module is level3ab:      # R6's build P/L, repriced only for who got this far
            data["build"] = inputs.build_pnl(data, alive)
        got = module.run(data if len(alive) else {}, alive, cfg)
        for fact in got:            # joined on identity: a level may return more than `alive`
            scores.loc[got.index, fact] = got[fact]
        for rule in rules_at.get(i, []):
            got = said(scores, rule, standing)
            fell = [who for who, (state, _) in got.items() if state == "fail"]
            scores.loc[fell, "cayo_nivel"] = level
            scores.loc[fell, "cayo_regla"] = [got[who][1] for who in fell]
            funnel.append({"level": level, "screen": label(rule), "kind": "hard",
                           "entered": len(standing), "passed": len(standing) - len(fell),
                           "limbo": sum(state == "limbo" for state, _ in got.values()),
                           "died": len(fell)})
            if say:
                print(f"nivel {level:3s} {funnel[-1]['screen']:44s} entran {len(standing):5d} "
                      f"limbo {funnel[-1]['limbo']:5d} caen {len(fell):5d}", flush=True)
            standing = standing.difference(fell)
        scores.to_parquet(out / "scorecard.parquet", compression="zstd")
        pd.DataFrame(funnel).to_csv(out / "funnel.csv", index=False)
    doubts = {who: [] for who in standing}
    for rule in (rule for at in sorted(rules_at) for rule in rules_at[at]):
        for who, (state, text) in said(scores, rule, standing).items():
            doubts[who] += [text] if state == "limbo" else []
    scores["survives"] = scores["cayo_nivel"].isna()
    scores["limbo"] = pd.Series({who: "; ".join(texts) for who, texts in doubts.items()},
                                dtype=object)
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
        `strategy`, `verdict`, `identity`, `reason`. DESCARTAR for whoever fell at a rule,
        MANTENER for the rest, limbo included; the reason names the level and the rule with
        the number that failed it, so a cut can be read a month later without rerunning.
    """
    named = scores[scores[side].notna()]
    reason = ["" if alive else f"nivel {level}: {rule}" for alive, level, rule in
              zip(named["survives"], named["cayo_nivel"], named["cayo_regla"])]
    return pd.DataFrame({"strategy": named[side].values,
                         "verdict": named["survives"].map({True: "MANTENER",
                                                           False: "DESCARTAR"}).values,
                         "identity": named.index, "reason": reason})
