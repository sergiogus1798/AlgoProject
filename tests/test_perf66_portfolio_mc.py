"""Encargo 66, the portfolio Monte Carlo: each fast or reseeded path against the code it replaced.

Bit for bit where the stream is kept (stitch under one generator, the weekly signs, family D's
windows, the greedy seeds); in distribution where the owner let the stream change (the stage-B
null's candidates, 2026-10-13); and no repeated seed among a million paths.
"""

import tracemalloc

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from engines.weekly import flip
from portfolio.common.construct.mc import paths
from portfolio.common.construct.search import greedy, stageb_null
from portfolio.common.monteCarlo.inputs import config as mc_config
from portfolio.common.monteCarlo.model import windows
from portfolio.common.monteCarlo.simulate import engine, family_d, metrics, stitch
from portfolio.common.monteCarlo.verdict import confidence

DRAWS = 20_000


def _graph(n: int, density: float, seed: int) -> np.ndarray:
    """A random symmetric admissible graph, diagonal False."""
    g = np.random.default_rng(seed).random((n, n)) < density
    return (g | g.T) & ~np.eye(n, dtype=bool)


def _old_grow(graph: np.ndarray, order: np.ndarray) -> np.ndarray:
    """greedy._grow as it was before it was compiled."""
    picked = np.empty(0, dtype=np.int32)
    for node in order:
        if picked.size == 0 or bool(graph[node, picked].all()):
            picked = np.append(picked, np.int32(node))
    return picked


def _old_candidates(graph: np.ndarray, sizes: np.ndarray, n: int,
                    rng: np.random.Generator) -> np.ndarray:
    """stageb_null.candidates as it was: one Python loop, everything from `rng`."""
    out = np.full((n, int(sizes.max())), -1, dtype=np.int32)
    order = np.arange(graph.shape[0])
    for row, k in enumerate(rng.choice(sizes, size=n)):
        rng.shuffle(order)
        clique = np.sort(_old_grow(graph, order))
        picked = np.sort(rng.choice(clique, size=min(int(k), clique.size), replace=False))
        out[row, :picked.size] = picked
    return out


def _old_bad_draws(pnl: np.ndarray, sims: int, quantiles: list[float],
                   rng: np.random.Generator) -> dict[float, np.ndarray]:
    """stitch._bad_draws as it was: the whole (sims, n) matrix and its argsort."""
    drawn = pnl[rng.integers(0, pnl.size, (sims, pnl.size))]
    order = np.argsort(drawn.sum(axis=1))
    return {q: drawn[order[int(q * (sims - 1))]] for q in quantiles}


def _segments(sizes: list[int]) -> list[dict]:
    """Consecutive blocks of trade positions of the given sizes."""
    edges = np.cumsum([0, *sizes])
    return [{"positions": np.arange(a, b)} for a, b in zip(edges[:-1], edges[1:])]


def test_worst_path_is_seeded_and_equal_to_the_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two runs give one path; drawn in strips it is the old whole-matrix path of the same stream.

    Segments of 2 and 3 trades are there for the ties: thousands of draws share a total, and
    the row the old argsort took among them is the row this must take.
    """
    sizes = [2, 3, 40, 1, 75, 130]
    pnl = np.random.default_rng(1).normal(20.0, 300.0, sum(sizes)).round(2)
    quantiles, sims = [0.01, 0.05, 0.10, 0.25], 3000
    first = stitch.worst_path(pnl, _segments(sizes), sims, quantiles, 100_000.0)
    assert first == stitch.worst_path(pnl, _segments(sizes), sims, quantiles, 100_000.0)

    rng = np.random.default_rng(stitch.SEED)
    old = [_old_bad_draws(pnl[s["positions"]], sims, quantiles, rng)
           for s in _segments(sizes) if s["positions"].size > 1]
    for strip_bytes in (stitch.STRIP_BYTES, 16 * 130 * 7, 1):
        monkeypatch.setattr(stitch, "STRIP_BYTES", strip_bytes)
        got = stitch.worst_path(pnl, _segments(sizes), sims, quantiles, 100_000.0)
        for q in quantiles:
            want = metrics.observed(np.concatenate([seg[q] for seg in old]), 100_000.0)
            assert got[q] == {**want, "segments": 5, "quantile": q}, (strip_bytes, q)


def test_path_gens_are_distinct_and_reproducible() -> None:
    """The kernels' generators come from `rng` alone: same rng, same draws; no two share a stream."""
    a, b = paths.path_gens(np.random.default_rng(1)), paths.path_gens(np.random.default_rng(1))
    first = np.array([g.integers(0, 2**62) for g in a])
    assert len(a) == paths.CHUNKS and len(np.unique(first)) == paths.CHUNKS
    assert np.array_equal(first, [g.integers(0, 2**62) for g in b])


def test_trade_paths_reproduce_from_their_generator() -> None:
    """T1 and T2 from the same generator seed are the same paths, to the last bit."""
    rng = np.random.default_rng(3)
    closed = rng.normal(0.0, 1.0, 400)
    from test_portfolio_mc_paths import _member
    members = [_member(closed), _member(closed[::-1].copy())]
    for draw in (lambda r: paths.trade_bootstrap(members, 40, 500, r),
                 lambda r: paths.trade_blocks(members, 40, 500, 7, r)):
        a, b = draw(np.random.default_rng(11)), draw(np.random.default_rng(11))
        assert all(np.array_equal(a[k], b[k]) for k in paths.FIGURES)


def test_greedy_seeds_did_not_move() -> None:
    """The compiled clique walk is the Python one: the real search's seeds keep their stream."""
    graph = _graph(80, 0.6, 5)
    got = greedy.seeds(graph, 200, np.random.default_rng(9))
    rng, order = np.random.default_rng(9), np.arange(80)
    for clique in got:
        rng.shuffle(order)
        want = np.sort(_old_grow(graph, order))
        assert clique.dtype == want.dtype and np.array_equal(clique, want)


@pytest.mark.parametrize("nodes, density", [(60, 0.5), (40, 0.85), (120, 0.3)])
def test_null_candidates_keep_their_distribution(nodes: int, density: float) -> None:
    """The compiled null draws what the Python loop drew: 20,000 of each, compared.

    Read on the size of the combination, on how often each node is in one, and on a
    continuous functional of the members (a fixed random weight per node, summed): its two
    moments within Monte Carlo error and a two-sample Kolmogorov-Smirnov that does not reject.
    """
    graph = _graph(nodes, density, 21)
    sizes = np.array([2, 3, 3, 4, 5, 6])
    old = _old_candidates(graph, sizes, DRAWS, np.random.default_rng(100))
    new = stageb_null.candidates(graph, sizes, DRAWS, np.random.default_rng(200))
    assert np.array_equal(new, stageb_null.candidates(graph, sizes, DRAWS,
                                                      np.random.default_rng(200)))
    for row in new[:2000]:
        members = row[row >= 0]
        assert np.all(np.diff(members) > 0) and graph[np.ix_(members, members)].sum() == \
            members.size * (members.size - 1)

    width = sizes.max() + 1
    counts = np.array([np.bincount((c >= 0).sum(axis=1), minlength=width) for c in (old, new)])
    assert stats.chi2_contingency(counts[:, counts.sum(axis=0) > 0])[1] > 0.01

    share = [np.bincount(c[c >= 0], minlength=nodes) / DRAWS for c in (old, new)]
    pooled = (share[0] + share[1]) / 2
    z = (share[0] - share[1]) / np.sqrt(pooled * (1 - pooled) * 2 / DRAWS)
    # 5 sigma is the Bonferroni bar over the nodes (4 was not: one node of 60 read 4.006 here by
    # chance; at 200,000 draws old against new peaks at 2.0-2.3, old against old at 3.0)
    assert np.abs(z).max() < 5.0, np.abs(z).max()
    assert stats.chi2.sf((z**2).sum(), nodes) > 0.001

    weight = np.append(np.random.default_rng(4).normal(0.0, 1.0, nodes), 0.0)
    a, b = weight[old].sum(axis=1), weight[new].sum(axis=1)
    assert abs(a.mean() - b.mean()) < 4 * np.sqrt((a.var() + b.var()) / DRAWS)
    assert abs(a.std() / b.std() - 1) < 0.04
    assert stats.ks_2samp(a, b).pvalue > 0.01


def _old_signs(seed: int, draws: int, weeks: int, block_weeks: int = 1) -> np.ndarray:
    """flip.signs as it was: two float64 temporaries and the repeat's copy."""
    blocks = -(-weeks // block_weeks)
    coin = np.random.default_rng(seed).integers(0, 2, (draws, blocks), dtype=np.int8)
    return np.repeat(coin * 2.0 - 1.0, block_weeks, axis=1)[:, :weeks]


def test_weekly_signs_same_matrix_in_half_the_memory() -> None:
    """The same +-1 matrix and the same `signs @ panel`, and only one float64 copy ever held."""
    panel = np.random.default_rng(2).normal(0.0, 1.0, (131, 9))
    for block in (1, 2, 3):
        old, new = _old_signs(7, 4000, 131, block), flip.signs(7, 4000, 131, block)
        assert new.dtype == old.dtype and np.array_equal(old, new)
        assert np.array_equal(old @ panel, new @ panel)
        assert np.array_equal(old @ pd.DataFrame(panel), new @ pd.DataFrame(panel))
    peaks = []
    for build in (_old_signs, flip.signs):
        tracemalloc.start()
        build(7, 20_000, 520, 1)
        peaks.append(tracemalloc.get_traced_memory()[1])
        tracemalloc.stop()
    result = 20_000 * 520 * 8
    assert peaks[0] > 1.9 * result and peaks[1] < 1.3 * result, peaks


def _old_slices(source: dict, spans: list[dict], cfg: dict, want_shape: bool) -> list[dict]:
    """family_d._slices as it was: one engine.single per window, here, in a loop."""
    sims, q = cfg["family_d"]["window_sims"], cfg["global"]["report_percentile"]
    rows = []
    for span in spans:
        pos = span["positions"]
        if pos.size < confidence.MEAN_PROVISIONAL:
            rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                         "median_net": float("nan"), "net_5": float("nan"),
                         "pf_5": float("nan"), "shape": None})
            continue
        got = engine.single(engine.payload(source, pos), "draw", "stationary",
                            mc_config.stationary_block(pos.size), sims, cfg, 0)
        net_seen = float(source["pnl"][pos].sum())
        rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                     "median_net": float(np.median(got["net"])),
                     "net_5": float(np.percentile(got["net"], 5)),
                     "pf_5": float(np.nanpercentile(got["pf"], 5)),
                     "shape": metrics.shape(got["net"], net_seen, q) if want_shape else None})
    return rows


def test_family_d_windows_same_figures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every window asks the kernel for what it asked before: fed one stream, the same rows.

    Each window has its own seed, so each call's generator is pinned here to compare;
    a sparse stretch leaves windows under the minimum, which stay blank.
    """
    rng = np.random.default_rng(6)
    opens = np.concatenate([pd.date_range("2015-01-01", periods=900, freq="36h").to_numpy(),
                            pd.date_range("2019-01-01", periods=12, freq="90D").to_numpy(),
                            pd.date_range("2022-01-01", periods=700, freq="24h").to_numpy()])
    pnl = rng.normal(15.0, 200.0, opens.size)
    source = {"pnl": pnl, "cost": np.zeros(pnl.size), "spread": np.full(pnl.size, 0.5),
              "mae": np.abs(pnl), "open": opens}
    cfg = mc_config.load(["family_d.window_sims=400", "global.seed=0"])
    fresh = np.random.default_rng
    monkeypatch.setattr(np.random, "default_rng", lambda *a: fresh(77))
    monkeypatch.setattr(engine, "SERIAL", True)
    for step, want_shape in ((6, False), (24, True)):
        spans = windows.rolling(opens, 24, step)
        got = family_d._slices(source, spans, cfg, want_shape)
        want = _old_slices(source, spans, cfg, want_shape)
        assert any(np.isnan(r["net_5"]) for r in got) and len(got) == len(spans) > 3
        assert repr(got) == repr(want)
