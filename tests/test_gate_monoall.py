"""L5 A: monoall hands EVERY harvested strategy to levels 1a and 3c, not the cascade's survivors."""

import pandas as pd

from studies.screening.gate import monoall


def test_everyone_reaches_the_monkey(monkeypatch: object, tmp_path: object) -> None:
    """Three strategies in the harvest: three rows of z_mono, whatever level 0 would say."""
    metrics = pd.DataFrame(index=pd.Index(["a", "b", "c"]))
    seen = []
    monkeypatch.setattr(monoall, "latest_harvest", lambda p, d: tmp_path)
    monkeypatch.setattr(monoall, "report_dir", lambda p, d, day: tmp_path)
    monkeypatch.setattr(monoall.inputs, "load", lambda f: {"metrics": metrics})
    monkeypatch.setattr(monoall.inputs, "timeframe", lambda m, c, o: "H1")
    monkeypatch.setattr(monoall.inputs, "staged", lambda h, f, t, o: dict(h))

    def level(fact: str) -> object:
        """A fake level that records who it was handed."""

        def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
            """Record `alive`, give one fact for each."""
            seen.append((fact, list(alive)))
            return pd.DataFrame({fact: 1.0}, index=alive)

        return run

    monkeypatch.setattr(monoall.level3c, "run", level("z_mono"))
    monkeypatch.setattr(monoall.level1a, "run", level("drift_excess_t"))
    got = monoall.everyone("Test_x", "X_M1")
    abc = ["a", "b", "c"]
    assert (
        seen == [("drift_excess_t", abc), ("z_mono", abc)]
        and got["z_mono"].notna().sum() == 3
    )
    assert (tmp_path / "gate-all" / "mono_all.parquet").exists()
