"""The eight tasks: what each perturbs, what it holds fixed, and the check against what SQX ran."""

from pathlib import Path

from core import sqxretest

# Order matters: it is the order the report reads them in, control first and production last.
TASKS = ("bar", "spread", "slippage", "mindist", "params", "exits", "ohlc", "stress")

DATABANK = {"bar": "MCR 1 Bar", "spread": "MCR 2 Spread", "slippage": "MCR 3 Slippage",
            "mindist": "MCR 4 MinDist", "params": "MCR 5 Params", "exits": "MCR 6 Exits",
            "ohlc": "MCR 7 OHLC", "stress": "MCR 8 Stress"}

# The SQX method types each task must have active, and no others. This is the isolation the
# whole study rests on: a task running two methods cannot attribute its damage to either.
METHOD = {"bar": ("RandomizeStartingBar",),
          "spread": ("RandomizeSpread",),
          "slippage": ("RandomizeSlippage",),
          "mindist": ("RandomizeMinDistance",),
          "params": ("RandomizeStrategyParameters",),
          "exits": ("RandomizeExitParameters",),
          "ohlc": ("RandomizeHistoryDataOHLC",),
          "stress": ("RandomizeExitParameters", "RandomizeHistoryDataOHLC",
                     "RandomizeMinDistance", "RandomizeSlippage", "RandomizeSpread",
                     "RandomizeStrategyParameters")}

# What each task randomises and what it leaves alone. Printed beside the numbers it produced,
# not kept as documentation: a reader who cannot see what moved cannot read what it cost.
PERTURBS = {
    "bar": "the bar the backtest starts on",
    "spread": "the spread charged on every trade",
    "slippage": "the slippage charged on every fill",
    "mindist": "how close to price a pending order may sit before the broker refuses it",
    "params": "every strategy parameter, each one certain to move",
    "exits": "the exit parameters only — stop, target, trailing",
    "ohlc": "the price history itself, each bar jittered by a share of its own ATR",
    "stress": "all six at once"}

HOLDS_FIXED = {
    "bar": "the strategy, its parameters, the data and every cost",
    "spread": "the strategy, the data, and every cost but the spread",
    "slippage": "the strategy, the data, and every cost but the slippage",
    "mindist": "the strategy, the data and every per-trade cost",
    "params": "the data and every cost",
    "exits": "the data, every cost, and every entry parameter",
    "ohlc": "the strategy, its parameters and every cost",
    "stress": "nothing but the strategy's own rules"}

# What a reader is entitled to conclude from this task alone, and nothing more.
READS = {
    "bar": "the irreducible noise floor: how much a re-run moves when nothing meaningful changed",
    "spread": "sensitivity to the quoted cost of entering",
    "slippage": "sensitivity to the fill actually received",
    "mindist": "whether the stops sit close enough to price for a broker to refuse them",
    "params": "whether the edge sits on a plateau of the fitness surface or on a narrow peak",
    "exits": "whether the edge is in the entry or in a finely calibrated stop",
    "ohlc": "whether the decisive trades are anchored to the exact history that happened",
    "stress": "what to expect in production when everything degrades at once"}

# The control is the denominator, never a test: a re-run moves even when nothing changed, and
# every other task's effect is only meaningful measured against that floor.
ROLE = {"bar": "control", "spread": "execution", "slippage": "execution",
        "mindist": "execution", "params": "specification", "exits": "specification",
        "ohlc": "data", "stress": "production"}

# Which sample the perturbation and the re-run cover. Only the production task is "full", and
# "full" means whatever split the strategy itself carries -- verify it has out-of-sample trades.
SCOPE = {t: ("full" if t == "stress" else "is") for t in TASKS}

# SQX's own intrabar fidelity codes, read off the eight runs on 2026-09-18.
PRECISION = {"1": "selected timeframe (fastest)", "2": "one minute", None: "unset"}

# The comparisons this study makes, and the question each one asks. Nothing outside this list
# is compared: a contrast with no question behind it is a p-value looking for a use.
CONTRASTS = (("ohlc", "params", "is it more fragile to the history it saw or to its own numbers?"),
             ("params", "exits", "does the edge live in the entry or only in the exit?"),
             ("slippage", "spread", "which half of the execution cost actually matters?"))

# What each task is called on screen and in the report. The keys above are code; nobody should
# have to know them to read a chart.
TITLES = {"bar": "Barra inicial (control)", "spread": "Spread", "slippage": "Slippage",
          "mindist": "Distancia mínima", "params": "Parámetros", "exits": "Salidas",
          "ohlc": "Datos históricos", "stress": "Estrés combinado"}


def provenance(path: Path) -> dict:
    """What one .sqx says about the retest that produced it.

    Args:
        path: A .sqx from one of the task databanks.

    Returns:
        The active method types with their parameters, the declared and stored simulation
        counts, the sample scope, the intrabar precision in words, and the date range.
        `stored` below `declared` means the run was cut short: its own level table was
        written over the full count and every rank in it is shifted.
    """
    settings, meta = sqxretest.settings(path), sqxretest.meta(path)
    return {"methods": settings["methods"],
            "declared": meta["declared"],
            "stored": int(sqxretest.simulations(path)["index"].size),
            "scope": "full" if settings["full_sample"] else "is",
            "precision": PRECISION.get(settings["precision"], settings["precision"]),
            "date_range": meta["date_range"]}


def verify(got: dict, task: str) -> list[str]:
    """Whether a databank holds the task it is supposed to hold.

    Args:
        got: What provenance() returned.
        task: One of TASKS.

    Returns:
        One message per broken expectation, empty when the databank is what it claims.
        These are fatal: a task running the wrong methods is a study about something else,
        and ingest refuses it rather than producing numbers under a false label.
        Only the *isolation* is asserted -- which methods ran, and over which sample. The
        magnitudes are the owner's decision and are recorded rather than judged, so a re-run
        with a wider spread range still parses and the report says which range.
        A short run is not here: it is a data-quality fact, not a wrong task. See usable().
    """
    out = []
    ran, want = set(got["methods"]), set(METHOD[task])
    # The production task is the one composition the project cannot always write in full: a
    # perturbation whose range is undecided is not written, and MinDistance never applies to
    # a population of market orders. A SUBSET is therefore read, not refused -- what it is
    # missing changes what the number means, so `methods` travels with the result and the
    # report names them. Every other task stays exact: two methods in one task cannot be
    # attributed to either, and that isolation is what the whole study rests on.
    wrong = ran - want if task == "stress" else ran ^ want
    if wrong or not ran:
        out.append(f"{task}: ran {sorted(ran)}, expected {sorted(want)}")
    if got["scope"] != SCOPE[task]:
        out.append(f"{task}: ran on the {got['scope']} sample, expected {SCOPE[task]}")
    return out


def usable(got: dict) -> bool:
    """Whether the confidence table SQX stored for this run can be read at all.

    Args:
        got: What provenance() returned.

    Returns:
        False when the run was cut short. SQX writes the table over the count it was asked
        for, so a run that stored 999 of 1000 has every rank in that table shifted by one.
        The simulations themselves are unharmed -- indices truncate at the tail and never
        gap -- so the reconstructed channel stays valid and only the stored one is lost.
    """
    return got["stored"] >= got["declared"]


def describe(task: str, got: dict) -> str:
    """One line naming the perturbation and the numbers it actually ran with.

    Args:
        task: One of TASKS.
        got: What provenance() returned.

    Returns:
        A sentence for the report, e.g. "Spread — randomises the spread charged on every
        trade (Min 5, Max 12); holds the strategy, the data, and every cost but the spread".
    """
    numbers = "; ".join(f"{m}: " + ", ".join(f"{k} {v}" for k, v in sorted(p.items()))
                        for m, p in sorted(got["methods"].items()))
    return (f"{TITLES[task]} — randomises {PERTURBS[task]} ({numbers}); "
            f"holds fixed {HOLDS_FIXED[task]}")
