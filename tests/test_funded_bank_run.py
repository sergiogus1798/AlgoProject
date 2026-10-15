"""Known-answer tests for the bank run: the whole run on a synthetic path set, the ledger row, the refusal."""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import funding_planted  # noqa: E402

funding_planted.plant()  # before anything imports core.paths

import ledger.study as study
from portfolio.funded.rules import catalog
from portfolio.funded.sim import inputs, plans, report, run, table

FAILED = []
NEVER = 10**9


def check(name: str, ok: bool, detail: object = "") -> None:
    """Print one result and remember its name if it failed."""
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if not ok else ""))
    if not ok:
        FAILED.append(name)


# 4. the whole run on a synthetic path set, in a temp folder; then the same counted in a temp ledger
rng = np.random.default_rng(4)
n, horizon = 300, 400
trade = rng.random((n, horizon)) < 0.6
closed = rng.normal(0.10, 1.0, (n, horizon)) * trade
paths = {
    "closed": closed,
    "float_end": np.zeros((n, horizon)),
    "low": np.minimum(closed, 0),
    "high": np.maximum(closed, 0),
    "opened": trade.astype(np.int32),
}
meta = {"unit_risk": 1.0, "days_per_year": 260.0, "synthetic": True, "label": "test"}
SET = [
    "owner.eurusd=1.2",
    "owner.rebuy=[same_plan, none]",
    "owner.haircuts=[0, 0.5, 1]",
    "owner.haircut_decides=0.5",
    "owner.payout_cushion=0.02",
    "owner.tax_rate=0",
    "owner.payout_fee=0",
    "owner.p_payout_denied=0",
    "owner.p_firm_closes_year=0",
    "gaps.hantec_fee_refund=false",
    "gaps.hantec_endurance_payout_days=14",
    "gaps.hantec_express_floor_after_payout=initial",
    "gaps.ftmo_1step_floor_after_payout=stays",
    "risk.challenge=[0.005, 0.01]",
    "risk.funded=[0.005, 0.01]",
]
cfg = inputs.load(SET)
check(
    "a complete policy is not refused",
    inputs.refuse(cfg) == [] and table.variants(cfg)[1] == [],
)
universe = catalog.plans(10000, "USD")
with tempfile.TemporaryDirectory() as tmp:
    done = run.run(paths, meta, cfg, Path(tmp) / "a", seed=1)
    frame = pd.read_parquet(Path(tmp) / "a" / "table.parquet")
    manifest = json.loads((Path(tmp) / "a" / "manifest.json").read_text())
    check(
        "one row per universe plan and re-buy policy, ordered by EV at the deciding haircut",
        sorted(frame["plan"]) == sorted(universe * 2)
        and frame["ev"].is_monotonic_decreasing
        and sorted(set(frame["rebuy"])) == ["none", "same_plan"],
        frame["plan"].tolist(),
    )
    one_policy = sum(
        len(plans.risk_grid(v, [0.005, 0.01], [0.005, 0.01])) for v in done["variants"]
    )
    expected = 2 * one_policy
    single = run.run(
        paths, meta, inputs.load([*SET, "owner.rebuy=[none]"]), Path(tmp) / "n", seed=1
    )
    check(
        "the re-buy policy is a searched dimension: both policies score twice what one does",
        len(single["search"]) == one_policy and len(done["search"]) == expected,
        (len(single["search"]), expected),
    )
    lone = frame[frame["rebuy"] == "none"]
    check(
        "rebuy = none: one purchase per draw, the fees are the price, and the worst draw loses exactly the price",
        np.allclose(lone["purchases"], 1)
        and np.allclose(lone["fees"], lone["price_usd"])
        and np.allclose(lone["net_min"], -lone["price_usd"]),
        lone[["plan", "net_min", "price_usd"]],
    )
    check(
        "h = 1 is the monkey at the risk chosen at the deciding h: never above the monkey at its best risk",
        bool((frame["ev_h100"] <= frame["ev_monkey"] + 1e-9).all()),
    )
    check(
        "the printed table puts the two policies side by side",
        any(
            "lado a lado" in line and "same_plan" in line and "none" in line
            for line in report.lines(done, cfg["owner"])
        ),
    )
    check(
        "every configuration scored is in search.parquet",
        len(pd.read_parquet(Path(tmp) / "a" / "search.parquet"))
        == expected
        == manifest["configurations"],
        expected,
    )
    check(
        "the EUR/USD rate, the seed and the path set are written beside the result; synthetic = no ledger row",
        (
            manifest["eurusd"],
            manifest["seed"],
            manifest["ledger"],
            manifest["paths"]["synthetic"],
        )
        == (1.2, 1, None, True),
    )
    row = frame.iloc[0]
    check(
        "the row's EV at the deciding h is its ev_h50, and the advantage is EV minus the monkey's",
        row["ev"] == row["ev_h50"]
        and abs(row["advantage"] - (row["ev"] - row["ev_monkey"])) < 1e-9,
    )
    check(
        "with a planted edge the curve falls as h grows, on every plan",
        bool(
            (frame["ev_h0"] > frame["ev_h50"]).all()
            and (frame["ev_h50"] > frame["ev_h100"]).all()
        ),
    )
    addons = pd.DataFrame(done["addons"]).merge(
        frame[["plan", "rebuy", "ev"]], on=["plan", "rebuy"], suffixes=("", "_base")
    )
    check(
        "an add-on's delta is its EV minus the bare plan's",
        np.allclose(addons["delta_ev"], addons["ev"] - addons["ev_base"]),
    )
    check(
        "the result is a valid study-contract dict carrying every flag as a warning",
        done["result"]["module"] == "portfolio.funded.sim"
        and len(done["result"]["warnings"]) == len(done["flags"]),
    )
    again = run.run(paths, meta, cfg, Path(tmp) / "b", seed=1)
    check(
        "the same seed and paths give the same table",
        pd.DataFrame(again["rows"]).equals(pd.DataFrame(done["rows"])),
    )
    real_path = study.path
    study.path = lambda s: Path(tmp) / f"{s}.jsonl"
    try:
        run.run(
            paths,
            {**meta, "synthetic": False},
            cfg,
            Path(tmp) / "c",
            seed=1,
            ledger={
                "study": "PORTFOLIO_test_construct",
                "symbol": "TESTSYM",
                "segment": "oos2",
            },
        )
        rows = study.read("PORTFOLIO_test_construct")
    finally:
        study.path = real_path
    check(
        "a real path set writes one ledger row counting every configuration (temp ledger)",
        len(rows) == 1
        and rows.iloc[0]["n_scored"] == expected
        and rows.iloc[0]["n_out"] == 2 * len(universe)
        and rows.iloc[0]["score_unit"] == "ev_bank_usd",
        rows.to_dict("records"),
    )

# 5. the command refuses, naming the input, when the owner's policy is missing
for missing in (
    "owner.eurusd",
    "owner.tax_rate",
    "owner.payout_cushion",
    "gaps.hantec_express_floor_after_payout",
):
    # the committed config now holds some of these (2026-10-14) and an override cannot
    # null a typed knob: blank the one under test in the loaded config, as run.main reads it
    cfg = inputs.load(SET)
    section, key = missing.split(".")
    cfg[section][key] = None
    lines = inputs.refuse(cfg) + table.variants(cfg)[1]
    check(
        f"without {missing} the command refuses and names it",
        any(missing in line or key in line for line in lines),
        lines,
    )
bad = inputs.load(
    [s_.replace("haircut_decides=0.5", "haircut_decides=0.4") for s_ in SET]
)
check(
    "a deciding haircut outside the list is refused",
    any("haircut_decides" in line for line in inputs.refuse(bad)),
)
try:
    inputs.load([*SET, "owner.rebuy=same_plan"])
    check("owner.rebuy as a single value is refused", False)
except ValueError:
    check("owner.rebuy as a single value is refused", True)
for value in ("[same_plan, sometimes]", "[same_plan, same_plan]", "[]"):
    check(
        f"owner.rebuy = {value} is refused: it is the list of policies compared",
        any(
            "owner.rebuy" in line
            for line in inputs.refuse(inputs.load([*SET, f"owner.rebuy={value}"]))
        ),
    )
committed = inputs.load([])["owner"]
answered = {
    "budget_eur": 1000,
    "eurusd": 1.12,
    "rebuy": ["same_plan", "none"],
    "haircuts": [0, 0.25, 0.5, 0.75, 1],
    "haircut_decides": 0.5,
    "payout_cushion": 0.0,
    "payout_fee": 0.02,
    "p_firm_closes_year": 0.05,
}
answered_gaps = {
    "hantec_fee_refund": False,
    "hantec_endurance_payout_days": 14,
    "hantec_express_floor_after_payout": "initial",
    "ftmo_1step_floor_after_payout": "stays",
}
check(
    "the committed config holds the owner's answers of 2026-09-29, 2026-10-05 and 2026-10-14 and nothing else: tax_rate and p_payout_denied stay null",
    committed == {**dict.fromkeys(committed), **answered}
    and inputs.load([])["gaps"] == answered_gaps,
    committed,
)

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":
    sys.exit(1 if FAILED else 0)
