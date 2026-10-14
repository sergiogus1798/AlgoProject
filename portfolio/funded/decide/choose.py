"""Encargo 33 §3.5 as a rule: which rows of the bank tables may be bought, why the others may not, and the one chosen."""

from typing import Any, TypedDict

# The gates, in the order they are asked; the first that fails is the row's reason (Spanish, the owner reads it).
GATES = (
    ("own", "cartera de otro plan ({source_plan})"),
    ("verdict", "la cartera no tiene veredicto favorable: {verdict_label}"),
    (
        "edge",
        "el edge fuera de muestra de la cartera no es positivo ({edge_oos:+.4f} por día con cierre)",
    ),
    (
        "budget",
        "el p90 del desembolso antes del primer cobro ({outlay_p90:.0f} $) supera la caja ({budget_usd:.0f} $)",
    ),
    ("positive", "el valor esperado con h = {h:.0%} no es positivo ({ev:+.1f} $)"),
    (
        "monkey",
        "el valor esperado no supera al mono ({ev:+.1f} $ contra {ev_monkey:+.1f} $)",
    ),
)


class Choice(TypedDict):
    """Every candidate row, the one chosen, the runner-up and whether they are a statistical tie."""

    rows: list[dict]
    chosen: dict | None
    runner_up: dict | None
    tie: bool


def facts(row: dict, own: bool, source: dict, h: float) -> dict[str, Any]:
    """A table row with what the gates read beside it."""
    return {
        **row,
        "h": h,
        "is_own": own,
        "source_plan": source.get("plan"),
        "verdict_pass": source.get("verdict_pass"),
        "verdict_label": source.get("verdict_label"),
        "edge_oos": source.get("edge_oos"),
        "members": source.get("members"),
        "run": source.get("run"),
    }


def gate(row: dict, ignore_verdict: bool) -> str | None:
    """The first gate a row fails, as its Spanish reason; `None` = it may be bought."""
    passed = {
        "own": row["is_own"],
        "verdict": ignore_verdict or row["verdict_pass"] is True,
        "edge": row["edge_oos"] is not None and row["edge_oos"] > 0,
        "budget": row["outlay_p90"] <= row["budget_usd"] + 1e-9,
        "positive": row["ev"] > 0,
        "monkey": row["ev"] > row["ev_monkey"],
    }
    for name, text in GATES:
        if not passed[name]:
            return text.format(**row)
    return None


def ranks(rows: list[dict], hs: list[float]) -> None:
    """Write each row's position (1 = best) at every haircut into `rank_h<h>` — how far the order moves with h."""
    for h in hs:
        key = f"ev_h{round(100 * h)}"
        for i, r in enumerate(sorted(rows, key=lambda r: -r[key])):
            r[f"rank_h{round(100 * h)}"] = i + 1


def decide(per_plan: dict[str, dict], owner: dict, ignore_verdict: bool) -> Choice:
    """Judge every row, pick the highest EV at the deciding haircut among the rows that pass every gate.

    Args:
        per_plan: `tables.per_plan()`'s dict.
        owner: The `owner` section the tables were simulated under (one for all of them).
        ignore_verdict: Skip the verdict gate — a wiring test, never a decision.

    Returns:
        `rows` (every row with `reason`, `None` when eligible, and `rank_h*`; best EV first),
        `chosen` (a row or `None`), `runner_up` (the next eligible row or `None`) and
        `tie` (True when the two are closer than twice the Monte Carlo error of their gap).
    """
    hs, h = owner["haircuts"], owner["haircut_decides"]
    rows = [
        facts(
            r, entry["own"], entry["table"]["manifest"]["paths"].get("source") or {}, h
        )
        for entry in per_plan.values()
        for r in entry["rows"]
    ]
    for r in rows:
        r["reason"] = gate(r, ignore_verdict)
    ranks(rows, hs)
    rows.sort(key=lambda r: -r["ev"])
    eligible = [r for r in rows if r["reason"] is None]
    chosen = eligible[0] if eligible else None
    runner_up = eligible[1] if len(eligible) > 1 else None
    tie = (
        runner_up is not None
        and chosen is not None
        and (
            chosen["ev"] - runner_up["ev"]
            < 2 * (chosen["ev_se"] ** 2 + runner_up["ev_se"] ** 2) ** 0.5
        )
    )
    return {"rows": rows, "chosen": chosen, "runner_up": runner_up, "tie": tie}
