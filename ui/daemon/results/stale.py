"""Whether a stored result is «caducado»: no configuration the window could launch today for this
project, the same way, would sign its hash."""

import itertools
import json
from pathlib import Path

from ui.daemon.results import forproject, knobs, store


def _recorded(path: Path) -> list[str] | None:
    """The `--set` overrides a run recorded in its manifest (`source.overrides`), or None."""
    got = json.loads(path.read_text(encoding="utf-8")).get("source") or {}
    return got.get("overrides") if isinstance(got.get("overrides"), list) else None


def _project(study: str, project: str) -> list[str]:
    """The overrides the runner adds for this project (`forproject.SET`), [] when none."""
    mine = forproject.facts(project) if study in forproject.SET else None
    return [f"{k}={mine[v]}" for k, v in forproject.SET[study].items()] if mine else []


def _signed(study: str, overrides: list[str], population: bool) -> str | None:
    """`knobs.signed`, None when today's config no longer takes one of these overrides."""
    try:
        return knobs.signed(study, overrides, population)
    except (KeyError, ValueError, TypeError):
        return None


def fresh(study: str, project: str, manifest: Path | None, population: bool) -> set[str]:
    """Every hash a run of this study for this project would sign with today's config.

    The ways it can be run: with the runner's per-project substitutions (cloud's `run.symbol`,
    the gate's `monkey.timeframe`…; none for most studies), or with the overrides its own run
    recorded in its manifest (a run by hand, outside the window) — each under every value of a
    per-run choice (`knobs.CHOICES`, the WFC's `split_mode`), which picks what to read and
    never makes a result stale (owner, 2026-10-01).

    Args:
        study: Study key.
        project: SQX project name.
        manifest: The run's own `manifest.json`, None when it has none or it is shared.
        population: Sign as the population scope (`knobs.LOADERS_POPULATION`).

    Returns:
        The hashes; empty for a study without a config.
    """
    sets = [_project(study, project)]
    recorded = (store.cached(manifest, _recorded) if manifest is not None and manifest.is_file()
                else None)
    if recorded is not None:
        sets.append(recorded)
    base = knobs.config(study, [], population)
    if base is None:
        return set()
    leaves = dict(knobs._leaves(base, ""))
    choices = [[f"{k}={v}" for v in values] for k, values in knobs.CHOICES.items() if k in leaves]
    picks = [list(p) for p in itertools.product(*choices)] if choices else [[]]
    return {h for s in sets for p in picks if (h := _signed(study, s + p, population))}


def judge(study: str, config_hash: str, project: str, manifest: Path | None,
          population: bool) -> tuple[bool, str | None]:
    """Whether one stored result is stale, and the hash it is compared with.

    Args:
        study, project, manifest, population: As `fresh`.
        config_hash: The hash the result signed.

    Returns:
        (stale, current): `current` is the result's own hash when some way of running it
        today signs the same, else the hash of the project's own run; (False, None) for a
        study without a config.
    """
    hashes = fresh(study, project, manifest, population)
    if not hashes:
        return False, None
    if config_hash in hashes:
        return False, config_hash
    return True, _signed(study, _project(study, project), population)
