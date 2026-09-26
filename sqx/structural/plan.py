"""Decide one mother's structural batch: the identity rebuild, one ablation per entry condition, the inversion."""

from pathlib import Path

import pandas as pd

from sqx.structural import logic
from sqx.variants.build import rewrite

# Identity, ablation, inversion. The letter is in the id so a file name says what it is.
KIND = {"identity": "O", "ablation": "A", "inversion": "I"}


def rows(mother: Path, m: int) -> list[dict]:
    """Every file one mother's batch holds, and what each must contain once written.

    Args:
        mother: A `.sqx` the strategy name is the stem of.
        m: The mother's position in the batch, for the id.

    Returns:
        One dict per file: `variant_id` (`S00O00`, `S00A01`…), `strategy`, `mother`,
        `kind`, the ablated `signal`, `index` and `block` (empty otherwise), and what the
        read-back must find — `expect_blocks`, the entry blocks left in file order joined
        by "+", and `expect_direction`, the entry orders' sides joined the same way.
        A signal with a single condition gets no ablation: `logic.ablate` refuses it.
    """
    portfolio = rewrite.members(mother)[rewrite.PORTFOLIO].decode("utf-8")
    found = logic.conditions(portfolio)
    sides = logic.direction(portfolio)
    base = {"strategy": mother.stem, "mother": str(mother), "signal": "", "index": -1,
            "block": ""}

    def keys(conds: list[dict]) -> str:
        """The entry blocks as the read-back spells them."""
        return "+".join(f"{c['signal']}:{c['block']}" for c in conds)

    def signed(values: list[int]) -> str:
        """The entry orders' directions as the read-back spells them."""
        return "+".join(str(v) for v in values)

    out = [base | {"variant_id": f"S{m:02d}O00", "kind": "identity",
                   "expect_blocks": keys(found), "expect_direction": signed(sides)}]
    per_signal = pd.Series([c["signal"] for c in found]).value_counts()
    for k, c in enumerate(found, 1):
        if per_signal[c["signal"]] < 2 or not c["operator"]:
            continue
        left = [d for d in found if d is not c]
        out.append(base | {"variant_id": f"S{m:02d}A{k:02d}", "kind": "ablation",
                           "signal": c["signal"], "index": c["index"], "block": c["block"],
                           "expect_blocks": keys(left), "expect_direction": signed(sides)})
    out.append(base | {"variant_id": f"S{m:02d}I00", "kind": "inversion",
                       "expect_blocks": keys(found),
                       "expect_direction": signed([-s for s in sides])})
    return out


def build(mothers: list[Path]) -> pd.DataFrame:
    """The whole batch's plan.

    Args:
        mothers: The `.sqx` of the strategies to test, one batch for all of them.

    Returns:
        One row per file to write, as `rows` describes them.
    """
    return pd.DataFrame([r for m, mother in enumerate(mothers) for r in rows(mother, m)])
