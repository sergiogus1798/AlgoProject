"""Turn the cross-market results into crossmarket.md. Pure text, computes nothing."""

import argparse

import pandas as pd

from strategies.crossmarket import inference, trade_models


def why_dropped(g: pd.DataFrame) -> str:
    """Which guard removed a market's rows from the vote.

    Args:
        g: One market's rows, none of them testable.

    Returns:
        A phrase naming the guard and the number that tripped it. A market that leaves the
        vote silently is indistinguishable from one that was never run, so the reason is
        reported with the same prominence as a p-value would have been.
    """
    thin = int((g["trades"] < inference.MIN_TRADES).sum())
    if thin:
        return f"{thin} of {len(g)} under {inference.MIN_TRADES} trades"
    return (f"only {g['on_bar_open'].median():.1%} of entries land on a bar open — the rest are "
            f"pending orders filled inside a bar, which no model can reproduce")


def per_market(rows: pd.DataFrame, alpha: float) -> list[str]:
    """One line per market: how many strategies beat their null there.

    Args:
        rows: Every (strategy, market) row.
        alpha: The per-market level a row has to clear.

    Returns:
        Markdown table lines, followed by a line per market that dropped out saying why. A
        market that silently left every vote cannot go unnoticed.
    """
    out = ["| market | strategies | testable | median trades | beat null | median p "
           "| median edge R |", "|---|---|---|---|---|---|---|"]
    reasons = []
    for market, g in rows.groupby("market", sort=False):
        ok = g[g["testable"]]
        cells = [f"`{market}`", str(len(g)), str(len(ok)), f"{g['trades'].median():.0f}"]
        cells += ["—", "—", "—"] if ok.empty else [
            str(int((ok["p"] <= alpha).sum())),
            f"{ok['p'].median():.3f}", f"{ok['edge_r'].median():+.3f}"]
        out.append("| " + " | ".join(cells) + " |")
        if ok.empty:
            reasons.append(f"- **`{market}` does not vote**: {why_dropped(g)}. Its p-values are "
                           f"in `by_market.csv` and are not part of any verdict.")
    return out + ([""] + reasons if reasons else [])


def per_model(rows: pd.DataFrame, models: list[str], alpha: float) -> list[str]:
    """One line per model: what it randomises, and how many rows it passes.

    Args:
        rows: Every (strategy, market) row.
        models: The models that were run, the verdict's first.
        alpha: The per-market level.

    Returns:
        Markdown table lines. Models disagreeing is the point of running more than one: a
        result that only survives the weaker models depended on an assumption, not on timing.
    """
    ok = rows[rows["testable"]]
    if ok.empty:
        return ["No row survived the guards, so no model was given anything to judge. What each "
                "would have randomised, for the p-values sitting unused in `by_market.csv`:", "",
                *[f"- `{m}` — {trade_models.RANDOMISES[m]}" for m in models]]
    out = ["| model | randomises | rows at p ≤ level | median p |", "|---|---|---|---|"]
    for i, model in enumerate(models):
        column = "p" if i == 0 else f"p_{model}"
        mark = " **(verdict)**" if i == 0 else ""
        out.append(f"| `{model}`{mark} | {trade_models.RANDOMISES[model]} | "
                   f"{int((ok[column] <= alpha).sum())} of {len(ok)} | {ok[column].median():.3f} |")
    return out


def render(a: argparse.Namespace, spec: dict, rows: pd.DataFrame, calls: pd.DataFrame,
           luck: dict) -> str:
    """The written report.

    Args:
        a: Parsed command line.
        spec: The asset's block of markets.yaml.
        rows: Every (strategy, market) row.
        calls: One row per strategy, from inference.table().
        luck: Expected false passes, from inference.false_passes().

    Returns:
        Markdown. It states what the study does not show as prominently as what it does,
        because a cross-market p-value reads like proof of edge and is not one.
    """
    alpha = 0.05
    counts = calls.verdict.value_counts().to_dict()
    entry_only = int((calls.family == "entry").sum())
    lines = [
        f"# Cross-market random-entry study — {a.project} / {a.databank}", "",
        f"Base asset `{a.asset}`, {len(spec['additional'])} additional markets, {a.draws} random "
        f"runs per model, exported {a.export}. Smallest p observable: "
        f"{1 / (1 + a.draws):.5f}.", "",
        "## Verdict", "",
        "| verdict | strategies |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in counts.items()], "",
        f"Of these, {entry_only} are pure entry tests: every exit is the fixed bar cap, so the "
        f"holds the models reuse owed nothing to the price path. The remaining "
        f"{len(calls) - entry_only} exit on a rule, so their holds encode information no model "
        "here reproduces — for those the result is a joint test of entry **and** exit, and it "
        "must not be reported as entry timing.", "",
        "## Per market", "", *per_market(rows, alpha), "",
        "## Per model", "", *per_model(rows, a.models, alpha), "",
        "The verdict uses the first model because it is the only one that randomises exactly one "
        "thing. Where a strategy passes under a later model but not under the first, what was "
        "found is a property of that model's extra assumption, not of the strategy.", "",
        "## How many of these are luck", "",
        (f"**The vote could not be held.** It needs {inference.MIN_MARKETS} markets carrying a "
         f"usable result and this study had {int(calls.markets.median())}, so every strategy is "
         f"NO EVALUABLE regardless of its p-values. The figures below are what the rule would "
         f"have been worth. " if int(calls.markets.median()) < inference.MIN_MARKETS else "")
        + f"The rule is a strict majority of markets at p ≤ {alpha}. Over {len(calls)} strategies "
        f"voted on about {int(calls.markets.median())} markets, that lets through "
        f"**{luck['independent']:.2f}** strategies by chance if the markets were independent, "
        f"and **{luck['correlated']:.1f}** if their outcomes correlate at 0.5 — which is the "
        "figure to use. Eight markets driven by one dollar-and-risk factor behave like about "
        "two, so the survivors of a lucky draw will look like a coherent family rather than "
        "like noise. Compare that number against the MANTENER count before calling anything a "
        "discovery.", "",
        "## What this does not say", "",
        "- It does not detect overfitting to the base asset. It detects whether the timing "
        "transfers to markets the strategies never saw.", "",
        "- It does not validate the equity curve. The statistic is size-free by design, so it says "
        "the entries land on better-than-random bars, not that the money management works.", "",
        "- A market where the strategy fails is not a failure of the test. It maps where the "
        "edge lives, which is the input to the edge-driver study.", "",
    ]
    return "\n".join(lines) + "\n"
