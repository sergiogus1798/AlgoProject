"""Which variants of a batch enter a composition: no controls, no exact duplicates, two trade floors."""

from typing import Any, cast

import pandas as pd

from core.paths import ROOT
from core.study import config as study_config
from engines.variants import panel
from ledger import gate, thresholds

CONTROLS = ("canary", "inert")
ORIGIN = "origin"


def knobs() -> dict[str, Any]:
    """The `panel` section of engines/variants/config.yaml, `ledger:` references filled."""
    path = ROOT / "engines" / "variants" / "config.yaml"
    return cast(dict[str, Any], thresholds.fill(study_config.load(path, [])))["panel"]


def screen(metrics: pd.DataFrame, comp: tuple[tuple, tuple], k: int, years_oos1: float,
           symbol: str, values: pd.DataFrame | None = None, floors: bool = True,
           step: float = 17, cfg: dict | None = None,
           prints: pd.Series | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The variants one composition of the split measures, and how many each filter removed.

    Order: controls and the inside floor; then the seal (`gate.seal`, raises PermissionError);
    then exact duplicates and the outside floor. None of the four reads `oos2`: duplicates
    compare build and oos1, and the outside floor counts the trades of oos1 (the last segment
    that is not held out), whichever composition is asked (owner, 2026-10-14, D20). A mother
    below a floor warns and that floor is not applied to the batch.

    Args:
        metrics: Contract C3: `variant_id`, `stratum` and the C3 columns of `panel.columns`.
        comp: One of `panel.COMPOSITIONS`.
        k: Live parameters of the mother (frozen and shifted ones do not count).
        years_oos1: Length of the oos1 window in years, what the outside floor is per.
        symbol: The asset, for the seal.
        values: The measure, supplied by the caller (`engines.variants.excess`): index
            `variant_id`, columns `e_is` and `e_oos`. Variants without one are dropped.
        floors: False skips both floors (the sensitivity reading, proposal §2).
        step: The step asking, for the seal.
        cfg: `knobs()` when None.
        prints: `fingerprint.prints` of the batch's build and oos1 trades (never oos2): exact
            duplicates are then equal trade lists. None compares the build and oos1 NetProfit to the cent, which also
            drops distinct variants that happen to total the same.

    Returns:
        (the surviving rows, with `e_is`/`e_oos` when `values` was given; counts), counts =
        {lote, controles, duplicados, suelo_dentro, suelo_fuera, sin_valor, quedan, sin_dato,
        avisos}. `sin_dato` is True under `min_variants`.
    """
    cfg = cfg or knobs()
    cols = panel.columns(comp)
    left, notes = metrics, cast(list[str], [])
    counts: dict[str, Any] = {"lote": len(metrics)}

    def drop(name: str, keep: pd.Series) -> None:
        """Keep the rows of `keep`; note how many the filter removed."""
        nonlocal left
        counts[name] = int((~keep).sum())
        left = cast(pd.DataFrame, left[keep])

    def floor(name: str, column: str, need: float) -> None:
        """Trade floor; skipped, with a warning, when the mother itself is under it."""
        mother = cast(pd.Series, left[left["stratum"] == ORIGIN][column])
        if not floors or (len(mother) and mother.iloc[0] < need):
            counts[name] = 0
            if floors:
                notes.append(f"{name}: la madre ({mother.iloc[0]:.0f}) no llega a {need:.0f}; no se aplica")
            return
        drop(name, cast(pd.Series, left[column] >= need))

    drop("controles", cast(pd.Series, ~left["stratum"].isin(CONTROLS)))
    floor("suelo_dentro", cols["trades_is"], cfg["floor_is_per_param"] * k)
    gate.seal(step, "+".join(comp[1]), symbol)
    first = left.assign(_o=left["stratum"] != ORIGIN).sort_values("_o", kind="stable")
    sig = (first[[f"NetProfit ({s})" for s in panel.SEGMENTS[:2]]].round(2) if prints is None
           else first["variant_id"].map(prints))  # pyright: ignore[reportArgumentType]  # stub types map() without a Series mapper
    drop("duplicados", cast(pd.Series, ~sig.duplicated().reindex(left.index)))
    floor("suelo_fuera", "NumberOfTrades (oos1)", cfg["floor_oos_per_year"] * years_oos1)
    if values is not None:
        left = left.join(values[["e_is", "e_oos"]], on="variant_id")
        drop("sin_valor", cast(pd.Series, left[["e_is", "e_oos"]].notna().all(axis=1)))
    counts |= {"quedan": len(left), "sin_dato": len(left) < cfg["min_variants"], "avisos": notes}
    return left, counts
