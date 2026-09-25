"""A throwaway mother strategy on disk, so the two proofs need no SQX and no real export."""

import json
import shutil
from pathlib import Path

from core.paths import report_dir
from pipeline.ledger import state
from pipeline.stages import recipe
from pipeline.stubs import placeholder

PROJECT, DATABANK, STRATEGY, DAY, ASSET = "_selftest", "SELFTEST", "Strategy 0.0.1", \
                                          "1970-01-01", "XAUUSD"
# The numbers the design brief would carry. Chosen to clear every threshold in
# config.yaml, so a failing self-test means the pipeline broke and not the thresholds.
BRIEF = {"strategy": STRATEGY, "verdict": "proceed", "n_eff": 8412,
         "observed_max": 4.61, "noise_max": 1.83, "parameters": [], "frozen": []}


def work() -> Path:
    """The fixture's work directory.

    Returns:
        Path under the data root, in a project no SQX install has.
    """
    return state.work_dir(PROJECT, STRATEGY)


def build() -> dict:
    """Create the fixture and return the substitution table the stages need.

    Returns:
        What `recipe.context` returned for it. The design brief is written by hand
        because the point of the fixture is to test the chaining, not sppUltra.
    """
    remove()
    where = report_dir(PROJECT, DATABANK, DAY) / "spp"
    where.mkdir(parents=True, exist_ok=True)
    (where / f"design_brief_{state.safe(STRATEGY)}.json").write_text(
        json.dumps(BRIEF, indent=2), encoding="utf-8")
    state.open_run(work(), STRATEGY, PROJECT, DATABANK, ASSET)
    return recipe.context(PROJECT, DATABANK, STRATEGY, DAY)


def chain(ctx: dict) -> list[dict]:
    """The stages the fixture can actually run.

    Args:
        ctx: What `build()` returned.

    Returns:
        Every stage, resolved, with each command that drives a real module
        swapped for the placeholder and its outputs normalised to `{work}/<name>.json`.

        What is under test here is the **ledger**: ordering, resumption, the monotonicity of
        `progress`, and that a half-written `state.json` is still valid JSON. None of that
        needs a real SQX export, a real parent `.sqx` or the 5,000 files the build stage
        writes -- and demanding them would turn a two-second check into a two-minute one
        that cannot run on a machine with no data. The real rows are exercised by running
        `pipeline.run` against a real strategy, which is a different test.

        The row's `name`, `record`, `hash` and `must` are kept, because those are the parts
        the ledger actually reads.

        A row the placeholder has no shape for is left exactly as the recipe writes it.
        That is `verdict`, which is this folder's own module and reads only the ledger the
        earlier stages wrote -- so it runs against the fixture for real, and should, since
        it is the stage that turns numbers into a judgement.
    """
    rows = []
    # Every row, not stages()[1:]. The slice used to skip sppultra because it was first;
    # the SPP rows now are, and a positional skip silently stopped matching what it meant.
    for row in recipe.stages():
        if row["name"] in placeholder.SHAPE:
            row = row | {"command": f"python3 -m pipeline.stubs.placeholder "
                                    f"--stage {row['name']} --work {{work}}",
                         "produces": [f"{{work}}/{row['name']}.json"]}
            row.pop("record_from", None)
        rows.append(recipe.resolve(row, ctx))
    return rows


def remove() -> None:
    """Delete everything the fixture wrote."""
    for where in (work(), report_dir(PROJECT, DATABANK, DAY)):
        shutil.rmtree(where, ignore_errors=True)
