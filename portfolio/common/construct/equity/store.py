"""Where a built universe lives on disk, and reading a finished one back."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.datapaths import portfolio_dir

ROOT = portfolio_dir() / "universe"


def folder(pool_hash: str, config_fingerprint: str) -> Path:
    """The cache folder for one pool+config pairing.

    Args:
        pool_hash: `inputs.pool.read()`'s `hash`.
        config_fingerprint: `core.study.config.fingerprint()` of the run's config.

    Returns:
        `ROOT/<pool_hash>-<config_fingerprint>/` — the fingerprint lives in the folder name,
        so a config change can never reuse another config's cache.
    """
    return ROOT / f"{pool_hash}-{config_fingerprint}"


def cached(out: Path) -> bool:
    """Whether a finished build already sits at this folder."""
    return (out / "manifest.json").is_file()


def write(out: Path, daily: pd.DataFrame, monthly: pd.DataFrame, reconcile: pd.DataFrame,
          days_by_firm: dict[str, pd.DataFrame], m5_by_firm: dict[str, dict],
          manifest: dict) -> None:
    """Write every universe file.

    Args:
        out: The cache folder (`folder()`'s result).
        daily, monthly: `matrix.stack`/`matrix.monthly` output over the kept members.
        reconcile: One row per identity x segment (`universe.build`'s contract).
        days_by_firm: `{firm: long-form day table}` (day, identity, closed, float_end,
            low, high, opened, open_end).
        m5_by_firm: `{firm: {"grid_start": int, "n_blocks": int, "block_days": array,
            "low": {identity: float32 array}, "high": {identity: float32 array}}}`.
        manifest: The run's manifest dict.
    """
    out.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out / "daily.parquet")
    monthly.to_parquet(out / "monthly.parquet")
    reconcile.to_csv(out / "reconcile.csv", index=False)
    for firm, frame in days_by_firm.items():
        frame.to_parquet(out / f"days_{firm}.parquet")
    for firm, blob in m5_by_firm.items():
        ids = list(blob["low"].keys())
        low = np.stack([blob["low"][i] for i in ids]) if ids else np.zeros((0, blob["n_blocks"]), np.float32)
        high = np.stack([blob["high"][i] for i in ids]) if ids else np.zeros((0, blob["n_blocks"]), np.float32)
        np.savez_compressed(out / f"m5_{firm}.npz", grid_start=blob["grid_start"],
                             n_blocks=blob["n_blocks"], block_days=blob["block_days"],
                             identities=np.array(ids), low=low, high=high)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")


def load(out: Path) -> dict:
    """Read a finished universe back.

    Args:
        out: The cache folder `universe.build()` returned.

    Returns:
        `daily`, `monthly` (DataFrames), `reconcile` (DataFrame), `days` (`{firm: frame}`),
        `m5` (`{firm: {"grid_start", "n_blocks", "block_days", "low": {id: array},
        "high": {id: array}}}`), `manifest` (dict).
    """
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    days, m5 = {}, {}
    for firm in manifest["clock"]["firms"]:
        days_path = out / f"days_{firm}.parquet"
        if days_path.is_file():
            days[firm] = pd.read_parquet(days_path)
        m5_path = out / f"m5_{firm}.npz"
        if m5_path.is_file():
            with np.load(m5_path, allow_pickle=False) as npz:
                ids = npz["identities"].tolist()
                m5[firm] = {"grid_start": int(npz["grid_start"]), "n_blocks": int(npz["n_blocks"]),
                            "block_days": npz["block_days"],
                            "low": dict(zip(ids, npz["low"])), "high": dict(zip(ids, npz["high"]))}
    return {"daily": pd.read_parquet(out / "daily.parquet"),
            "monthly": pd.read_parquet(out / "monthly.parquet"),
            "reconcile": pd.read_csv(out / "reconcile.csv"),
            "days": days, "m5": m5, "manifest": manifest}
