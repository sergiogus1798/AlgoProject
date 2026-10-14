"""The exports an analysis reads that are not loader pieces: which databanks feed each, and the command."""

from studies.breakage.mcRetest.inputs.tasks import DATABANK as MCR

# The exports a step's analysis reads that are not the loader's pieces: without them the
# analysis ran on the last export a skill had made, or said «necesita el export» (📓
# 2026-09-29: the step-13 run of the window was never ingested, so step 14 read 09-27's).
# Name → (source databanks, export databank, what marks one export, argv after `-m`).
# The ingest refuses when a metric misses on max(2, 5 %) of its runs, a share calibrated on
# hundreds: the ten strategies of a smoke run tripped it with 5 of 70 RecoveryFactor cells at
# 1.01-1.22x the tolerance and the run ended at step 14 (🔬 2026-10-05). A smoke run passes the
# ingest's own override; the cells are still excluded and recorded. Never outside `--smoke`.
SMOKE_SHARE = 0.2
EXTRA = {
    # The marker is each export's manifest.json, which every export rewrites: a folder's date
    # does not move when a second export of the day overwrites its files, and the WFM was
    # re-exported (918k trades, ~8 min) at every stop for it (📓 2026-09-29).
    "ingesta MC Retest": (
        tuple(MCR.values()),
        "MCR_All",
        "*/manifest.json",
        ["studies.breakage.mcRetest.ingest", "--databank", "MCR_All"],
    ),
    "SPP IS": (
        ("SPP IS",),
        "SPP_IS",
        "*/spp/manifest.json",
        ["sqx.export.export_spp", "--databank", "SPP IS"],
    ),
    "SPP OOS": (
        ("SPP OOS",),
        "SPP_OOS",
        "*/spp/manifest.json",
        ["sqx.export.export_spp", "--databank", "SPP OOS"],
    ),
    "WFM": (
        ("WFM",),
        "WFM",
        "*/wfm/manifest.json",
        ["sqx.export.export_wfm", "--databank", "WFM"],
    ),
}
