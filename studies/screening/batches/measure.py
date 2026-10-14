"""Whether several builds of one cell are one population: same setup, same funnel, few repeats."""

import hashlib
from pathlib import Path
from typing import TypedDict, cast

import numpy as np
import pandas as pd

ALIVE = "sobrevive"
SMALL = "otras"          # destinations whose expected count per batch is under MIN_EXPECTED
MIN_EXPECTED = 5
ALARM = 0.01             # the funnel differs between batches
WARN, STOP = 0.10, 0.30  # share of a batch already generated in the earlier ones (owner, 2026-10-07)
DRAWS = 5000


def parts(verdict: pd.DataFrame) -> pd.DataFrame:
    """Each generated strategy's island and where the gate left it.

    Args:
        verdict: The gate's verdict.csv of one batch.

    Returns:
        `identity`, `island` and `dest` — the first rule that killed it, or ALIVE. SQX names a
        genetic build's strategy `Strategy <island>.<generation>.<n>`: an island evolves its
        own relatives, so it is the unit chance acts on, not the strategy.
    """
    return pd.DataFrame({
        "identity": verdict["identity"],
        "island": verdict["strategy"].str.extract(r"Strategy (\d+)\.")[0].astype(int),
        "dest": verdict["reason"].str.extract(r"gate\.scorecard\.(\w+?)=")[0]
        .where(verdict["verdict"] == "DESCARTAR", ALIVE)})


def fingerprint(source: dict, screens: list[str], row: dict) -> dict[str, str | list[str]]:
    """What has to be equal for two batches to be the same draw.

    Args:
        source: `source` of the gate's manifest.
        screens: The rules the gate applied, in order (funnel.csv).
        row: The project's line of the registry.

    Returns:
        Field -> value. The gate's seeds are left out: they are drawn per run.
    """
    template = Path(row["template"])
    return {"symbol": row["symbol"], "timeframe": row["timeframe"],
            "template": hashlib.sha256(template.read_bytes()).hexdigest()[:12],
            "feed": source["feed"], "split": source["split"], "end": source["end"],
            "overrides": sorted(o for o in source["overrides"] if "seed" not in o),
            "rules": screens}


def table(batches: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Islands by destination, small destinations pooled.

    Args:
        batches: Batch name -> `parts`.

    Returns:
        One row per (batch, island), one column per destination; a destination a batch would
        hold fewer than MIN_EXPECTED of goes into SMALL.
    """
    both = pd.concat([b.assign(batch=name) for name, b in batches.items()])
    share = both["dest"].value_counts(normalize=True)
    least = min(len(b) for b in batches.values())
    pooled = both["dest"].where(pd.Series(both["dest"]).map(share) * least >= MIN_EXPECTED, SMALL)
    return pd.crosstab([both["batch"], both["island"]], pooled)


def chi2(counts: np.ndarray) -> float:
    """Pearson's statistic of a rows-by-destinations table of counts; an empty column adds nothing."""
    counts = counts[:, counts.sum(0) > 0]
    expected = counts.sum(1, keepdims=True) * counts.sum(0, keepdims=True) / counts.sum()
    return float(((counts - expected) ** 2 / expected).sum())


class Homogeneity(TypedDict):
    """Whether the batches' funnels differ more than chance: statistic, p, alarm and dispersion."""
    chi2: float
    p: float
    alarm: bool
    phi: float


class Repeat(TypedDict):
    """How much of one batch the earlier ones had already generated."""
    batch: str
    generated: int
    repeated: int
    share: float
    alive: int
    alive_repeated: int
    space: float
    state: str


class Spread(TypedDict):
    """How concentrated a batch's survivors are among its islands."""
    alive: int
    islands: int
    of: int
    top: int
    top_n: int


def homogeneity(islands: pd.DataFrame, seed: int = 0) -> Homogeneity:
    """Whether the batches' funnels differ more than batches of related strategies do by chance.

    Args:
        islands: What `table` returned.
        seed: Of the permutation.

    Returns:
        `chi2` between batches, `p` — the share of DRAWS relabellings of whole islands that
        reach it — `phi`, how many times wider than independent draws the islands of one batch
        spread, and `alarm`. Islands are relabelled, never strategies: 19 of one build's 56
        survivors came from one island, so a strategy is not an independent draw.
    """
    counts = islands.to_numpy(float)
    label = pd.factorize(islands.index.get_level_values("batch"))[0]
    lots = np.eye(label.max() + 1)

    def between(of: np.ndarray) -> float:
        """The statistic with the islands labelled `of`."""
        return chi2(lots[of].T @ counts)

    rng = np.random.default_rng(seed)
    seen = between(label)
    drawn = np.array([between(rng.permutation(label)) for _ in range(DRAWS)])
    within = [(chi2(counts[label == k]), (np.sum(label == k) - 1) * (counts.shape[1] - 1))
              for k in range(label.max() + 1)]
    p = float((1 + np.sum(drawn >= seen)) / (1 + DRAWS))
    return Homogeneity(chi2=seen, p=p, alarm=p < ALARM,
                       phi=float(sum(c for c, _ in within) / sum(d for _, d in within)))


def by_rule(funnels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Each rule's kill rate per batch, of those that reached it, against the first batch.

    Args:
        funnels: Batch name -> the gate's funnel.csv.

    Returns:
        One row per rule that killed anybody: `entered`, `died` and `rate` per batch, and `z`,
        the gap to the first batch in binomial standard errors. A diagnosis of which rule
        moves, not a test: related strategies make these z's larger than chance alone would.
    """
    names = list(funnels)
    first = funnels[names[0]]
    out = first[["screen"]].copy()
    for name in names:
        f = funnels[name]
        out[f"entered {name}"], out[f"died {name}"] = f["entered"], f["died"]
        out[f"rate {name}"] = f["died"] / f["entered"]
    for name in names[1:]:
        n1, n2 = first["entered"], funnels[name]["entered"]
        pooled = (first["died"] + funnels[name]["died"]) / (n1 + n2)
        out[f"z {name}"] = ((out[f"rate {name}"] - out[f"rate {names[0]}"])
                            / np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2)))
    return pd.DataFrame(out[sum(out[f"died {n}"] for n in names) > 0]).reset_index(drop=True)


def repeats(batches: dict[str, pd.DataFrame]) -> list[Repeat]:
    """How much of each batch the earlier ones had already generated.

    Args:
        batches: Batch name -> `parts`, oldest first.

    Returns:
        Per batch after the first: `repeated` identities of `generated`, their `share`,
        `alive_repeated` of its `alive` survivors, `space` — the capture-recapture bound on how
        many distinct strategies the cell holds, a floor when the build is genetic and `> n1·n2`
        with no repeat — and `state`: ok, aviso (WARN) or parar (STOP).
    """
    names, out = list(batches), []
    seen: set[str] = set()
    for name in names:
        b = batches[name]
        if seen:
            hit = b["identity"].isin(list(seen))
            share = float(hit.mean())
            out.append(Repeat(
                batch=name, generated=len(b), repeated=int(hit.sum()), share=share,
                alive=int((b["dest"] == ALIVE).sum()),
                alive_repeated=int((hit & (b["dest"] == ALIVE)).sum()),
                space=len(seen) * len(b) / max(int(hit.sum()), 1),
                state="parar" if share >= STOP else "aviso" if share >= WARN else "ok"))
        seen |= set(b["identity"])
    return out


def spread(b: pd.DataFrame) -> Spread:
    """How concentrated a batch's survivors are: of how many islands, and the largest one's."""
    alive = pd.Series(b[b["dest"] == ALIVE]["island"]).value_counts()
    return Spread(alive=int(alive.sum()), islands=int(len(alive)), of=int(b["island"].nunique()),
                  top=int(cast(int, alive.index[0])) if len(alive) else 0,
                  top_n=int(alive.max()) if len(alive) else 0)


def differing(prints: dict[str, dict[str, str | list[str]]]) -> list[str]:
    """The fingerprint fields that are not equal across batches."""
    first = next(iter(prints.values()))
    return [k for k in first if any(p[k] != first[k] for p in prints.values())]


def decision(fields: list[str], same: Homogeneity | None, dup: list[Repeat]) -> tuple[str, str]:
    """The one line the owner acts on.

    Args:
        fields: `differing`.
        same: `homogeneity`.
        dup: `repeats`.

    Returns:
        (NO SUMAR | PARAR CELDA | AVISO | SUMAR, why). SUMAR says no difference was detected,
        never that there is none: two batches cannot show that.
    """
    if fields:
        return "NO SUMAR", "la configuración difiere entre lotes: " + ", ".join(fields)
    assert same is not None     # only `fields` makes the caller skip homogeneity
    if same["alarm"]:
        return "NO SUMAR", (f"el embudo difiere entre lotes más que el azar (p={same['p']:.4f}): "
                            "mirar qué cambió antes de juntarlos")
    worst = max(dup, key=lambda d: d["share"])
    if worst["state"] == "parar":
        return "PARAR CELDA", (f"{worst['share']:.0%} de {worst['batch']} ya estaba generado: "
                               "la celda está agotada, o la semilla se repite si es casi todo")
    if worst["state"] == "aviso":
        return "AVISO", (f"{worst['share']:.0%} de {worst['batch']} ya estaba generado: la celda "
                         f"tiene del orden de {worst['space']:,.0f} estrategias distintas")
    return "SUMAR", "no se detecta diferencia entre lotes ni repetidas (con pocos lotes, potencia baja)"
