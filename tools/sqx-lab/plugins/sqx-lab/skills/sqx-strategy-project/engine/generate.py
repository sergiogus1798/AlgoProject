r"""
generate.py — clone a build-144 SQX project (project.cfx) into a NEW project that
runs a chosen set of strategy templates as N build tasks.

Distilled from the BUILD-CONFIRMED one-off scripts (_attach_breakout_fleet.py +
_build_long_project.py), generalized and made install-parametric. Stays strictly
inside the proven mechanic — do not deviate without a fresh AlgoWizard build-confirm.

THE PROVEN MECHANIC
-------------------
A project.cfx is a ZIP:
    config.xml                  <- <Project><Tasks/><Databanks/></Project>
    Build-Task{N}.xml           <- one per build task; each EMBEDS ~3 MB of build settings
    GoToTask-Task1.xml          <- inactive helper task (verbatim)
    StopAndStart-Task1.xml      <- inactive helper task (verbatim)

To wire N tasks we CLONE one base Build-Task (bytes-level) per new task and swap ONLY:
    (a) <StrategyType ... templateFile="...">                 -> this task's .sqx (ABSOLUTE)
        — and type= is forced to "template". Donors ship type="simple", under which SQX
        ignores templateFile and builds generic random strategies with no error.
    (b) <Databank label="Output databank" name="Output" value="..."> -> this task's own databank
    (c) [optional] AvgTradesPerMonth acceptance numeric — and the enclosing <Condition>
        is forced use="true" (real donors ship it disabled; a number inside a disabled
        condition gates nothing)
    (d) [optional] <StopCondition ... minutes="..."> — and type= is forced to
        "time-limit" (the donor's "databank-full" ignores minutes=; enum confirmed from
        a GUI-built project on the reference install + the app's own enum table in
        internal/web/RESULTS2/result2.js: buildStopConditionTypes)
Everything else in the 3 MB stays byte-identical, so the donor task's data feed,
symbol, timeframe, exit stack, and acceptance settings are inherited unchanged.

config.xml is regenerated: the <Project> tag, the system databanks, and the inactive
(non-Build) tasks are PRESERVED from the base verbatim; the build <Task> entries and
their per-task <Databank> registrations are replaced with the N new ones.

GOTCHAS (load-bearing)
----------------------
* The OUTPUT databank lives INSIDE Build-Task{N}.xml (swap b), NOT in config.xml.
  config.xml's <Task title=> is only a DISPLAY label; cloning without swap (b) makes
  every task write to the donor's output databank.
* templateFile paths are ABSOLUTE (build-144 has no relative form) -> they are resolved
  against the TARGET install so the project is self-contained on that machine.
* SQX MUST be closed when deploying into an install (it rewrites project.cfx on close
  and will clobber the edits).
"""
import os
import re
import zipfile
import datetime as _dt
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr, escape

# --- the 5 always-present system databanks (preserved from the base by name) -----------
SYSTEM_DB = {
    "Results", "Last generation", "Initial population",
    "Strategies to improve", "Existing portfolio",
}


# --------------------------------------------------------------------------------------
# base-project reading
# --------------------------------------------------------------------------------------
def _section(root, tag):
    """The required <Tasks>/<Databanks> container, with a clear error if absent."""
    el = root.find(tag)
    if el is None:
        raise ValueError(f"malformed config.xml: no <{tag}> section")
    return el


def read_base(cfx_path):
    """Return {member_name: bytes} for every entry of a base project.cfx."""
    with zipfile.ZipFile(cfx_path) as z:
        return {n: z.read(n) for n in z.namelist()}


def base_build_tasks(members):
    """The Build-Task{N}.xml member names that back an active type="Build" task,
    in config order. Returns list of (config_Task_element, member_name)."""
    cfg = ET.fromstring(members["config.xml"].decode("utf-8"))
    out = []
    for t in _section(cfg, "Tasks").findall("Task"):
        if t.get("type") == "Build":
            out.append((t, t.get("taskXMLFile")))
    return out


# --------------------------------------------------------------------------------------
# per-task cloning (bytes-level, surgical — never reserialize the 3 MB)
# --------------------------------------------------------------------------------------
def _note(notes, msg, warn=False):
    """Record a human-readable note for the caller's report. WARNINGs also print to
    stdout immediately — never silent (silent failure is this engine's audit-confirmed
    worst defect class). `notes` may be None (direct low-level calls)."""
    if warn and not msg.startswith("WARNING"):
        msg = "WARNING: " + msg
    if warn:
        print(msg)
    if notes is not None:
        notes.append(msg)


def _find_rankings(task_bytes):
    """The task's single <Rankings> block (the generation acceptance) as a re.Match.
    A build task carries exactly one; the CrossCheck acceptance blocks (WF/MC/Retest)
    live OUTSIDE it, so everything scoped to this match can never touch them."""
    m = re.search(rb"<Rankings\b.*?</Rankings>", task_bytes, re.S)
    if not m:
        raise ValueError("the donor task has no <Rankings> block — is it a build task?")
    return m


def _set_condition_use(cond_seg, value):
    """Force use="<value>" on a <Condition …> segment's OPENING tag, attribute-order-
    insensitively (a donor writing `<Condition id="x" use="true">` is handled the same
    as `<Condition use="true">`). Returns (new_segment, changed: bool). A missing use=
    attribute is added (SQX always writes one, but never assume)."""
    om = re.match(rb"<Condition\b[^>]*>", cond_seg)
    tag = om.group(0)
    um = re.search(rb'\buse="([^"]*)"', tag)
    if um is None:
        head = len(b"<Condition")
        new_tag = tag[:head] + b' use="' + value + b'"' + tag[head:]
        return new_tag + cond_seg[om.end():], True
    if um.group(1) == value:
        return cond_seg, False
    new_tag = tag[:um.start(1)] + value + tag[um.end(1):]
    return new_tag + cond_seg[om.end():], True


def _rankings_conditions(block):
    """Iterate (match, left_side_class) over every <Condition> in a Rankings block.
    The class is read from the Left-Side (the acceptance column), attribute-order-
    insensitively. `<Conditions>`/`<ConditionsType>`/`<StopCondition>` cannot match:
    the pattern requires a word boundary after `<Condition` and a literal
    `</Condition>` closer."""
    for cm in re.finditer(rb"<Condition\b[^>]*>.*?</Condition>", block, re.S):
        seg = cm.group(0)
        left = re.search(rb"<Left-Side\b.*?</Left-Side>", seg, re.S)
        cls_m = re.search(rb'\bclass="([^"]*)"', left.group(0) if left else seg)
        yield cm, (cls_m.group(1) if cls_m else b"")


def _set_avg_trades(task_bytes, avg_trades, notes=None):
    """Set the AvgTradesPerMonth acceptance numeric AND make sure the enclosing
    <Condition> is use="true". Both real donors on the reference install ship every
    <Rankings> condition use="false" — writing the number alone (the old behaviour)
    reported "AvgTrades>N enforced" while the gate never applied."""
    m = _find_rankings(task_bytes)
    block = m.group(0)
    hit = None
    for cm, cls in _rankings_conditions(block):
        if cls == b"AvgTradesPerMonth":
            hit = cm
            break
    if hit is None:
        raise ValueError("avg-trades swap requested but the donor task's <Rankings> has "
                         "no AvgTradesPerMonth acceptance condition")
    seg = hit.group(0)
    val = str(avg_trades).encode("utf-8")
    seg, n = re.subn(rb'(<Right-Side valueType="numeric">\s*<Numeric-Value value=")[^"]*(")',
                     lambda mm: mm.group(1) + val + mm.group(2), seg, count=1)
    if n != 1:
        raise ValueError("avg-trades: the AvgTradesPerMonth condition has no numeric "
                         "right side to set")
    seg, flipped = _set_condition_use(seg, b"true")
    if flipped:
        _note(notes, "enabled AvgTradesPerMonth acceptance (donor had it disabled)")
    block = block[:hit.start()] + seg + block[hit.end():]
    return task_bytes[:m.start()] + block + task_bytes[m.end():]


GENERATION_TYPES = ("random-generation", "genetic-evolution")


def set_generation_type(task_bytes, gen_type):
    """Pin <BuildMode generationType=>.

    THIS IS A METHOD CHOICE, NOT A TUNING KNOB. `random-generation` draws each offspring
    independently from the declared space; `genetic-evolution` BREEDS toward fitness, so
    the surviving population is selected rather than sampled. A family statistic (median /
    survival / pooled t) computed over a bred population measures the search, not the
    template — which is the survivorship the acceptance-stripping exists to remove,
    reintroduced one layer upstream.

    Always written, never inherited: the donor carries whichever mode it happened to use,
    and a silent switch here would invalidate every family verdict without any error.
    (The genetic sub-settings — PopulationSize, Islands, Crossover… — stay in the XML under
    either mode; they are simply inert when the type is random-generation.)"""
    if gen_type not in GENERATION_TYPES:
        raise ValueError(f"generationType must be one of {GENERATION_TYPES}, got {gen_type!r}")
    new, n = re.subn(rb'(<BuildMode\b[^>]*\bgenerationType=")[^"]*(")',
                     lambda m: m.group(1) + gen_type.encode("utf-8") + m.group(2),
                     task_bytes, count=1)
    if n != 1:
        raise ValueError("no <BuildMode generationType=> in the donor task")
    return new


def clone_task(base_task_bytes, template_path, output_db,
               avg_trades=None, time_minutes=None, passed_strategies=None, notes=None):
    """Clone a donor Build-Task, swapping in this task's template + output databank
    (+ optional acceptance / stop condition). Returns the new task XML bytes;
    human-readable notes about donor-state corrections (e.g. "enabled
    AvgTradesPerMonth acceptance") are appended to `notes` when a list is passed.

    Raises if a mandatory swap (a, b) does not match exactly once — a loud failure
    is correct: it means the donor task is not a template-type build task.
    """
    tpl = template_path.encode("utf-8")
    odb = output_db.encode("utf-8")
    new = base_task_bytes

    # (a) attach the strategy template AND put the task into template mode.
    # type= is forced to "template": both real Builder donors ship type="simple", and
    # under "simple" SQX IGNORES templateFile entirely and builds generic random
    # strategies — the same donor-state trap as the disabled acceptance condition in
    # (c) and the "databank-full" stop condition in (d), but silent and far worse,
    # because the run looks successful. Enum confirmed from the user's own GUI-built
    # projects: 186 template-driven build tasks across the installs on this machine all
    # carry type="template", and every type="simple" task carries a stale templateFile
    # that SQX never reads.
    hit = re.search(rb'<StrategyType\b[^>]*>', new)
    if hit is None:
        raise ValueError("templateFile swap failed — donor task has no <StrategyType> "
                         "element; is it a build task?")
    el = hit.group(0)

    el, n = re.subn(rb'(\btemplateFile=")[^"]*(")',
                    lambda m: m.group(1) + tpl + m.group(2), el, count=1)
    if n != 1:
        raise ValueError("templateFile swap failed — donor <StrategyType> has no "
                         "templateFile= attribute; is it a template build task?")

    # \b keeps this off improveType=/subtype=-style attributes; the search is scoped to
    # the isolated element, so it does not depend on attribute order.
    was = re.search(rb'\btype="([^"]*)"', el)
    el, n = re.subn(rb'\btype="[^"]*"', b'type="template"', el, count=1)
    if n != 1:
        raise ValueError('donor <StrategyType> has no type= attribute — cannot put the '
                         'task into template mode; the attached template would be ignored')
    if was and was.group(1) != b"template":
        _note(notes, 'set <StrategyType type="template"> (donor was type='
                     f'"{was.group(1).decode("utf-8", "replace")}", under which SQX '
                     "ignores the attached template and builds generic strategies)")

    new = new[:hit.start()] + el + new[hit.end():]
    if tpl not in new:
        raise ValueError("templateFile swap failed — template path did not land in the "
                         "cloned task")

    # (b) point the OUTPUT databank at this task's own databank
    new, n = re.subn(rb'(<Databank label="Output databank" name="Output" value=")[^"]*(")',
                     lambda m: m.group(1) + odb + m.group(2), new, count=1)
    if n != 1:
        raise ValueError("output-databank swap failed — no "
                         '<Databank label="Output databank" name="Output"> in donor task')

    # (c) optional: AvgTradesPerMonth acceptance numeric + enable the condition
    if avg_trades is not None:
        new = _set_avg_trades(new, avg_trades, notes=notes)

    # (d) optional: per-task stop condition. From BuildStopConditionsChecker in TaskBuild.jar
    # there are FOUR types, each reading a different setting:
    #   time-limit     MaxBuildRunTime      vs taskRunningTime            (days/hours/minutes)
    #   passed-count   MaxStrategiesPassed  vs runInfo.strategiesAccepted (passedStrategies)
    #   databank-full  databankFilter.getMaxStrategies() vs databank.size()
    #   never
    # NOTE `databank-full` does NOT read passedStrategies — it compares the databank against
    # the RANKINGS cap. Setting it with a count is a silent no-op: the run then ends only when
    # the genetic search exhausts restartCount (confirmed the hard way 2026-07-26 — a
    # "10,000" budget produced 22,055 accepted in 22 min). `passed-count` is the equal-budget
    # type, and it counts ACCEPTED strategies — the same unit the ledger counts.
    # `type` decides which setting is read, so each setter writes BOTH type and value.
    if time_minutes is not None and passed_strategies is not None:
        raise ValueError("time_minutes and passed_strategies are mutually exclusive — "
                         "SQX honours whichever <StopCondition type=> names; pick one")

    if time_minutes is not None:
        m = re.search(rb'<StopCondition\b[^>]*\bminutes="\d+"[^>]*/?>', new)
        if not m:
            raise ValueError("time-limit swap requested but no <StopCondition minutes=> "
                             "was found in the donor task")
        tag = m.group(0)
        mins = str(int(time_minutes)).encode("utf-8")
        tag = re.subn(rb'(\bminutes=")\d+(")',
                      lambda mm: mm.group(1) + mins + mm.group(2), tag, count=1)[0]
        tm = re.search(rb'\btype="([^"]*)"', tag)
        if tm is None:
            _note(notes, "donor <StopCondition> has no type= attribute — the "
                         f"{time_minutes}-min cap may be inert; confirm the stop "
                         "condition in the GUI", warn=True)
        elif tm.group(1) != b"time-limit":
            old_type = tm.group(1).decode("utf-8", "replace")
            tag = tag[:tm.start(1)] + b"time-limit" + tag[tm.end(1):]
            _note(notes, f'time cap: set StopCondition type="time-limit" (donor had '
                         f'type="{old_type}", under which minutes= is ignored and the '
                         f'cap would be inert)')
        new = new[:m.start()] + tag + new[m.end():]

    # (d2) optional: equal-COUNT budget — stop after N ACCEPTED strategies (type=passed-count,
    # checked against runInfo.strategiesAccepted). This is the protocol's "equal generation
    # budget per (template x instrument)": a time-limit yields a different N on every
    # instrument (they backtest at different speeds), which confounds any cross-instrument
    # comparison. Accepted is also the unit the ledger counts, since acceptance is stripped
    # to the measurability floor.
    if passed_strategies is not None:
        new, n = re.subn(rb'(<StopCondition\b[^>]*\bpassedStrategies=")\d+(")',
                         (r'\g<1>%s\g<2>' % passed_strategies).encode("utf-8"), new, count=1)
        if n != 1:
            raise ValueError("passed-strategies swap requested but no <StopCondition "
                             "passedStrategies=> was found in the donor task")
        new, n = re.subn(rb'(<StopCondition\b[^>]*\btype=")[^"]*(")',
                         rb'\g<1>passed-count\g<2>', new, count=1)
        if n != 1:
            raise ValueError("no <StopCondition type=> in the donor task")
        # Zero the donor's leftover clock. `type` is supposed to select which attribute is
        # read, but a stale minutes= that SQX also honoured would silently cap the run
        # short of the count — reintroducing the unequal budget this setter exists to
        # remove, invisibly. Zeroed, the count is the only stop; a template that cannot
        # reach it hangs loudly and the runner's wall-clock timeout catches it.
        new = re.sub(rb'(<StopCondition\b[^>]*\b)(days|hours|minutes)(=")\d+(")',
                     rb'\g<1>\g<2>\g<3>0\g<4>', new)

    # (e) multi-timeframe template support (empirically derived 2026-07-18, XAUUSD gold wave):
    # an MTF template declares a 2nd data stream (<data><timeFrame>1440</timeFrame>) that a
    # 1-chart donor task cannot satisfy. Three independent pieces are required, found by bytecode
    # inspection of BlockSettingsConverter + live-run confirmation:
    #   1. a 2nd <Chart> in EVERY <Setup> (data provisioning; fixes the hard error
    #      "Strategy from template file requires 2 charts, 1 defined" — both IS and OOS
    #      Setups count, patching only one leaves the error in place),
    #   2. a 2nd <data> stream entry in the task's <Datas> mapping,
    #   3. a 2nd <Chart> under <RulesComplexity> — THIS is the list
    #      BlockSettingsConverter.convertToCharts() builds the builder's chart index from;
    #      without it every #Chart#=1 random-group binding silently degrades to the main
    #      chart ("Random group uses chart index 1, but there are not enough charts").
    # NOTE: applied by make_project AFTER apply_overrides (set_instrument/set_timeframe
    # rewrite every data <Chart timeframe=> and would flatten the inserted chart).
    return new


_TF_NAME = {240: "H4", 1440: "D1", 10080: "W1"}


def ensure_mtf_charts(task_bytes, template_path, notes=None):
    """If the template at `template_path` declares extra data streams, make the task
    2-chart-capable (see clone_task step (e)). No-op for single-stream templates.
    Donor-shape caveats about the task-level <Datas> section are appended to `notes`."""
    import zipfile
    try:
        with zipfile.ZipFile(template_path) as z:
            tpl = z.read("strategy_Portfolio.xml")
    except Exception:
        return task_bytes  # template unreadable here — leave the task as the donor had it
    extra_tfs = [int(t) for t in re.findall(rb"<timeFrame>(\d+)</timeFrame>", tpl)
                 if int(t) > 0]
    if not extra_tfs:
        return task_bytes
    new = task_bytes
    for tf in extra_tfs:
        tf_name = _TF_NAME.get(tf)
        if tf_name is None:
            raise ValueError(f"MTF template stream timeframe {tf} min has no chart-name "
                             f"mapping yet — extend _TF_NAME")
        if (b'timeframe="%s"' % tf_name.encode()) in new:
            continue  # this stream's chart already present
        # 1) sibling chart in every Setup
        new, n = re.subn(
            rb'(<Chart symbol="([^"]+)" timeframe="[^"]+" spread="([^"]+)" />)',
            (r'\g<1>\n        <Chart symbol="\g<2>" timeframe="%s" spread="\g<3>" />'
             % tf_name).encode(),
            new)
        if n < 1:
            raise ValueError("MTF chart insert failed — no <Chart symbol=…/> in Setups")
        # 2) 2nd data stream entry — ONLY for donors that carry a task-level <Datas>.
        # Donor shapes differ: 177 of the 232 build tasks on the reference machine have a
        # <Datas> block, 55 (including the stock 144.2953 Builder) have none at all. The
        # template declares its own streams in strategy_Portfolio.xml, so the <Datas>-less
        # donor still yields correct multi-timeframe strategies.
        # BUILD-CONFIRMED 2026-07-31 on the <Datas>-less 144.2953 Builder donor: of the
        # strategies the fleet generated, every MTF_* one carries TWO data streams
        # (timeFrame 0 + 1440, "Main chart" + "Subchart 1") and every non-MTF one carries
        # exactly one — 40/40 each way. So the note below records which path was taken; it
        # is no longer a warning about an unverified shape.
        if re.search(rb"</data>\s*</Datas>", new):
            entry = (b"</data>\n            <data>\n              <id>1</id>\n"
                     b"              <symbol>NULL</symbol>\n"
                     b"              <chart>Main chart</chart>\n"
                     b"              <timeFrame>%d</timeFrame>\n"
                     b"            </data>\n          </Datas>" % tf)
            new, n = re.subn(rb"</data>\s*</Datas>", entry, new, count=1)
            if n != 1:
                raise ValueError("MTF <data> stream insert failed — <Datas> present but "
                                 "its final </data></Datas> pair did not match once")
        elif b"<Datas" in new:
            raise ValueError("MTF <data> stream insert failed — the task has a <Datas> "
                             "section in an unexpected shape; refusing to guess")
        else:
            _note(notes,
                  f"MTF: donor task carries no <Datas> section, so the {tf_name} stream is "
                  f"wired via the Setup chart + RulesComplexity chart and the template's own "
                  f"stream declaration (build-confirmed 2026-07-31: generated MTF strategies "
                  f"carry both streams).")
        # 3) 2nd RulesComplexity chart (the builder's actual chart index list)
        new, n = re.subn(
            rb'(<Chart name="Main chart"([^>]*)/>\s*)(</RulesComplexity>)',
            (r'\g<1><Chart name="%s chart"\g<2>/>\n    \g<3>' % tf_name).encode(),
            new, count=1)
        if n != 1:
            raise ValueError("MTF RulesComplexity chart insert failed")
    return new


# --------------------------------------------------------------------------------------
# per-task OVERRIDES — instrument / dates / trading options (build-confirmed 2026-07-11)
# --------------------------------------------------------------------------------------
# These promote fields the base clone would otherwise inherit unchanged into settable
# holes. Each is a byte-surgical swap with an asserted match count (loud failure on any
# drift), matching the discipline of clone_task's (a)/(b) swaps. Empirically confirmed:
# switching the symbol string is enough — SQX re-resolves tickSize/pointValue/swap/
# commissions from its data manager on project LOAD (probe: index->EURUSD healed every
# money field). What SQX does NOT heal and we therefore set explicitly: <Chart spread>
# and the epoch <Symbol dateFrom/dateTo> range. See docs/custom-project-authoring.md.

def _norm_ymd(d):
    """'2012-01-01' | '2012.01.01' | datetime.date -> 'YYYY.MM.DD'."""
    if isinstance(d, (_dt.date, _dt.datetime)):
        return d.strftime("%Y.%m.%d")
    s = str(d).strip().replace("-", ".").replace("/", ".")
    y, m, day = s.split(".")
    return f"{int(y):04d}.{int(m):02d}.{int(day):02d}"


def _ymd_to_ms(ymd):
    """'YYYY.MM.DD' -> epoch ms at UTC midnight (SQX stores the data range this way)."""
    y, m, d = (int(x) for x in ymd.split("."))
    return int(_dt.datetime(y, m, d, tzinfo=_dt.timezone.utc).timestamp() * 1000)


def detect_instrument(task_bytes):
    """Return (symbol, instrument_id) currently wired in a task, from the data <Chart>
    and the Resources <InstrumentInfo>. Used to auto-target the swap."""
    sym = re.search(rb'<Chart symbol="([^"]*)" timeframe="[^"]*" spread="[^"]*" />', task_bytes)
    ins = re.search(rb'<InstrumentInfo\b[^>]*\binstrument="([^"]*)"', task_bytes)
    return (sym.group(1).decode() if sym else None,
            ins.group(1).decode() if ins else None)


# <Symbol source=> / <Symbol broker=> identify WHICH data provider SQX resolves the symbol
# against. They are NOT cosmetic: a symbol name from one provider with another provider's
# source code is a contradiction — SQX looks the name up in the wrong catalogue, finds
# nothing, and silently leaves the whole <InstrumentInfo> at the donor's values (wrong
# tickSize, wrong tick economics). No error is raised. Confirmed 2026-07-27: ICM index
# symbols deployed with a Dukascopy donor's source=2/broker=3 kept tickSize=0.001 and
# defaultSpread=1503.0 from the donor instead of resolving.
# Codes observed across working projects on the install:
SOURCE_BROKER = {
    "dukascopy": (2, 3),
    "dukas":     (2, 3),
    "ICM":       (1, 5),
    "MT5":       (1, -1),   # *_Darwinex_MT5
}


def source_broker_for(symbol):
    """(source, broker) for a data-key symbol like 'USTEC_M1_ICM', or None if unknown."""
    for suffix, pair in SOURCE_BROKER.items():
        if symbol.endswith("_" + suffix):
            return pair
    return None


def set_source_broker(task_bytes, source, broker):
    """Point every data <Symbol> at the provider that actually holds the symbol."""
    new, n = re.subn(rb'(<Symbol\b[^>]*\bsource=")[^"]*(")',
                     (r'\g<1>%s\g<2>' % source).encode("utf-8"), task_bytes)
    if n < 1:
        raise ValueError("set_source_broker: no <Symbol source=> found")
    new, k = re.subn(rb'(<Symbol\b[^>]*\bbroker=")[^"]*(")',
                     (r'\g<1>%s\g<2>' % broker).encode("utf-8"), new)
    if k != n:
        raise ValueError(f"set_source_broker: {n} source= but {k} broker= — malformed")
    return new


def set_instrument(task_bytes, new_symbol, new_instrument,
                   old_symbol=None, old_instrument=None, timeframe=None,
                   usymbol="", usymbol_name="", source=None, broker=None, notes=None):
    """Repoint a task at a different instrument, with ANCHORED substitutions only —
    never a global byte replace. The symbol string is swapped exclusively inside its
    three legitimate contexts:
        symbol="…"        (the data <Chart> in every Setup, or any symbol= attribute)
        <Symbol name="…"  (the Resources symbol registry entry)
        <symbol>…</symbol> (a <Datas> data-entry element)
    and the instrument id exclusively inside instrument="…" attributes. This makes the
    swap correct even when the donor ALIASES the two (symbol string == instrument id,
    e.g. AUDJPY_M1_FOREX as both — a global replace left the instrument id pointing at
    the new SYMBOL and never applied `new_instrument`), and it can no longer corrupt
    unrelated text that merely contains a short id like "NQ".

    Each substitution class is counted; the swap requires >=1 symbol context and >=1
    instrument context, and the counts are recorded in `notes`. If the donor carries
    charts on OTHER symbols (a 2-chart donor), only the primary is swapped and a
    WARNING naming the untouched foreign symbols/instruments is recorded + printed.

    SQX heals the money metadata on load. `old_*` auto-detected from the task if
    omitted. Optional timeframe rewrites every data <Chart timeframe=>. `source`/
    `broker` repoint the data provider (see set_source_broker); when omitted they are
    inferred from the new symbol's data-key suffix.

    CRITICAL: also rewrites the data <Symbol> element's `uSymbol`/`uSymbolName` — SQX's
    real underlying-instrument RESOLVER key. The donor carries the base project's
    underlying (e.g. `uSymbol="USATECHIDXUSD"`); if left unchanged when the symbol switches
    it MISMATCHES the new instrument and SQX loads the project with "unresolved resources".
    GUI-authored projects leave these EMPTY and resolve via symbol+instrument, so we
    default to empty (build-confirmed 2026-07-11). Pass usymbol/usymbol_name to set them
    explicitly (e.g. the data manager's Instrument-column value) if a donor/source needs it."""
    ds, di = detect_instrument(task_bytes)
    old_symbol = old_symbol or ds
    old_instrument = old_instrument or di
    if not old_symbol or not old_instrument:
        raise ValueError("set_instrument: could not detect donor symbol/instrument")
    new = task_bytes
    osym = re.escape(old_symbol.encode("utf-8"))
    oins = re.escape(old_instrument.encode("utf-8"))
    nsym = new_symbol.encode("utf-8")
    nins = new_instrument.encode("utf-8")

    # (1) symbol="…" attribute contexts. (?<!\w) keeps uSymbol=/chartSymbol=-style
    #     attributes out; attribute names are case-sensitive.
    new, n_sym_attr = re.subn(rb'((?<!\w)symbol=")' + osym + rb'(")',
                              lambda m: m.group(1) + nsym + m.group(2), new)
    # (2) the Resources <Symbol name="…"> registry entry
    new, n_sym_name = re.subn(rb'(<Symbol\b[^>]*?\bname=")' + osym + rb'(")',
                              lambda m: m.group(1) + nsym + m.group(2), new)
    # (3) <symbol>…</symbol> data-entry elements (the <Datas> mapping)
    new, n_sym_data = re.subn(rb'(<symbol>)' + osym + rb'(</symbol>)',
                              lambda m: m.group(1) + nsym + m.group(2), new)
    # (4) instrument="…" attribute contexts (InstrumentInfo in Datas + Resources)
    new, n_ins = re.subn(rb'((?<!\w)instrument=")' + oins + rb'(")',
                         lambda m: m.group(1) + nins + m.group(2), new)

    if (n_sym_attr + n_sym_name + n_sym_data) < 1 or n_ins < 1:
        raise ValueError(
            f"set_instrument: donor symbol/instrument not found in any anchored context "
            f"(symbol {old_symbol!r}: {n_sym_attr} attribute / {n_sym_name} registry / "
            f"{n_sym_data} data contexts; instrument {old_instrument!r}: {n_ins} contexts)")
    _note(notes, f"set_instrument: symbol {old_symbol} -> {new_symbol} in {n_sym_attr} "
                 f"attribute + {n_sym_name} registry + {n_sym_data} data context(s); "
                 f"instrument {old_instrument} -> {new_instrument} in {n_ins} context(s)")

    # foreign markets the donor also charts — deliberately left untouched, loudly
    foreign_syms = sorted({s.decode("utf-8", "replace")
                           for s in re.findall(rb'<Chart symbol="([^"]*)"', new)
                           if s != nsym})
    foreign_ins = sorted({s.decode("utf-8", "replace")
                          for s in re.findall(rb'(?<!\w)instrument="([^"]*)"', new)
                          if s != nins})
    if foreign_syms or foreign_ins:
        _note(notes, "set_instrument: donor task also charts OTHER symbol(s) that were "
                     "left untouched: "
                     + ", ".join(foreign_syms + [f"(instrument {i})" for i in foreign_ins])
                     + " — the extra chart keeps its original market; re-point it in "
                     "the GUI if that is not intended", warn=True)

    # uSymbol / uSymbolName on the data <Symbol> — the loader's underlying resolver.
    # Present once (older donors may lack it, so matches are not asserted).
    new = re.subn(rb'(\buSymbol=")[^"]*(")',
                  lambda m: m.group(1) + usymbol.encode("utf-8") + m.group(2), new)[0]
    new = re.subn(rb'(\buSymbolName=")[^"]*(")',
                  lambda m: m.group(1) + usymbol_name.encode("utf-8") + m.group(2), new)[0]

    # Repoint the provider to whoever actually holds the new symbol. Explicit args win;
    # otherwise infer from the data-key suffix. Unknown suffix -> leave the donor's codes
    # and say so, rather than guessing a provider.
    if source is None or broker is None:
        pair = source_broker_for(new_symbol)
        if pair:
            source = pair[0] if source is None else source
            broker = pair[1] if broker is None else broker
        else:
            _note(notes, f"set_instrument: unknown data source for {new_symbol!r} — "
                         "leaving the donor's <Symbol source/broker>. If the provider "
                         "differs, InstrumentInfo will NOT resolve and tick economics "
                         "stay at the donor's values.", warn=True)
    if source is not None and broker is not None:
        new = set_source_broker(new, source, broker)

    if timeframe is not None:
        tf = str(timeframe).encode("utf-8")
        new, n = re.subn(rb'(<Chart symbol="[^"]*" timeframe=")[^"]*(" spread=)',
                         lambda m: m.group(1) + tf + m.group(2), new)
        if n < 1:
            raise ValueError("set_instrument: timeframe requested but no data <Chart> matched")
    return new


def set_timeframe(task_bytes, timeframe):
    """Change the chart timeframe (e.g. 'M30') WITHOUT switching instrument. Rewrites
    every data <Chart ... timeframe=> (2x normal / 4x MTF). SQX resamples from the M1
    base data. Asserts at least one match."""
    new, n = re.subn(rb'(<Chart symbol="[^"]*" timeframe=")[^"]*(" spread=)',
                     (r'\g<1>%s\g<2>' % timeframe).encode(), task_bytes)
    if n < 1:
        raise ValueError("set_timeframe: no data <Chart timeframe=> matched")
    return new


def set_dates(task_bytes, date_from, date_to):
    """Set the backtest/IS window on the <Data><Setups> setup ONLY (never the disabled
    cross-check retest setup). Rewrites the human YYYY.MM.DD Setup range AND the epoch-ms
    Resources <Symbol> availability range. Match count is asserted == 1 each."""
    frm, to = _norm_ymd(date_from), _norm_ymd(date_to)
    if _ymd_to_ms(frm) >= _ymd_to_ms(to):
        raise ValueError(f"set_dates: from ({frm}) must be before to ({to})")
    new = task_bytes

    # (1) the DATA setup: anchor on <Data><Setups><Setup ...> so the inverted/empty
    #     CrossChecks retest setup is never touched.
    new, n = re.subn(
        rb'(<Data>\s*<Setups>\s*<Setup\b[^>]*\bdateFrom=")[^"]*(" dateTo=")[^"]*(")',
        (r'\g<1>%s\g<2>%s\g<3>' % (frm, to)).encode(), new, count=1)
    if n != 1:
        raise ValueError("set_dates: the <Data><Setups> setup was not found exactly once")

    # (2) the epoch data-availability range on the Resources <Symbol>
    new, n = re.subn(
        rb'(<Symbol\b[^>]*\bdateFrom=")\d{10,}(" dateTo=")\d{10,}(")',
        (r'\g<1>%d\g<2>%d\g<3>' % (_ymd_to_ms(frm), _ymd_to_ms(to))).encode(), new, count=1)
    if n != 1:
        raise ValueError("set_dates: the Resources <Symbol> epoch range was not found once")
    return new


def set_oos_ranges(task_bytes, ranges):
    r"""Declare SQX's out-of-sample slice(s) on the build task's <Data><OutOfSample>.

    SEMANTICS (from internal/plugins/SettingsData/DataService.js — load :98-113, save :637-643):
    the <Data><Setups><Setup dateFrom dateTo> range is the WHOLE backtest window; each
    <Range> element CARVES A HOLDOUT OUT OF IT. The builder evolves on the remainder (IS)
    and reports the carved part separately as OOS. So the caller must have set the Setup
    span to IS+OOS (set_dates) BEFORE calling this — a Range outside the Setup span is
    silently dropped by SQX's recalculateOOSRanges().

    `ranges` = [{"from": "2021-02-01", "to": "2024-06-30"}, …] (max 20, DataService.MaxRanges).
    `type` is omitted on purpose: DataService writes the attribute only when type != 'oos',
    so an absent attribute IS 'oos'.

    The donor's element is the empty self-closing form `<OutOfSample showGraph="…" />`;
    both that and an already-populated paired form are handled. Returns rewritten bytes."""
    if not ranges:
        return task_bytes
    if len(ranges) > 20:
        raise ValueError(f"set_oos_ranges: {len(ranges)} ranges exceeds DataService.MaxRanges (20)")

    # the Setup span these ranges must fit inside (assert, don't silently lose the holdout)
    m = re.search(rb'<Data>\s*<Setups>\s*<Setup\b[^>]*\bdateFrom="([^"]*)" dateTo="([^"]*)"', task_bytes)
    if not m:
        raise ValueError("set_oos_ranges: could not read the <Data><Setups> Setup span")
    span_from, span_to = m.group(1).decode(), m.group(2).decode()

    body = []
    for r in ranges:
        frm, to = _norm_ymd(r["from"]), _norm_ymd(r["to"])
        if _ymd_to_ms(frm) >= _ymd_to_ms(to):
            raise ValueError(f"set_oos_ranges: from ({frm}) must be before to ({to})")
        if _ymd_to_ms(frm) < _ymd_to_ms(span_from) or _ymd_to_ms(to) > _ymd_to_ms(span_to):
            raise ValueError(
                f"set_oos_ranges: OOS range {frm}..{to} falls outside the Setup span "
                f"{span_from}..{span_to} — SQX would drop it. Widen the Setup (set_dates) "
                "to cover IS+OOS first.")
        body.append(f'<Range dateFrom="{frm}" dateTo="{to}" />')
    inner = "".join(body).encode()

    # (a) empty self-closing donor form -> paired form carrying the ranges
    new, n = re.subn(rb'<OutOfSample\b([^>]*?)\s*/>',
                     rb'<OutOfSample\g<1>>' + inner + rb'</OutOfSample>', task_bytes, count=1)
    if n != 1:
        # (b) already paired (re-run over a previously-stamped task): replace its children
        new, n = re.subn(rb'(<OutOfSample\b[^>]*>).*?(</OutOfSample>)',
                         rb'\g<1>' + inner + rb'\g<2>', task_bytes, count=1, flags=re.S)
    if n != 1:
        raise ValueError("set_oos_ranges: no <OutOfSample> element found in the task")
    return new


def set_crosschecks(task_bytes, additional_markets=None, annotation_only=True,
                    date_from=None, date_to=None):
    r"""Wire SQX's RetestOnAdditionalMarkets cross-check (the "other markets" robustness
    retest) and flip the CrossChecks master switch on.

    SCHEMA (donor-derived, build 144): <CrossChecks use= evaluateAll=> holds one element per
    check; a check runs only when BOTH the master and its own use="true". The donor ships
    RetestOnAdditionalMarkets use="true" but the master use="false", plus ONE placeholder
    <Setup> with INVERTED dates (2023.01.01 -> 2022.12.31 = disabled). We replace the whole
    <Setups> body with one <Setup> per requested market.

    `additional_markets` = [{"symbol", "instrument_id"(unused here, kept for symmetry),
                             "timeframe", "spread", "swap"(optional dict|False)}, …]

    ANNOTATION-ONLY (default): every <Condition> under this check is forced use="false" and
    <MinConditions> to 0, so the retest COMPUTES per-strategy results without rejecting
    anything. This matters — cross-check acceptance filters the databank, which would
    re-introduce exactly the survivorship that stripping the Rankings conditions removed.

    SWAP: the donor's <Swap> carries the MAIN symbol's numbers (EURUSD long=-3421.39). Those
    are wrong for any other market and SQX does not heal them on a cross-check setup, so swap
    is DISABLED per additional market unless the caller passes an explicit swap dict. Spread
    must be given per market for the same reason (SQX heals tickSize/pointValue, never spread).

    Raises if a second cross-check is already use="true" (flipping the master would silently
    enable it too). Returns rewritten bytes."""
    if not additional_markets:
        return task_bytes

    i = task_bytes.find(b"<CrossChecks")
    j = task_bytes.find(b"</CrossChecks>")
    if i < 0 or j < 0:
        raise ValueError("set_crosschecks: no <CrossChecks> block in the task")
    block = task_bytes[i:j]

    # guard: flipping the master must not switch on anything we did not ask for
    others = [n.decode() for n, u in re.findall(rb'<([A-Za-z0-9_]+) use="(\w+)"', block)
              if u == b"true" and n not in (b"CrossChecks", b"RetestOnAdditionalMarkets")]
    # (the regex also catches nested <Method use=> etc.; keep only known top-level checks)
    KNOWN = {"WalkForwardOptimization", "RetestWithHigherPrecision", "MonteCarloRetest",
             "WalkForwardMatrix", "MonteCarloManipulation", "OptProfileSysParamPermutation",
             "WhatIf", "SequentialOptimization"}
    live = sorted(set(others) & KNOWN)
    if live:
        raise ValueError(
            f"set_crosschecks: refusing to flip the CrossChecks master — these checks are "
            f"already use=\"true\" and would start running too: {live}")

    ri = task_bytes.find(b"<RetestOnAdditionalMarkets")
    rj = task_bytes.find(b"</RetestOnAdditionalMarkets>")
    if ri < 0 or rj < 0:
        raise ValueError("set_crosschecks: RetestOnAdditionalMarkets element not found")
    rblock = task_bytes[ri:rj]

    # reuse the donor Setup's engine/session/precision attributes verbatim; only the market,
    # the dates and the economics change
    m = re.search(rb'<Setup\b([^>]*?)>', rblock)
    if not m:
        raise ValueError("set_crosschecks: no placeholder <Setup> to derive attributes from")
    attrs = m.group(1).decode()
    for k in ("dateFrom", "dateTo"):
        attrs = re.sub(rf'\s*{k}="[^"]*"', "", attrs)
    commissions = re.search(rb'<Commissions>.*?</Commissions>', rblock, re.S)
    mtv = re.search(rb'<MainTestValues\b[^>]*/>', rblock)

    setups = []
    for mk in additional_markets:
        if not mk.get("spread"):
            raise ValueError(f"set_crosschecks: market {mk.get('symbol')!r} needs an explicit "
                             "'spread' — SQX never heals <Chart spread> on an instrument swap")
        d_from = _norm_ymd(mk.get("from") or date_from)
        d_to = _norm_ymd(mk.get("to") or date_to)
        if _ymd_to_ms(d_from) >= _ymd_to_ms(d_to):
            raise ValueError(f"set_crosschecks: {mk['symbol']} from {d_from} >= to {d_to}")
        swap = mk.get("swap")
        swap_xml = ('<Swap use="false" type="points" long="0" short="0" '
                    'tripleSwapOn="NEVER" rolloutHour="23:00" />') if not swap else (
            '<Swap use="true" type="{type}" long="{long}" short="{short}" '
            'tripleSwapOn="{tripleSwapOn}" rolloutHour="{rolloutHour}" />'.format(
                **{"type": "points", "tripleSwapOn": "NEVER", "rolloutHour": "23:00", **swap}))
        setups.append(
            f'<Setup dateFrom="{d_from}" dateTo="{d_to}"{attrs}>'
            f'<Chart symbol="{mk["symbol"]}" timeframe="{mk.get("timeframe", "H1")}" '
            f'spread="{mk["spread"]}" />'
            + (commissions.group(0).decode() if commissions else "")
            + swap_xml
            + (mtv.group(0).decode() if mtv else "")
            + '</Setup>')

    new_r, n = re.subn(rb'(<Setups\b[^>]*>).*?(</Setups>)',
                       lambda _m: _m.group(1) + "".join(setups).encode() + _m.group(2),
                       rblock, count=1, flags=re.S)
    if n != 1:
        raise ValueError("set_crosschecks: could not replace the <Setups> body")

    if annotation_only:
        # neutralise this check's acceptance so it annotates instead of filtering
        def _neutralise(mm):
            body = re.sub(rb'<Condition use="true">', b'<Condition use="false">', mm.group(0))
            return re.sub(rb'<MinConditions>\d+</MinConditions>',
                          b"<MinConditions>0</MinConditions>", body)
        new_r, na = re.subn(rb'<AcceptanceSettings>.*?</AcceptanceSettings>',
                            _neutralise, new_r, count=1, flags=re.S)
        if na != 1:
            raise ValueError("set_crosschecks: AcceptanceSettings block not found")

    new = task_bytes[:ri] + new_r + task_bytes[rj:]

    # finally flip the master switch on
    new, nm = re.subn(rb'(<CrossChecks\b[^>]*?\buse=")false(")', rb'\g<1>true\g<2>', new, count=1)
    if nm != 1 and b'<CrossChecks use="true"' not in new:
        raise ValueError("set_crosschecks: could not flip the CrossChecks master switch")
    return new


def _hms_to_secs(t):
    """'08:00' | '8' | '08:00:00' | int seconds -> seconds-of-day (SQX SignalTimeRange unit)."""
    if isinstance(t, (int, float)):
        return int(t)
    parts = [int(x) for x in str(t).strip().split(":")]
    parts += [0] * (3 - len(parts))          # H | H:M | H:M:S
    h, m, s = parts[:3]
    return h * 3600 + m * 60 + s


def set_time_range(task_bytes, time_from=None, time_to=None, exit_at_end=None,
                   order_type_to_exit=None, enabled=True):
    """Enable the builder task's "Limit time range" trading option and set the intraday
    signal window (LimitTimeRange=true, SignalTimeRangeFrom/To in seconds-of-day). This
    is the per-builder-task BuildTradingOptions setting — NOT a named session and NOT a
    strategy block. `time_from`/`time_to` accept 'HH:MM' or seconds. Optional
    `exit_at_end` toggles ExitAtEndOfRange; `order_type_to_exit` selects WHICH orders are
    closed at end of range — the GUI's "Order types to close" = All / Live / Pending
    (int enum; donor default = 0. Confirm the 0/1/2 -> All/Live/Pending mapping in the GUI
    before relying on a non-default value). Each Param matches once.
    `enabled=False` DISABLES the window (LimitTimeRange=false), e.g. to strip a donor's
    intraday window from a swing project; times are ignored in that case."""
    new = task_bytes

    def _param(b, key, value):
        b2, n = re.subn(
            (r'(<Param key="%s" className="LimitTimeRange">)[^<]*(</Param>)' % key).encode(),
            (r'\g<1>%s\g<2>' % value).encode(), b, count=1)
        if n != 1:
            raise ValueError(f"set_time_range: <Param {key}> not found once")
        return b2

    if not enabled:
        return _param(new, "LimitTimeRange", "false")
    frm, to = _hms_to_secs(time_from), _hms_to_secs(time_to)
    new = _param(new, "LimitTimeRange", "true")
    new = _param(new, "SignalTimeRangeFrom", frm)
    new = _param(new, "SignalTimeRangeTo", to)
    if exit_at_end is not None:
        new = _param(new, "ExitAtEndOfRange", "true" if exit_at_end else "false")
    if order_type_to_exit is not None:
        new = _param(new, "OrderTypeToExit", int(order_type_to_exit))
    return new


def set_friday_exit(task_bytes, exit_time=None, enabled=True):
    """Toggle the builder task's "Exit on Friday" trading option and set its time-of-day
    (close open positions before the weekend). SQX stores this as two Params both under
    className="ExitOnFriday": the boolean `ExitOnFriday` and `FridayExitTime` in
    seconds-of-day (72000 = 20:00). `exit_time` accepts 'HH:MM' or seconds; omit to leave
    the donor time and only flip the flag. Each touched Param is asserted to match once."""
    new = task_bytes

    def _param(b, key, value):
        b2, n = re.subn(
            (r'(<Param key="%s" className="ExitOnFriday">)[^<]*(</Param>)' % key).encode(),
            (r'\g<1>%s\g<2>' % value).encode(), b, count=1)
        if n != 1:
            raise ValueError(f"set_friday_exit: <Param {key}> not found once")
        return b2

    new = _param(new, "ExitOnFriday", "true" if enabled else "false")
    if enabled and exit_time is not None:
        new = _param(new, "FridayExitTime", _hms_to_secs(exit_time))
    return new


def set_swap(task_bytes, enabled=False, long=None, short=None):
    """Turn overnight swap on/off on EVERY <Swap> element in the task.

    WHY THIS IS NOT OPTIONAL. SQX heals tickSize/pointValue on an instrument switch but it
    does NOT heal <Swap> — exactly like <Chart spread>. The donor's swap numbers therefore
    leak onto whatever symbol you switch to. A donor built on an index CFD carries values
    like long="-3421.39" short="1385.57" (points), and those get charged against every
    overnight position on, say, EURUSD. It is silent: no error, no warning, and it shows up
    only as inexplicably bad performance concentrated in the direction with the negative leg.

    Disabling also ZEROES the numbers, so a later accidental use="true" cannot resurrect the
    donor's values. Pass enabled=True with explicit long/short to model real financing.

    Matches ALL occurrences (a task has one <Swap> per Setup — main and out-of-sample)."""
    new = task_bytes
    flag = b"true" if enabled else b"false"
    new, n = re.subn(rb'(<Swap\b[^>]*\buse=")[^"]*(")',
                     lambda m: m.group(1) + flag + m.group(2), new)
    if n < 1:
        raise ValueError("set_swap: no <Swap use=> element found in the task")
    lo = "0.0" if (not enabled and long is None) else long
    sh = "0.0" if (not enabled and short is None) else short
    if lo is not None:
        new, k = re.subn(rb'(<Swap\b[^>]*\blong=")[^"]*(")',
                         (r'\g<1>%s\g<2>' % lo).encode("utf-8"), new)
        if k != n:
            raise ValueError(f"set_swap: matched {n} <Swap use=> but {k} long= — malformed")
    if sh is not None:
        new, k = re.subn(rb'(<Swap\b[^>]*\bshort=")[^"]*(")',
                         (r'\g<1>%s\g<2>' % sh).encode("utf-8"), new)
        if k != n:
            raise ValueError(f"set_swap: matched {n} <Swap use=> but {k} short= — malformed")
    return new


def set_trading_options(task_bytes, spread=None, slippage=None, session=None,
                        market_side=None, time_range=None, friday_exit=None, swap=None):
    """Set per-run trading options SQX does not inherit/heal for us. Each provided knob
    is asserted to match; None = leave the donor value. `spread` updates every data
    <Chart> (2x/4x); `slippage`/`session` update the <Data> setup; `market_side`
    (long|short|both) updates <MarketSides type=>; `time_range` = {"from","to"[,"exit_at_end"]}
    enables the builder task "Limit time range" window (per multiple builder tasks);
    `friday_exit` = {"exit_time","enabled"} toggles the "Exit on Friday" weekend-flat
    option ("exit_time" is the documented key; the legacy "time" key is also accepted,
    "exit_time" winning when both are present); `swap` = False (or
    {"enabled","long","short"}) controls overnight swap — see set_swap: the donor's
    swap LEAKS onto a switched instrument exactly like spread does."""
    new = task_bytes
    if swap is not None:
        if isinstance(swap, dict):
            new = set_swap(new, enabled=swap.get("enabled", False),
                           long=swap.get("long"), short=swap.get("short"))
        else:
            new = set_swap(new, enabled=bool(swap))
    if time_range is not None:
        new = set_time_range(new, time_range.get("from"), time_range.get("to"),
                             exit_at_end=time_range.get("exit_at_end"),
                             order_type_to_exit=time_range.get("order_type_to_exit"),
                             enabled=time_range.get("enabled", True))
    if friday_exit is not None:
        fx_time = friday_exit.get("exit_time")     # the key SKILL.md documents
        if fx_time is None:
            fx_time = friday_exit.get("time")      # legacy key — kept working
        new = set_friday_exit(new, exit_time=fx_time,
                              enabled=friday_exit.get("enabled", True))
    if spread is not None:
        new, n = re.subn(rb'(<Chart symbol="[^"]*" timeframe="[^"]*" spread=")[^"]*(" />)',
                         (r'\g<1>%s\g<2>' % spread).encode(), new)
        if n < 1:
            raise ValueError("set_trading_options: no data <Chart spread=> matched")
    if slippage is not None:
        new, n = re.subn(rb'(<Setup\b[^>]*\bslippage=")[^"]*(")',
                         (r'\g<1>%s\g<2>' % slippage).encode(), new, count=1)
        if n != 1:
            raise ValueError("set_trading_options: <Setup slippage=> not found once")
    if session is not None:
        new, n = re.subn(rb'(<Setup\b[^>]*\bsession=")[^"]*(")',
                         (r'\g<1>%s\g<2>' % session).encode(), new, count=1)
        if n != 1:
            raise ValueError("set_trading_options: <Setup session=> not found once")
    if market_side is not None:
        new, n = re.subn(rb'(<MarketSides type=")[^"]*(")',
                         (r'\g<1>%s\g<2>' % market_side).encode(), new, count=1)
        if n != 1:
            raise ValueError("set_trading_options: <MarketSides type=> not found once")
    return new


def set_databank_cap(task_bytes, cap):
    """Raise the build's databank size cap (<Rankings><MaxStrategies>). Whatever the cap is,
    the databank trims to the best-N by fitness once full = SURVIVORSHIP. For an honest gate
    matrix set this >= the generation budget so every tested strategy that passes acceptance
    is retained. Asserts exactly one <MaxStrategies> (it lives only in <Rankings>).

    Donor caps vary — do NOT assume 1000. Across the 232 build tasks on the reference
    machine: 1000 x134, 10000 x88, 20000 x9, 100 x1 (the 144.2953 Builder ships 10000).
    Read the donor's value rather than relying on a documented default."""
    new, n = re.subn(rb'<MaxStrategies>\d+</MaxStrategies>',
                     ("<MaxStrategies>%d</MaxStrategies>" % int(cap)).encode(), task_bytes)
    if n != 1:
        raise ValueError(f"set_databank_cap: expected exactly 1 <MaxStrategies>, found {n}")
    return new


# SQX's sample selector, as stored in a condition's <Column-Value sampleType="…">.
# Codes read off the app's own SQConstants.sampleTypeList (144.2953).
SAMPLE_TYPES = {"full": 127, "is": 10, "oos": 20}


def set_acceptance(task_bytes, keep_classes=("AvgTradesPerMonth",), sample_type=None,
                   notes=None):
    """Reduce the build's databank ACCEPTANCE to only the given column classes. Every
    keep-class condition in <Rankings><Conditions> is ENABLED (use="true" — even when
    the donor ships it disabled: both real donors on the reference install carry ALL
    conditions use="false", which the previous implementation could only raise on), and
    every OTHER condition is switched off. Matching is attribute-order-insensitive, so
    a donor writing `<Condition use="true" id=…>` can no longer slip a performance
    filter past the sweep — the survivorship bias this function exists to remove.

    Default keeps just AvgTradesPerMonth — a *measurability* floor (enough trades to
    form a returns series), dropping *performance* filters (ProfitFactor / NetProfit /
    …) so the databank retains winners AND losers, the honest population the gate
    needs. Operates ONLY inside <Rankings> (the generation acceptance — a build task
    has exactly one such block); the CrossCheck acceptance blocks (WF / MonteCarlo /
    Retest) live outside it and are never touched. Raises only if a keep class does
    not exist among the donor's <Rankings> conditions at all.

    `sample_type` ("is" | "oos" | "full", or a raw SQX code) sets WHICH SAMPLE the
    surviving conditions are measured over. This matters more than it looks: the donor
    default is 127 = Full Sample, so a floor written to select a measurable population
    is evaluated over IS **and OOS together** — membership in the study then depends on
    out-of-sample behaviour, and offspring that went dormant after the split date are
    removed retroactively. The fingerprint is n_no_activity == 0 in both windows. Pass
    "is" to keep the holdout out of the population definition. None leaves the donor's
    sample untouched."""
    m = _find_rankings(task_bytes)
    block = m.group(0)
    keep = tuple((k.encode("utf-8") if isinstance(k, str) else k) for k in keep_classes)

    code = None
    if sample_type is not None:
        code = (SAMPLE_TYPES.get(str(sample_type).lower())
                if not isinstance(sample_type, int) else sample_type)
        if code is None:
            raise ValueError(f"set_acceptance: unknown sample_type {sample_type!r} "
                             f"(known: {sorted(SAMPLE_TYPES)} or a raw SQX code)")

    present, avail = set(), []
    enabled, disabled = [], []
    out, pos = [], 0
    for cm, cls in _rankings_conditions(block):
        avail.append(cls.decode("utf-8", "replace"))
        out.append(block[pos:cm.start()])
        seg = cm.group(0)
        if cls in keep:
            present.add(cls)
            seg, changed = _set_condition_use(seg, b"true")
            if changed:
                enabled.append(cls.decode("utf-8", "replace"))
            if code is not None:               # measure the floor on the chosen sample
                seg = re.sub(rb'\bsampleType="[^"]*"',
                             b'sampleType="%d"' % code, seg)
                if not re.search(rb'\bsampleType="%d"' % code, seg):
                    raise ValueError(
                        f"set_acceptance: sampleType={code} did not land on kept "
                        f"condition {cls.decode('utf-8', 'replace')!r} — the "
                        f"Column-Value attribute was not found")
        else:
            seg, changed = _set_condition_use(seg, b"false")
            if changed:
                disabled.append(cls.decode("utf-8", "replace") or "<unnamed>")
        out.append(seg)
        pos = cm.end()
    out.append(block[pos:])

    missing = sorted(k.decode("utf-8", "replace") for k in keep if k not in present)
    if missing:
        raise ValueError(
            f"set_acceptance: keep class(es) {missing} do not exist in the donor's "
            f"<Rankings> conditions — available: {sorted(set(avail))}. Pick from those, "
            f"or add the condition to the base project in SQX first.")
    if enabled:
        _note(notes, "acceptance: enabled " + ", ".join(enabled)
                     + " (donor had it disabled)")
    if disabled:
        _note(notes, "acceptance: disabled " + ", ".join(disabled))
    if code is not None:
        _note(notes, f"acceptance: kept condition(s) measured on sample "
                     f"{sample_type!r} (sampleType={code})")
    return task_bytes[:m.start()] + b"".join(out) + task_bytes[m.end():]


def apply_overrides(task_bytes, overrides, notes=None):
    """Apply an override spec to one task's bytes, in a safe order (instrument first so
    later swaps see the final symbol). `overrides` (all keys optional):
        {instrument: {symbol, instrument_id, timeframe},
         dates: {from, to},            # the FULL Setup span (= IS+OOS when oos is given)
         oos: [{from, to}, …],         # holdout slice(s) carved out of that span
         trading: {spread, slippage, session, market_side, time_range, friday_exit},
         generation: {acceptance: [<column class>, …], databank_cap: <int>}}
    Returns the rewritten bytes (unchanged if overrides is falsy). Notes/warnings are
    appended to `notes` by the setters that accept it — set_instrument and set_acceptance.
    The trading-option setters take no `notes` and therefore report nothing; they fail
    loudly on any unmatched swap instead, so silence there means every knob matched."""
    if not overrides:
        return task_bytes
    new = task_bytes
    ins = overrides.get("instrument")
    if ins:
        new = set_instrument(new, ins["symbol"], ins["instrument_id"],
                             old_symbol=ins.get("old_symbol"),
                             old_instrument=ins.get("old_instrument"),
                             timeframe=ins.get("timeframe"),
                             usymbol=ins.get("usymbol", ""),
                             usymbol_name=ins.get("usymbol_name", ""),
                             source=ins.get("source"), broker=ins.get("broker"),
                             notes=notes)
    elif overrides.get("timeframe"):          # retime without switching instrument
        new = set_timeframe(new, overrides["timeframe"])
    dates = overrides.get("dates")
    if dates:
        new = set_dates(new, dates["from"], dates["to"])
    oos = overrides.get("oos")          # AFTER set_dates: ranges are validated against the span
    if oos:
        new = set_oos_ranges(new, oos if isinstance(oos, (list, tuple)) else [oos])
    cc = overrides.get("cross_checks")
    if cc and cc.get("additional_markets"):
        d = overrides.get("dates") or {}
        new = set_crosschecks(new, additional_markets=cc["additional_markets"],
                              annotation_only=cc.get("annotation_only", True),
                              date_from=cc.get("from") or d.get("from"),
                              date_to=cc.get("to") or d.get("to"))
    tr = overrides.get("trading")
    if tr:
        new = set_trading_options(new, spread=tr.get("spread"), slippage=tr.get("slippage"),
                                  session=tr.get("session"), market_side=tr.get("market_side"),
                                  time_range=tr.get("time_range"), friday_exit=tr.get("friday_exit"),
                                  swap=tr.get("swap"))
    gen = overrides.get("generation")
    if gen:
        if gen.get("databank_cap") is not None:
            new = set_databank_cap(new, gen["databank_cap"])
        acc = gen.get("acceptance")
        if acc:
            keep = acc if isinstance(acc, (list, tuple)) else [acc]
            new = set_acceptance(new, keep_classes=tuple(keep),
                                 sample_type=gen.get("acceptance_sample"), notes=notes)
        # written on EVERY build, inherited never — see set_generation_type
        if gen.get("method"):
            new = set_generation_type(new, gen["method"])
    return new


# --------------------------------------------------------------------------------------
# CustomAnalysis task (the ExportReturnsMatrix export step) — plugin schema, 2026-07-14
# --------------------------------------------------------------------------------------
# Task type token 'CustomAnalysis' (internal/plugins/TaskCustomAnalysis/module.js). Unlike a
# Build task (a 3 MB donor clone) the CustomAnalysis task XML is TINY and built from scratch:
# a <CustomAnalysis> block that names the method in one of four slots — PerStrategy1/2 (per-
# strategy methods) or FullDatabank1/2 (whole-databank methods) — plus that slot's InputArgs,
# and an Input/Output <Databank> pair. ExportReturnsMatrix registers as TYPE_PROCESS_DATABANK
# (super("ExportReturnsMatrix", …)) so it belongs in a FullDatabank slot. The element names
# match plugins/SettingsCustomAnalysis/SettingsCustomAnalysisService.js verbatim (PerStrategy1,
# FullDatabank1, InputArgsFullDatabank1, RemoveFailedStrategies, Databank Input/Output).

ANALYSIS_SLOTS = ("FullDatabank1", "FullDatabank2", "PerStrategy1", "PerStrategy2")


def build_analysis_task(method, input_args, input_db, output_db=None,
                        slot="FullDatabank1", remove_failed=False):
    """Return the bytes of a CustomAnalysis task XML: run `method` (a registered
    CustomAnalysisMethod name, e.g. 'ExportReturnsMatrix') over `input_db`, passing the
    snippet's `input_args` string (ExportReturnsMatrix: 'outputDir[;period[;sample]]').
    Non-destructive by default (output defaults to input, RemoveFailedStrategies=false).
    `slot` = FullDatabank1/2 for TYPE_PROCESS_DATABANK methods, PerStrategy1/2 for
    per-strategy methods."""
    if slot not in ANALYSIS_SLOTS:
        raise ValueError(f"build_analysis_task: bad slot {slot!r} (one of {ANALYSIS_SLOTS})")
    output_db = output_db or input_db
    methods = {"PerStrategy1": "none", "PerStrategy2": "none",
               "FullDatabank1": "none", "FullDatabank2": "none"}
    iargs = {"PerStrategy1": "", "PerStrategy2": "", "FullDatabank1": "", "FullDatabank2": ""}
    methods[slot] = method
    iargs[slot] = input_args
    # ROOT is <Settings> — the same envelope Build-Task/Retest-Task use inside a project.cfx.
    # (The plugin's task.xml template wraps this in <Task>, but the app strips that wrapper
    # when persisting; a stored task whose root is <Task> fails to load: "Element
    # 'CustomAnalysis' not found, in setting: CustomAnalysis".)
    return (
        "<Settings>\n"
        "  <CustomAnalysis>\n"
        f"    <PerStrategy1>{escape(methods['PerStrategy1'])}</PerStrategy1>\n"
        f"    <PerStrategy2>{escape(methods['PerStrategy2'])}</PerStrategy2>\n"
        f"    <FullDatabank1>{escape(methods['FullDatabank1'])}</FullDatabank1>\n"
        f"    <FullDatabank2>{escape(methods['FullDatabank2'])}</FullDatabank2>\n"
        f"    <InputArgsPerStrategy1>{escape(iargs['PerStrategy1'])}</InputArgsPerStrategy1>\n"
        f"    <InputArgsPerStrategy2>{escape(iargs['PerStrategy2'])}</InputArgsPerStrategy2>\n"
        f"    <InputArgsFullDatabank1>{escape(iargs['FullDatabank1'])}</InputArgsFullDatabank1>\n"
        f"    <InputArgsFullDatabank2>{escape(iargs['FullDatabank2'])}</InputArgsFullDatabank2>\n"
        f"    <RemoveFailedStrategies>{'true' if remove_failed else 'false'}</RemoveFailedStrategies>\n"
        "  </CustomAnalysis>\n"
        "  <Databanks>\n"
        f'    <Databank label="Input databank" name="Input" value={quoteattr(input_db)}/>\n'
        f'    <Databank label="Output databank" name="Output" value={quoteattr(output_db)} />\n'
        "  </Databanks>\n"
        "</Settings>\n"
    ).encode("utf-8")


# --------------------------------------------------------------------------------------
# config.xml regeneration (preserve project tag + system DBs + inactive tasks
# + every other top-level section — e.g. <Resources> — verbatim, in original order)
# --------------------------------------------------------------------------------------
def _el_line(indent, tag, attrib):
    return f"{indent}<{tag} " + " ".join(f"{k}={quoteattr(v)}" for k, v in attrib.items()) + " />"


# any XML tag (quote-aware, so a quoted '>' inside an attribute can't split it) or comment
_XML_TOKEN = re.compile(r'<!--.*?-->|<(?:"[^"]*"|\'[^\']*\'|[^>"\'])*>', re.S)


def _top_level_raw(config_text):
    """Split raw config.xml text into (root_open_tag, children) where `children` is an
    ordered list of (tag_name, raw_source_segment) for every top-level child of the
    root — tag_name None for a bare comment between children. Segments are verbatim
    source slices (inner formatting intact), which is what lets build_config pass
    sections it does not regenerate (e.g. <Resources>) through byte-identically."""
    children = []
    root_open = None
    depth = 0
    child_start = child_tag = None
    for m in _XML_TOKEN.finditer(config_text):
        tok = m.group(0)
        if tok.startswith("<!--"):
            if depth == 1 and child_start is None:
                children.append((None, tok))
            continue
        if tok.startswith("<?") or tok.startswith("<!"):
            continue                                   # declaration / doctype
        name_m = re.match(r"</?\s*([\w.-]+)", tok)
        name = name_m.group(1) if name_m else ""
        if tok.startswith("</"):
            depth -= 1
            if depth == 1 and child_start is not None:
                children.append((child_tag, config_text[child_start:m.end()]))
                child_start = child_tag = None
            elif depth == 0:
                break                                  # root element closed
        elif tok.endswith("/>"):
            if depth == 1:
                children.append((name, tok))
        else:
            if depth == 0:
                root_open = tok
            elif depth == 1:
                child_start, child_tag = m.start(), name
            depth += 1
    if root_open is None:
        raise ValueError("malformed config.xml: no root element found")
    return root_open, children


def build_config(base_config_bytes, project_name, tasks, analysis_tasks=None):
    """Regenerate config.xml.

    `tasks` is a list of build-task dicts (config order):
        {name, taskXMLFile, output_db, settings_preset, position}
    `analysis_tasks` (optional) is a list of CustomAnalysis-task dicts, appended AFTER the
    build tasks so they run over the freshly generated databanks:
        {name, taskXMLFile, input_db, output_db}
    Preserves: the <Project> tag (name swapped), the inactive (non-Build) helper tasks,
    every databank that is NOT an old build-task output (system + any user databanks),
    and EVERY other top-level section of the base config (e.g. <Resources> — the
    Symbols/Sessions/CustomIndicators/CustomBlocks registry behind "unresolved
    resources", carried by real GUI-built projects) VERBATIM and in original order.

    Raises ValueError if a task's output_db collides with a databank the base project
    already carries (system or user) — a duplicate <Databank> registration would
    corrupt the project while looking successful.
    """
    analysis_tasks = analysis_tasks or []
    config_text = base_config_bytes.decode("utf-8")
    cfg = ET.fromstring(config_text)
    proj = dict(cfg.attrib)
    proj["name"] = project_name

    # which databanks were old build-task outputs -> drop; keep everything else verbatim.
    # inactive = base helper tasks (GoToTask/StopAndStart); we re-emit our own analysis tasks,
    # so exclude any CustomAnalysis from the preserved-inactive set too.
    old_outputs = {t.get("title") for t in _section(cfg, "Tasks").findall("Task")
                   if t.get("type") == "Build"}
    inactive = [t for t in _section(cfg, "Tasks").findall("Task")
                if t.get("type") not in ("Build", "CustomAnalysis")]
    preserved_db = [d for d in _section(cfg, "Databanks").findall("Databank")
                    if d.get("name") not in old_outputs]

    # a new output databank must not collide with a databank we preserve (system DBs
    # like "Results", or any user databank) — that would register the same name twice
    preserved_names = {d.get("name") for d in preserved_db}
    clashes = sorted({t["output_db"] for t in tasks} & preserved_names)
    if clashes:
        raise ValueError(
            f"build_config: output databank name(s) {clashes} collide with databank(s) "
            f"the base project already carries (the 5 system databanks "
            f"{sorted(SYSTEM_DB)} are always present). Choose different output_db names.")

    task_lines = [
        _el_line("    ", "Task", {
            "type": "Build", "name": t["name"], "showSettingsOverview": "false",
            "sampleName": "Custom", "active": "true", "taskXMLFile": t["taskXMLFile"],
            "templateFile": t["settings_preset"], "title": t["output_db"],
        }) for t in tasks
    ]
    task_lines += [
        _el_line("    ", "Task", {
            "type": "CustomAnalysis", "name": a["name"], "showSettingsOverview": "false",
            "sampleName": "Custom", "active": "true", "taskXMLFile": a["taskXMLFile"],
        }) for a in analysis_tasks
    ]
    task_lines += [_el_line("    ", "Task", t.attrib) for t in inactive]

    db_lines = [_el_line("    ", "Databank", d.attrib) for d in preserved_db]
    db_lines += [
        _el_line("    ", "Databank", {
            "name": t["output_db"], "view": "Default - Main data",
            "syncType": "Auto-sync every 10 minutes", "position": str(t["position"]),
        }) for t in tasks
    ]
    # register any analysis Output databank that isn't already a build output / preserved DB
    registered = {d.get("name") for d in preserved_db} | {t["output_db"] for t in tasks}
    for k, a in enumerate(analysis_tasks):
        odb = a.get("output_db")
        if odb and odb not in registered:
            db_lines.append(_el_line("    ", "Databank", {
                "name": odb, "view": "Default - Main data",
                "syncType": "Auto-sync every 10 minutes",
                "position": str(9000 + k),
            }))
            registered.add(odb)

    # re-emit the root: Tasks + Databanks regenerated, every OTHER top-level child of
    # the base (e.g. <Resources>) passed through verbatim, in the base's own order
    proj_open = f"<{cfg.tag} " + " ".join(f"{k}={quoteattr(v)}" for k, v in proj.items()) + ">"
    _base_open, base_children = _top_level_raw(config_text)
    body = []
    emitted = {"Tasks": False, "Databanks": False}
    for tag, seg in base_children:
        if tag in emitted:
            if emitted[tag]:
                raise ValueError(f"malformed config.xml: more than one <{tag}> section")
            emitted[tag] = True
            lines = task_lines if tag == "Tasks" else db_lines
            body.append(f"  <{tag}>\n" + "\n".join(lines) + f"\n  </{tag}>")
        else:
            body.append("  " + seg)
    if not all(emitted.values()):
        # unreachable in practice: _section() above already raised for a missing block
        raise ValueError("malformed config.xml: missing <Tasks> or <Databanks> section")
    return (proj_open + "\n" + "\n".join(body) + f"\n</{cfg.tag}>").encode("utf-8")


# --------------------------------------------------------------------------------------
# the public entry point
# --------------------------------------------------------------------------------------
def make_project(base_cfx, project_name, tasks, out_cfx,
                 base_task_index=0, db_base_pos=1000, db_pos_step=100,
                 make_databank_dirs=True, overrides=None, analysis_tasks=None):
    """Clone `base_cfx` into a new project.cfx at `out_cfx`.

    `tasks` is a list of per-task dicts:
        {template: <abs .sqx path>, output_db: <databank name>,
         name: <task name, default = template stem>,
         avg_trades: <int|None>,
         time_minutes: <int|None>,        # stop at a wall-clock cap  (type=time-limit)
         passed_strategies: <int|None>}   # stop at N in the databank (type=databank-full)
                                          #   the two stop conditions are exclusive
    The donor build task is base_cfx's build task #`base_task_index` (its embedded
    settings — data/symbol/TF/exits — are inherited by every clone).

    Writes `out_cfx`, creates empty databank folders next to it (databanks/<name>/),
    and self-verifies. Returns the verification report dict; its "notes" key carries
    deduplicated human-readable notes/WARNINGs from the cloning + override steps (e.g.
    "enabled AvgTradesPerMonth acceptance", untouched foreign charts) — surface them to
    the user. Does NOT touch the install beyond out_cfx + its databank folders;
    deploy() handles install placement.
    """
    members = read_base(base_cfx)
    build = base_build_tasks(members)
    if not build:
        raise ValueError(f"{base_cfx}: no active Build tasks to clone from")
    donor_name = build[base_task_index][1]
    donor_bytes = members[donor_name]
    settings_preset = build[base_task_index][0].get("templateFile", "")

    # resolve per-task defaults + build the task spec list
    spec = []
    for i, t in enumerate(tasks):
        stem = os.path.splitext(os.path.basename(t["template"]))[0]
        spec.append({
            "name": t.get("name") or stem,
            "taskXMLFile": f"Build-Task{i + 1}.xml",
            "output_db": t["output_db"],
            "settings_preset": settings_preset,
            "position": db_base_pos + i * db_pos_step,
            "template": t["template"],
            "avg_trades": t.get("avg_trades"),
            "time_minutes": t.get("time_minutes"),
            "passed_strategies": t.get("passed_strategies"),
        })

    # clone the N build task XMLs (+ apply project-level overrides: instrument/dates/trading)
    notes = []
    task_members = {}
    for i, t in enumerate(spec, 1):
        clone = clone_task(
            donor_bytes, t["template"], t["output_db"],
            avg_trades=t["avg_trades"], time_minutes=t["time_minutes"],
            passed_strategies=t["passed_strategies"], notes=notes)
        clone = apply_overrides(clone, overrides, notes=notes)
        # MTF chart provisioning runs LAST: set_instrument/set_timeframe rewrite every
        # data <Chart timeframe=>, which would flatten an earlier-inserted D1 chart to H1
        task_members[f"Build-Task{i}.xml"] = ensure_mtf_charts(clone, t["template"],
                                                               notes=notes)

    # resolve the CustomAnalysis task spec + build each tiny task XML from scratch (no donor)
    a_spec = []
    for j, a in enumerate(analysis_tasks or [], 1):
        a_spec.append({
            "name": a.get("name") or f"Analysis{j}",
            "taskXMLFile": f"CustomAnalysis-Task{j}.xml",
            "input_db": a["input_db"],
            "output_db": a.get("output_db") or a["input_db"],
            "method": a.get("method", "ExportReturnsMatrix"),
            "input_args": a["input_args"],
            "slot": a.get("slot", "FullDatabank1"),
            "remove_failed": a.get("remove_failed", False),
        })
    analysis_members = {
        a["taskXMLFile"]: build_analysis_task(
            a["method"], a["input_args"], a["input_db"],
            output_db=a["output_db"], slot=a["slot"], remove_failed=a["remove_failed"])
        for a in a_spec
    }

    new_cfg = build_config(members["config.xml"], project_name, spec, analysis_tasks=a_spec)

    # verbatim inactive helper members (not config, Build-Task*, or CustomAnalysis-Task*)
    inactive_members = {n: b for n, b in members.items()
                        if n != "config.xml" and not n.startswith("Build-Task")
                        and not n.startswith("CustomAnalysis-Task")}

    os.makedirs(os.path.dirname(out_cfx) or ".", exist_ok=True)
    with zipfile.ZipFile(out_cfx, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("config.xml", new_cfg)
        for i in range(1, len(spec) + 1):
            z.writestr(f"Build-Task{i}.xml", task_members[f"Build-Task{i}.xml"])
        for a in a_spec:
            z.writestr(a["taskXMLFile"], analysis_members[a["taskXMLFile"]])
        for n, b in inactive_members.items():
            z.writestr(n, b)

    if make_databank_dirs:
        db_dir = os.path.join(os.path.dirname(out_cfx), "databanks")
        cfg_new = ET.fromstring(new_cfg.decode("utf-8"))
        for d in _section(cfg_new, "Databanks").findall("Databank"):
            os.makedirs(os.path.join(db_dir, d.get("name") or ""), exist_ok=True)

    report = verify(out_cfx, spec, require_templates_exist=True, analysis_spec=a_spec)
    # identical per-task notes collapse to one entry (N clones of one donor produce the
    # same correction note N times); order of first occurrence is kept
    seen = set()
    report["notes"] = [n for n in notes if not (n in seen or seen.add(n))]
    return report


# --------------------------------------------------------------------------------------
# verification (the oracle short of an actual build)
# --------------------------------------------------------------------------------------
def verify(cfx_path, spec, require_templates_exist=True, analysis_spec=None):
    """Re-open the written project and assert the proven invariants. Raises on any
    failure; returns a report dict on success."""
    analysis_spec = analysis_spec or []
    with zipfile.ZipFile(cfx_path) as z:
        names = z.namelist()
        cfg = ET.fromstring(z.read("config.xml").decode("utf-8"))
        build_tasks = [t for t in _section(cfg, "Tasks").findall("Task") if t.get("type") == "Build"]
        ca_tasks = [t for t in _section(cfg, "Tasks").findall("Task") if t.get("type") == "CustomAnalysis"]
        out_dbs = [t["output_db"] for t in spec]

        # 1) one Build-Task member per spec entry + the inactive helpers + config
        for i in range(1, len(spec) + 1):
            assert f"Build-Task{i}.xml" in names, f"missing Build-Task{i}.xml"
        assert len(build_tasks) == len(spec), \
            f"config has {len(build_tasks)} build tasks, expected {len(spec)}"

        # 2) output databanks are unique and all registered
        assert len(set(out_dbs)) == len(out_dbs), "duplicate output databank names"
        reg = {d.get("name") for d in _section(cfg, "Databanks").findall("Databank")}
        missing_db = [d for d in out_dbs if d not in reg]
        assert not missing_db, f"output databanks not registered: {missing_db}"

        # 3) system databanks survived
        missing_sys = [s for s in SYSTEM_DB if s not in reg]
        assert not missing_sys, f"system databanks dropped: {missing_sys}"

        # 4) per-task: the task is in TEMPLATE MODE and templateFile resolves to THIS
        #    task's template; internal Output == title.
        #    The mode check is not optional: a task can carry a perfectly correct,
        #    on-disk templateFile and still ignore it completely under type="simple".
        #    Checking only the path is what let simple-mode projects verify green.
        broken, mism, wrong_mode = [], [], []
        for i, t in enumerate(spec, 1):
            raw = z.read(f"Build-Task{i}.xml").decode("utf-8", "replace")
            el = re.search(r'<StrategyType\b[^>]*>', raw)
            el = el.group(0) if el else ""
            mode = re.search(r'\btype="([^"]*)"', el)
            if not mode or mode.group(1) != "template":
                wrong_mode.append((i, t["name"], mode and mode.group(1)))
            m = re.search(r'\btemplateFile="([^"]*)"', el)
            tpl = m.group(1) if m else None
            if not tpl or os.path.normpath(tpl) != os.path.normpath(t["template"]):
                mism.append((i, t["name"], tpl))
            elif require_templates_exist and not os.path.exists(tpl):
                broken.append((i, t["name"], tpl))
            od = re.search(r'<Databank label="Output databank" name="Output" value="([^"]*)"', raw)
            assert od and od.group(1) == t["output_db"], \
                (i, t["name"], "internal Output != title", od and od.group(1))
        assert not wrong_mode, \
            ('<StrategyType type=> is not "template" — the attached template would be '
             f"IGNORED and the task would build generic strategies: {wrong_mode}")
        assert not mism, f"templateFile mismatch: {mism}"
        assert not broken, f"templateFile does not resolve on disk: {broken}"

        # 5) CustomAnalysis tasks: one member each, registered in config, method+input DB wired
        assert len(ca_tasks) == len(analysis_spec), \
            f"config has {len(ca_tasks)} CustomAnalysis tasks, expected {len(analysis_spec)}"
        for a in analysis_spec:
            assert a["taskXMLFile"] in names, f"missing {a['taskXMLFile']}"
            raw = z.read(a["taskXMLFile"]).decode("utf-8", "replace")
            slot = a.get("slot", "FullDatabank1")
            assert re.search(rf'<{slot}>{re.escape(a["method"])}</{slot}>', raw), \
                f"{a['taskXMLFile']}: method {a['method']} not in slot {slot}"
            assert re.search(rf'<InputArgs{slot}>{re.escape(escape(a["input_args"]))}</InputArgs{slot}>', raw), \
                f"{a['taskXMLFile']}: input_args not wired into InputArgs{slot}"
            assert f'name="Input" value="{a["input_db"]}"' in raw, \
                f"{a['taskXMLFile']}: input databank != {a['input_db']}"
            assert a["input_db"] in reg, f"analysis input databank not registered: {a['input_db']}"

    return {
        "project": cfg.get("name"),
        "build_tasks": len(build_tasks),
        "analysis_tasks": len(ca_tasks),
        "output_databanks": len(out_dbs),
        "system_databanks_ok": True,
        "template_mode_ok": True,
        "templates_resolve": require_templates_exist,
        "members": len(names),
    }


# --------------------------------------------------------------------------------------
# deploy into an install (SQX must be CLOSED)
# --------------------------------------------------------------------------------------
def deploy(out_cfx, install, project_name, backup=True):
    """Place a generated project.cfx into <install>/user/projects/<project_name>/ and
    create its databank folders. Returns the destination path. SQX MUST be closed."""
    if not os.path.isdir(install):
        raise ValueError(f"install not found: {install}")
    dest_dir = os.path.join(install, "user", "projects", project_name)
    os.makedirs(os.path.join(dest_dir, "databanks"), exist_ok=True)
    dest = os.path.join(dest_dir, "project.cfx")

    if backup and os.path.exists(dest):
        os.replace(dest, dest + f".bak-{int(os.path.getmtime(dest))}")

    with open(out_cfx, "rb") as r, open(dest, "wb") as w:
        w.write(r.read())

    with zipfile.ZipFile(dest) as z:
        cfg = ET.fromstring(z.read("config.xml").decode("utf-8"))
    for d in _section(cfg, "Databanks").findall("Databank"):
        os.makedirs(os.path.join(dest_dir, "databanks", d.get("name") or ""), exist_ok=True)
    return dest
