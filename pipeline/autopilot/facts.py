"""Every number a judging step's studies wrote, one row per strategy and key."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from studies.transfer.crossTF.verdict import MEANS
from ui.daemon.workflow import sources
from ui.daemon.workflow.steps import STEPS

BY_N = {s["n"]: s for s in STEPS}
# A scaled sibling's name ends in its target timeframe (`sqx.projects.crosstfload.SIBLING`).
TARGET = re.compile(r"_Scaled([MHD]\d+)(\(\d+\))?$")
COLUMNS = ["study", "strategy", "identity", "key", "value"]
BOOLS = {"True": 1.0, "False": 0.0}
# The per-strategy CSVs a result folder may hold, read column by column as `<stem>_csv.<col>`:
# a study's own verdict, and the monkey's ladder (`nulls.csv`, one row per strategy × market).
CSVS = ("verdict.csv", "nulls.csv")
# Columns of those CSVs that name the row, never a fact.
NAMES = {"strategy", "identity", "verdict", "verdict_state", "mother", "market"}


def slug(text: str) -> str:
    """A title as a key part: accents dropped, lower case, runs of anything else as one `_`."""
    plain = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-z]+", "_", plain.lower()).strip("_")


def number(value: object) -> float | None:
    """A cell as a float, or None when it is not a number (text, None, NaN).

    A CSV cell comes as text: a number in it is read, and "True"/"False" are 1 and 0.
    """
    if isinstance(value, str):
        value = BOOLS.get(value, value)
        try:
            value = float(value)
        except ValueError:
            return None
    if not isinstance(value, (bool, int, float, np.number, np.bool_)):
        return None
    return float(value) if value == value else None


def block(b: dict) -> list[tuple[str, float | None]]:
    """The numbers one contract block carries, keyed under its title.

    A distribution gives its real value, median, p and percentiles; a table every numeric
    cell as `<title>.<first cell of the row>.<column>`; a verdict `verdict_pass` (1 when its
    state is pass: a reading such as profitShape's `spread`) and each part's value. The other
    kinds are pictures of series and give nothing a rule can test.
    """
    t = slug(b.get("title") or b.get("label") or b["kind"])
    if b["kind"] == "distribution":
        got = [(f"{t}.real", b.get("real")), (f"{t}.median", b.get("median")),
               (f"{t}.p", b.get("p"))]
        return got + [(f"{t}.p{q}", v) for q, v in (b.get("percentiles") or {}).items()]
    if b["kind"] == "table":
        return [(f"{t}.{slug(row[0])}.{slug(col)}", cell) for row in b["rows"]
                for col, cell in zip(b["columns"][1:], row[1:])]
    if b["kind"] == "verdict":
        return [("verdict_pass", b["state"] == "pass")] + [
            (f"{t}.{slug(p['label'])}", p.get("value")) for p in b.get("parts", [])]
    return []


def flatten(result: dict) -> list[tuple[str, float | None]]:
    """One strategy's contract result as (key, value) pairs.

    Returns:
        `summary.*`, `verdict.pass` (1 when its own verdict state is pass), `verdict.score`,
        `verdict.<part>`, and every block of every tab, the default selector combination
        only. Values that are not numbers come back as None and are dropped by the caller.
    """
    out = [(f"summary.{slug(k)}", v) for k, v in (result.get("summary") or {}).items()]
    v = result.get("verdict")
    if v:
        out += [("verdict.pass", v["state"] == "pass"), ("verdict.score", v.get("score"))]
        out += [(f"verdict.{slug(p['label'])}", p.get("value")) for p in v.get("parts", [])]
    for tab in result.get("tabs", []):
        for b in tab["blocks"]:
            if "select" in b and any(s["default"] != b["select"].get(s["key"])
                                     for s in tab.get("selectors", [])):
                continue
            out += [(f"{slug(tab['name'])}.{k}", x) for k, x in block(b)]
    return out


def per_strategy(study: str, df: pd.DataFrame, prefix: str, skip: set[str]) -> list[dict]:
    """Every column of a one-row-per-strategy table that holds a number, as `<prefix>.<col>`.

    A column with any number in it is read; its text cells (and a bool column's None, where a
    cascade never reached the strategy) are dropped by the caller as not numbers.
    """
    ids = df["identity"].fillna("") if "identity" in df.columns else pd.Series("", index=df.index)
    rows = []
    for col in df.columns.difference(skip, sort=False):
        values = [number(x) for x in df[col]]
        if any(v is not None for v in values):
            rows += [{"study": study, "strategy": s, "identity": i,
                      "key": f"{prefix}.{slug(col)}", "value": v}
                     for s, i, v in zip(df["strategy"], ids, values)]
    return rows


def from_folder(study: str, folder: Path) -> list[dict]:
    """The rows of one result folder: its per-strategy JSONs, its one-row-per-strategy parquets
    and CSVs (`CSVS`), `verdict_csv.drop` (1 when the study itself said DESCARTAR) and, where
    the CSV has a `verdict_state`, `verdict_csv.state_pass` (1 when it is pass).

    A parquet indexed by identity (the gate's scorecard) gets it as a column, so its facts join
    the databank by identity like every other study's. Rows without a strategy name (the
    gate's build strategies SQX never put in the OOS databank) are not in any databank judged.
    """
    rows = []
    for f in sorted((folder / "estrategias").glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        rows += [{"study": study, "strategy": r["strategy"], "identity": r.get("identity", ""),
                  "key": k, "value": number(x)} for k, x in flatten(r)]
    for f in sorted(folder.glob("*.parquet")):
        df = pd.read_parquet(f)
        df = df.reset_index() if df.index.name == "identity" else df
        if "strategy" not in df.columns:
            continue
        df = df[df["strategy"].notna()]
        if df["strategy"].duplicated().any():
            continue        # a trade or cell table: its rows are not one per strategy
        rows += per_strategy(study, df, slug(f.stem), {"strategy", "identity"})
    for name in CSVS:
        csv = folder / name
        if not csv.exists():
            continue
        df = pd.read_csv(csv, dtype=str)
        if name != "verdict.csv" and df["strategy"].duplicated().any():
            continue        # a ladder over several markets: no one row per strategy
        rows += per_strategy(study, df, f"{csv.stem}_csv", NAMES)
        if name == "verdict.csv":
            ids = df["identity"].fillna("") if "identity" in df.columns else \
                pd.Series("", index=df.index)
            rows += [{"study": study, "strategy": s, "identity": i, "key": "verdict_csv.drop",
                      "value": float(v == "DESCARTAR")}
                     for s, i, v in zip(df["strategy"], ids, df["verdict"])]
            # spread says its own call in words (pass/fail) beside a verdict that only marks
            rows += [{"study": study, "strategy": s, "identity": i,
                      "key": "verdict_csv.state_pass", "value": float(v == "pass")}
                     for s, i, v in zip(df["strategy"], ids, df.get("verdict_state", []))]
    return rows


def crosstf_rows(folder: Path) -> list[dict]:
    """Step 12's facts, one set per MOTHER: the cross-TF test judges a mother by its siblings.

    Keys under `crossTF.`:
        `cells.<role>.<tf>.<metric>` — role baseline (the mother on its own timeframe),
            unscaled, scaled, control; tf is the cell's timeframe, and for a scaled sibling's
            control (run on the mother's timeframe) the sibling's target. Metrics: trades,
            seen, p, and every statistic of `seen_all` / `p_all` (`net`, `p_net`…).
        `cells.<role>.<tf>.<stat>_vs_original` — that statistic over the baseline's.
        `reading.<tf>.<reading>` — 1 for the study's reading of that sibling, 0 for every other
            reading of `verdict.MEANS`; `reading.n_<reading>` counts them, 0 included — an
            absent count would read as a missing fact, and a missing fact is limbo.
    """
    cells = pd.read_parquet(folder / "cells.parquet")
    rows = []

    def add(mother: str, key: str, value: object) -> None:
        """One fact of one mother; identity left empty so it matches the mother's file by name."""
        rows.append({"study": "crossTF", "strategy": mother, "identity": "",
                     "key": key, "value": number(value)})

    original = {(r.mother, k): v for r in cells[cells["role"] == "baseline"].itertuples()
                for k, v in (r.seen_all or {}).items()}
    for r in cells.itertuples():
        hit = TARGET.search(r.strategy)
        tf = hit.group(1) if hit else r.timeframe
        at = f"cells.{r.role}.{tf}"
        for k, v in [("trades", r.trades), ("seen", r.seen), ("p", r.p),
                     *(r.seen_all or {}).items(),
                     *((f"p_{k}", v) for k, v in (r.p_all or {}).items())]:
            add(r.mother, f"{at}.{k}", v)
        for k, v in (r.seen_all or {}).items() if r.role != "baseline" else []:
            base = original.get((r.mother, k))
            if v is not None and base:
                add(r.mother, f"{at}.{k}_vs_original", v / base)
    readings = pd.read_csv(folder / "verdict.csv")
    for r in readings.itertuples():
        for reading in MEANS:
            add(r.mother, f"reading.{r.timeframe}.{reading}", r.reading == reading)
    for mother, got in readings.groupby("mother")["reading"]:
        for reading in MEANS:
            add(mother, f"reading.n_{reading}", (got == reading).sum())
    return rows


def gather(project: str, n: str) -> pd.DataFrame:
    """Every number the studies of step `n` and its extras (`steps.EXTRA`: step 8's monkey,
    profitShape, entryQuality) wrote for `project`, from each one's newest result.

    Args:
        project: Project name.
        n: A WORKFLOW step number, e.g. "8".

    Returns:
        Long frame `study, strategy, identity, key, value`: the key carries the study as its
        first part, so `gate.summary.survives` and `crossmarket.verdict.pass` never collide.
        Rows whose value is not a number are dropped. A key one strategy repeats (two table
        rows with the same label) gets `#2`, `#3`… in its order, never one picked silently.
    """
    rows = []
    for study in BY_N[n]["studies"] + BY_N[n]["extra"]:
        found = [r for r in sources.results(project, study, False if study == "edgeCost"
                                            else None) if r["path"].is_dir()]
        if found:
            rows += (crosstf_rows if study == "crossTF" else
                     lambda f: from_folder(study, f))(found[0]["path"])
    df = pd.DataFrame(rows, columns=COLUMNS).dropna(subset=["value"])
    df["key"] = df["study"] + "." + df["key"]
    nth = df.groupby(["strategy", "identity", "key"]).cumcount()
    df.loc[nth > 0, "key"] += "#" + (nth[nth > 0] + 1).astype(str)
    return df.reset_index(drop=True)


def main() -> None:
    """Print every key of one step with its count, median and range: the menu of criteria.yaml."""
    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--step", required=True, help="paso que juzga: 8, 10, 12, 14 o 16")
    ap.add_argument("--grep", default="", help="solo las claves que contienen este texto")
    a = ap.parse_args()
    df = gather(a.project, a.step)
    df = df[df["key"].str.contains(a.grep, regex=False)]
    table = df.groupby("key")["value"].agg(["count", "median", "min", "max"])
    with pd.option_context("display.max_rows", None, "display.width", 200,
                           "display.max_colwidth", 90):
        print(table.round(4).to_string())


if __name__ == "__main__":
    main()
