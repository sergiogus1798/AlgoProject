"""A study's knobs as its own loader reads them, their tooltips, and the hash a run would sign."""

import copy
import importlib

from core.paths import ROOT
from core.study.config import fingerprint
from ui.daemon.results.catalogue import STUDIES

# Each study's own config loader, which is what its report calls: several merge a shared
# file or replace `ledger:<key>` references, so reading config.yaml alone would sign a
# different hash than the study does. A study absent here has no config.yaml.
LOADERS = {
    "gate": "studies.screening.gate.inputs:config",
    "snoopingScreen": "studies.screening.snoopingScreen.inputs:config",
    "crossmarket": "studies.transfer.crossmarket.inputs.config:load",
    "crossTF": "studies.transfer.crossTF.inputs:config",
    "mcRetest": "studies.breakage.mcRetest.inputs.config:load",
    "spp": "studies.breakage.spp.inputs.config:load",
    "cloud": "studies.optimisation.cloud.inputs.config:config",
    "wfc": "studies.optimisation.wfc.inputs.config:load",
    "cscv": "studies.optimisation.cscv.inputs.config:load",
    "marketSurfaces": "studies.optimisation.marketSurfaces.inputs.config:load",
    "wfm": "studies.optimisation.wfm.inputs.config:load",
    "blindJoint": "studies.closing.blindJoint.inputs:config",
    "exposure": "studies.closing.exposure.inputs:config",
    "atrCalculator": "studies.closing.atrCalculator.inputs:config",
    # the monkey has no config.yaml of its own: its knobs are the null engine's
    "monkey": "engines.nulls.inputs:config",
    "profitShape": "studies.readings.profitShape.inputs:config",
    "entryQuality": "studies.readings.entryQuality.inputs:config",
    "edgeCost": "studies.readings.edgeCost.inputs:config",
    "conditionalMap": "studies.readings.conditionalMap.inputs:config",
    "structure": "studies.readings.structure.inputs:config",
    "monteCarlo": "portfolio.common.monteCarlo.inputs.config:load",
    "feedQuality": "studies.data.feedQuality.inputs:config",
    "spread": "studies.data.spread.inputs:config",
}

# A study whose population run signs a config that differs from what LOADERS reads, because
# it substitutes one knob before fingerprinting (crossmarket: `nulls.draws` -> `nulls.
# batch_draws`, `many.run`'s own docstring). Absent here, the population and per-strategy
# scopes sign the same config. OPEN #52: without this, a population result always read stale.
LOADERS_POPULATION = {
    "crossmarket": "studies.transfer.crossmarket.inputs.config:population",
}

# Prose copied into reports, not a knob: the gate's screens each carry a `why`.
NOT_KNOBS = ("why",)

TYPES = {bool: "bool", int: "int", float: "float", str: "str", list: "list"}

# Where the loaders read from: a study's config.yaml, the shared variant and null configs,
# the ledger's frozen thresholds. Any YAML there changing invalidates every cached config.
SOURCES = ("studies", "engines", "ledger", "portfolio", "assets")

# (study, population) -> (version, config with no overrides). The feed-quality loader
# re-reads the ledger once per reference and takes ~2 s; the catalogue and every staleness
# check ask for the same config again and again.
_BASE: dict[tuple[str, bool], tuple[float, dict | None]] = {}


def _version() -> float:
    """The newest modification time of any YAML a loader may read.

    Returns:
        Seconds since the epoch; ~7 ms over the ~50 files.
    """
    return max(p.stat().st_mtime for d in SOURCES for p in (ROOT / d).rglob("*.yaml"))


def _load(key: str, overrides: list[str], population: bool = False) -> dict | None:
    """The study's own loader, called.

    Args:
        key: Study key.
        overrides: "section.key=value" strings.
        population: Use `LOADERS_POPULATION`'s loader when the study has one — what a
            population run of it actually signs, if that differs from `LOADERS`'.

    Returns:
        The parsed config, None for a study without one.
    """
    table = LOADERS_POPULATION if population and key in LOADERS_POPULATION else LOADERS
    if key not in table:
        return None
    module, function = table[key].split(":")
    return getattr(importlib.import_module(module), function)(overrides)


def config(key: str, overrides: list[str], population: bool = False) -> dict | None:
    """The study's config as its next run would read it.

    Args:
        key: Study key.
        overrides: "section.key=value" strings, as --set takes them.
        population: As `_load`.

    Returns:
        The parsed config, or None for a study without one. A bad override raises, as
        the study itself would. Without overrides it comes from the cache while no YAML
        changed, copied so no caller can alter the cached one.
    """
    if overrides:
        return _load(key, overrides, population)
    version = _version()
    cache_key = (key, population)
    if cache_key not in _BASE or _BASE[cache_key][0] != version:
        _BASE[cache_key] = (version, _load(key, [], population))
    return copy.deepcopy(_BASE[cache_key][1])


def _leaves(node: object, path: str) -> list[tuple[str, object]]:
    """Every addressable leaf under one node, as `--set` spells its path.

    Args:
        node: A config node.
        path: Its dotted path so far, "" at the top.

    Returns:
        (dotted key, value) pairs. A list of dicts that each carry a `name` is addressed by
        that name (the gate's screens, `core.study.config.apply`'s `names`); any other
        list is one knob.
    """
    if isinstance(node, dict):
        return [leaf for k, v in node.items() if k not in NOT_KNOBS
                for leaf in _leaves(v, f"{path}.{k}" if path else str(k))]
    if isinstance(node, list) and node and all(isinstance(x, dict) and "name" in x
                                               for x in node):
        return [leaf for x in node
                for leaf in _leaves({k: v for k, v in x.items() if k != "name"}, x["name"])]
    return [(path, node)]


def _tip(tips: dict[str, str], key: str) -> str:
    """The tooltip of a knob, or of the nearest section above it that has one.

    Args:
        tips: The study's TIPS.
        key: Dotted knob path.

    Returns:
        One Spanish sentence, "" when the study wrote none.
    """
    parts = key.split(".")
    found = (tips.get(".".join(parts[:n])) for n in range(len(parts), 0, -1))
    return next((t for t in found if t), "")


def sections(key: str) -> dict:
    """The configuration drawer of one study.

    Args:
        key: Study key.

    Returns:
        `sections` — one per first-level key, each with its knobs (key, value, default,
        type, tip); top-level scalars go in "general" — and `hash`, the config's
        fingerprint. A study without a config returns no sections and a None hash.
    """
    cfg = config(key, [])
    if cfg is None:
        return {"sections": [], "hash": None}
    tips = importlib.import_module(f"{STUDIES[key][1]}.tooltips").TIPS
    grouped: dict[str, list[dict]] = {}
    for dotted, value in _leaves(cfg, ""):
        section = dotted.split(".")[0] if "." in dotted else "general"
        grouped.setdefault(section, []).append({
            "key": dotted, "value": value, "default": value,
            "type": TYPES.get(type(value), "str"), "tip": _tip(tips, dotted)})
    return {"sections": [{"name": n, "knobs": k} for n, k in grouped.items()],
            "hash": fingerprint(cfg)}


def signed(key: str, overrides: list[str], population: bool = False) -> str | None:
    """The hash the next run would sign with these overrides.

    Args:
        key: Study key.
        overrides: "section.key=value" strings.
        population: As `config` — the population scope's loader when the study has one.

    Returns:
        16 hex characters, None for a study without a config.
    """
    cfg = config(key, overrides, population)
    return fingerprint(cfg) if cfg is not None else None
