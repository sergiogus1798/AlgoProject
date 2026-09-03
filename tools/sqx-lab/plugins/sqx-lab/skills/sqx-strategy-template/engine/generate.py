"""Generate a strategy template (.sqx) from a design, bound to install groups.

A design is just group names from the install. The generator looks them up, points
the RandomCondition/RandomValue blocks at them, embeds them, renames, and validates.
It never invents blocks/groups; the chosen groups must exist (and be the right type)
in the install.

Shapes (each maps to a proven, build-confirmed skeleton):
  stop          2 Condition groups AND'd + 1 Value group for the stop price (EnterAtStop)
  market        2 Condition groups AND'd, immediate fill          (EnterAtMarket)
  market_single 1 Condition group, immediate fill                 (EnterAtMarket)

All shapes share the signal-variable structure: entry signals -> entry/exit rules,
short = mirror (NegatedCondition / OppositeValue). The skeleton already carries the
full exit stack; the template only binds the entry groups.

Usage:  python generate.py [INSTALL_PATH]
"""
import sys, os, copy, io, re, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))


sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from sqx_common import load_shared_install as _load_shared_install  # noqa: E402


def _shared_install():
    """The stored SQX install path (sqx_common.state_dir()), written by whichever
    sqx-lab skill bootstraps first. Empty string if not yet set."""
    return _load_shared_install() or ""


DEFAULT_INSTALL = _shared_install() or r"C:\StrategyQuantX"
SKEL = os.path.join(HERE, "skeletons")

# shape -> (skeleton file, n condition groups, needs a value group)
SHAPES = {
    "stop":           ("stop_skeleton.sqx",            2, True),
    # market: clean AND(filter, trigger) in the SIGNAL var -> EnterAtMarket. REBUILT 2026-06-09 by
    # build_market_skeletons.py from the CONFIRMED `stop` architecture (was previously cloned from the
    # example "3TrendUPBBNotAdvanced", which buried the trigger in the entry rule + a BarsSinceOrderClosed
    # re-entry guard => built but never traded; that lineage is gone). PENDING BUILD-CONFIRM.
    "market":         ("market_skeleton.sqx",          2, False),
    "market_single":  ("market_single_skeleton.sqx",   1, False),
    # session_market: clean market + a non-directional time gate as a third positive AND term in BOTH
    # signal vars (AND(AND(filter, trigger), BarDayOfWeekIsNot)). REBUILT 2026-06-09 by
    # build_market_skeletons.py on the clean market (the old proto_session_gate version inherited the
    # buggy market lineage => no trades). PENDING BUILD-CONFIRM.
    "session_market": ("session_market_skeleton.sqx",  2, False),
    # stop_long_single: LONG-ONLY, one condition group (trigger) -> EnterAtStop, stop price
    # from a Value group. PENDING BUILD-CONFIRM — derived by proto_long_stop.py from stop_skeleton.
    "stop_long_single": ("stop_long_single_skeleton.sqx", 1, True),
    # two_entry_market: LONG-ONLY, TWO INDEPENDENT entry legs — two condition groups on two
    # signal vars, each -> EnterAtMarket with its own MagicNumber + ExitAfterBars (A=10, B=30).
    # PENDING BUILD-CONFIRM — composed by proto_two_entries.py (most novel shape).
    "two_entry_market": ("two_entry_market_skeleton.sqx", 2, False),
    # role_market: ROLE-STRUCTURED entry == regime AND trigger AND NOT veto (3 Condition holes),
    # market execution, short = mirror (!regime AND !trigger AND veto). The first shape with real
    # boolean depth + a negated (veto) slot. PENDING BUILD-CONFIRM — composed by
    # build_role_market_skeleton.py from the CONFIRMED stop architecture (positive AND in the
    # signal var, no bars-guard) + EnterAtMarket + the Not(condition) veto idiom from market.
    # Holes bound in order: RandomCondition1=regime, RandomCondition2=trigger, RandomCondition3=veto.
    "role_market": ("role_market_skeleton.sqx", 3, False),
    # mtf_filter: MULTI-TIMEFRAME entry == a HIGHER-TIMEFRAME (daily) regime FILTER AND a
    # main-TF TRIGGER, entered on a stop at a price level. Same SIGNATURE as `stop` (2 condition
    # holes + 1 value group), but the skeleton carries a 2-stream <Datas> (main + daily Subchart #1
    # @ tf=1440) and binds RandomCondition1 (the FILTER) to #Chart#=1 so it evaluates on the daily
    # chart; RandomCondition2 (trigger) + the RandomValue stop price stay on #Chart#=0. The short
    # NegatedCondition mirror inherits the daily binding by identification. The FIRST shape on
    # design axis A (multi-data / multi-timeframe). PENDING BUILD-CONFIRM — derived by
    # build_mtf_filter_skeleton.py from the CONFIRMED stop skeleton + the MTF mechanic proven in
    # the install's own StrategyTemplates/highest_breakout_template_daily_filter.sqx. Bind order:
    # RandomCondition1 = daily_filter (HTF), RandomCondition2 = trigger (main TF).
    "mtf_filter": ("mtf_filter_skeleton.sqx", 2, True),
    # --- LONG-ONLY twins (short mirror stripped by proto_long_fleet.py from the two-sided
    # skeletons above; same filter+trigger(+value) signatures, only the Long signal/entry/exit
    # survive). BUILD-CONFIRMED 2026-06-10 — the 24-template breakout_fleet_long built cleanly in
    # AlgoWizard as INDICES_ID_60_MKT_LONG (deployed to your install). ---
    "stop_long":       ("stop_long_skeleton.sqx",       2, True),
    "market_long":     ("market_long_skeleton.sqx",     2, False),
    "mtf_filter_long": ("mtf_filter_long_skeleton.sqx", 2, True),
    # --- SHORT-ONLY twins (proto_short_fleet.py). NOT the mirror of the long twins:
    # the mirror ("generate=opposite") signal is EMPTIED and the long machinery is renamed
    # + flipped to #Direction#=-1, so the template fires on the PRIMARY signal — i.e. on the
    # groups the design chose, directly. Architecture derived from the hand-corrected
    # gold-templates-short6-FIXED set (4x stop_short + 2x mtf_filter_short) and verified
    # structurally against it by evals/run_evals.py.
    # DESIGN CONTRACT: a short design must name genuinely BEARISH pools — nothing mirrors
    # them for you. See research_agent.md.
    # PENDING BUILD-CONFIRM of an engine-generated template (the reference set is hand-made).
    "stop_short":       ("stop_short_skeleton.sqx",       2, True),
    "mtf_filter_short": ("mtf_filter_short_skeleton.sqx", 2, True),
    # market_short inherits `market`'s own still-unconfirmed lineage AND has no FIXED
    # reference of its own (all six references are stop/mtf shapes) — weakest of the three.
    "market_short":     ("market_short_skeleton.sqx",     2, False),
}


def _install_groups(install):
    bg = ET.parse(os.path.join(install, "user", "settings", "blockGroups.xml")).getroot()
    return {g.get("name"): g for g in bg.iter("Group")}


def _safe_filename(name):
    """spec['name'] is LLM-authored free text: collapse anything path-hostile
    (separators, '..' traversal, drive colons, spaces) to '_' before it becomes
    the output filename. The strategy name INSIDE the XML stays as authored."""
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)


def _missing_group_error(gn, groups, prefix=""):
    """Actionable 'group not in install' message: show what the LIVE install actually
    has, and point at the usual cause — a stale catalog.json."""
    cond = sorted(n for n, g in groups.items() if g.get("type") == "Condition")
    val = sorted(n for n, g in groups.items() if g.get("type") == "Value")
    return (f"{prefix}group not in install: {gn}\n"
            f"  Condition groups in the live install: {', '.join(cond) if cond else '(none)'}\n"
            f"  Value groups in the live install: {', '.join(val) if val else '(none)'}\n"
            "  If you took this name from catalog.json, the catalog may be stale — "
            "re-run: python engine/discover.py")


def _avail(install):
    raw = open(os.path.join(install, "user", "settings", "customBlocks.xml"),
               encoding="utf-8", errors="replace").read()
    return set(re.findall(r'key="(CBlock_[A-Za-z0-9_]+)"', raw))


def _build(name, shape, cond_groups, value_group, install, outdir):
    """Core builder: bind `cond_groups` (ordered) + optional `value_group` into `shape`."""
    if shape not in SHAPES:
        raise SystemExit(f"unknown shape {shape!r} (have: {sorted(SHAPES)})")
    skel_file, n_cond, needs_value = SHAPES[shape]
    if len(cond_groups) != n_cond:
        raise SystemExit(f"{shape} needs {n_cond} condition group(s), got {len(cond_groups)}")
    if needs_value and not value_group:
        raise SystemExit(f"{shape} needs a value group for the price pool")
    if not needs_value and value_group:
        raise SystemExit(f"{shape} takes no value group (got {value_group!r})")
    if len(set(cond_groups)) != len(cond_groups):
        raise SystemExit(f"condition groups must be distinct (got {cond_groups})")

    groups = _install_groups(install)
    checks = [(gn, "Condition") for gn in cond_groups]
    if value_group:
        checks.append((value_group, "Value"))
    for gn, kind in checks:
        if gn not in groups:
            raise SystemExit(_missing_group_error(gn, groups))
        if groups[gn].get("type") != kind:
            raise SystemExit(f"{gn} is {groups[gn].get('type')}, expected {kind}")

    zin = zipfile.ZipFile(os.path.join(SKEL, skel_file))
    members = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])

    chosen = list(cond_groups) + ([value_group] if value_group else [])
    ids = {gn: groups[gn].get("id") for gn in chosen}
    # RandomCondition{i} (1-based) -> cond_groups[i-1]
    cond_by_ident = {f"RandomCondition{i+1}": gn for i, gn in enumerate(cond_groups)}

    for it in root.iter("Item"):
        k = it.get("key")
        if k == "RandomCondition":
            ident = next(p.text for p in it.findall("Param") if p.get("key") == "#Identification#")
            gp = next(p for p in it.findall("Param") if p.get("key") == "#Group#")
            gn = cond_by_ident.get(ident or "")
            if gn is None:
                raise SystemExit(f"skeleton has RandomCondition '{ident}' but design has no group for it")
            gp.text = ids[gn]
        elif k == "RandomValue":
            if not value_group:
                raise SystemExit("skeleton has a RandomValue but shape declares no value group")
            gp = next(p for p in it.findall("Param") if p.get("key") == "#Group#")
            gp.text = ids[value_group]

    # embed the chosen groups (replace the skeleton's), deduped by id
    rg = root.find(".//RandomGroups")
    assert rg is not None, "skeleton missing <RandomGroups>"
    for g in list(rg.findall("Group")):
        rg.remove(g)
    for gn in chosen:
        rg.append(copy.deepcopy(groups[gn]))

    sn = root.find(".//StrategyName")
    if sn is not None:
        sn.text = name
    st = root.find("Strategy")
    if st is not None:
        st.set("name", name)

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

    outdir = outdir or os.path.join(HERE, "out")
    outpath = os.path.join(outdir, _safe_filename(name) + ".sqx")
    # Assemble the zip IN MEMORY and validate it BEFORE anything touches the disk:
    # a template that fails validation must leave NO .sqx behind (a broken file in
    # out/ is indistinguishable from a good one).
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)

    _validate(buf, install, shape=shape, display=os.path.basename(outpath))
    os.makedirs(outdir, exist_ok=True)
    with open(outpath, "wb") as f:
        f.write(buf.getvalue())
    return outpath


def generate_stop(name, cond1, cond2, value_group, install=DEFAULT_INSTALL, outdir=None):
    return _build(name, "stop", [cond1, cond2], value_group, install, outdir)


def generate_market(name, cond1, cond2, install=DEFAULT_INSTALL, outdir=None):
    return _build(name, "market", [cond1, cond2], None, install, outdir)


def generate_market_single(name, cond, install=DEFAULT_INSTALL, outdir=None):
    return _build(name, "market_single", [cond], None, install, outdir)


def from_design(spec, install=DEFAULT_INSTALL, outdir=None):
    """Realize a research-agent design spec into a .sqx. Dispatches by shape.

    spec = {name, shape, ...}
      stop          -> filter, trigger, price_pool
      market        -> filter, trigger
      market_single -> condition (or trigger)
    """
    shape = spec.get("shape", "stop")
    name = spec["name"]
    # stop_short takes the same holes as stop, but every pool must be BEARISH — the mirror
    # signal is emptied, so nothing flips the groups for you (see proto_short_fleet.py).
    if shape in ("stop", "stop_long", "stop_short"):
        return _build(name, shape, [spec["filter"], spec["trigger"]], spec["price_pool"], install, outdir)
    if shape in ("mtf_filter", "mtf_filter_long", "mtf_filter_short"):
        # daily_filter -> RandomCondition1 (the #Chart#=1 hole), trigger -> RandomCondition2
        return _build(name, shape, [spec["daily_filter"], spec["trigger"]], spec["price_pool"], install, outdir)
    if shape == "stop_long_single":
        cond = spec.get("trigger") or spec.get("condition") or spec.get("filter")
        return _build(name, shape, [cond], spec["price_pool"], install, outdir)
    if shape == "two_entry_market":
        return _build(name, shape, [spec["entry_a"], spec["entry_b"]], None, install, outdir)
    if shape == "role_market":
        return _build(name, shape, [spec["regime"], spec["trigger"], spec["veto"]], None, install, outdir)
    if shape in ("market", "market_long", "market_short", "session_market"):
        return _build(name, shape, [spec["filter"], spec["trigger"]], None, install, outdir)
    if shape == "market_single":
        cond = spec.get("condition") or spec.get("trigger") or spec.get("filter")
        return _build(name, shape, [cond], None, install, outdir)
    if shape == "multi_leg":
        return generate_multi_leg(name, spec["legs"], install, outdir)
    raise SystemExit(f"shape not supported yet: {shape!r} (have: {sorted(SHAPES)} + multi_leg)")


# --- multi-leg: dynamic assembly of N independent entry legs --------------------
# Generalizes the build-confirmed two_entry_market. Each leg = its own Condition group +
# order type (market|stop) + ExitAfterBars + a distinct MagicNumber. Stop legs also take a
# Value group for the stop price. Long-only; exit per-leg via ExitAfterBars ("nothing more").
# Templates (RandomCondition, EnterAtStop+RandomValue, the clean entry rule) come from the
# build-confirmed stop_long_single skeleton; EnterAtMarket from market_skeleton.
_SCAFFOLD = os.path.join(SKEL, "stop_long_single_skeleton.sqx")
_LONG_ENTRY_VAR = "33333333-1111-1111-3333-333333333333"


def _make_variable(vid, name, vtype, value):
    v = ET.Element("variable", {"makeExternal": "false"})
    for tag, val in (("id", vid), ("name", name), ("type", vtype), ("value", value)):
        ET.SubElement(v, tag).text = val
    ET.SubElement(v, "paramType")
    ET.SubElement(v, "makeExternal").text = "false"
    return v


def _set_param(item, key, text, drop_generate=False):
    p = next((p for p in item.iter("Param") if p.get("key") == key), None)
    if p is None:
        raise SystemExit(f"param {key} not on {item.get('key')}")
    p.text = text
    if drop_generate:
        for a in ("generate", "randomValue"):
            p.attrib.pop(a, None)


def _market_order_template():
    z = zipfile.ZipFile(os.path.join(SKEL, "market_skeleton.sqx"))
    r = ET.fromstring(z.read("strategy_Portfolio.xml"))
    z.close()
    return copy.deepcopy(next(it for it in r.iter("Item") if it.get("key") == "EnterAtMarket"))


def generate_multi_leg(name, legs, install=DEFAULT_INSTALL, outdir=None):
    """legs = [{group, order:'market'|'stop', exit_bars:int, price_pool?(stop)}], >=1."""
    if not legs:
        raise SystemExit("multi_leg needs >=1 leg")
    groups = _install_groups(install)
    for i, leg in enumerate(legs, 1):
        g = leg.get("group")
        if g not in groups:
            raise SystemExit(_missing_group_error(g, groups, prefix=f"leg {i}: "))
        if groups[g].get("type") != "Condition":
            raise SystemExit(f"leg {i}: {g} is {groups[g].get('type')}, expected Condition")
        order = leg.get("order", "market")
        if order not in ("market", "stop"):
            raise SystemExit(f"leg {i}: order must be 'market' or 'stop', got {order!r}")
        if order == "stop":
            pp = leg.get("price_pool")
            if pp not in groups:
                raise SystemExit(_missing_group_error(
                    pp, groups, prefix=f"leg {i}: stop needs a price_pool Value group; "))
            if groups[pp].get("type") != "Value":
                raise SystemExit(f"leg {i}: {pp} is {groups[pp].get('type')}, expected Value")

    z = zipfile.ZipFile(_SCAFFOLD)
    members = {n: z.read(n) for n in z.namelist()}
    z.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])
    pmap = {c: p for p in root.iter() for c in p}

    sig_rule = next(r for r in root.iter("Rule") if r.get("type") == "Signal")
    rc_template = copy.deepcopy(next(it for it in sig_rule.iter("Item") if it.get("key") == "RandomCondition"))
    entry_rule_template = copy.deepcopy(next(r for r in root.iter("Rule")
                                             if r.get("type") == "IfThen" and r.get("name") == "Long entry"))
    stop_order_template = copy.deepcopy(next(it for it in entry_rule_template.iter("Item")
                                             if it.get("key") == "EnterAtStop"))
    market_order_template = _market_order_template()

    variables = next(root.iter("Variables"))
    event = pmap[sig_rule]
    signals = sig_rule.find("signals")
    assert signals is not None, "Signal rule has no <signals>"
    for s in list(signals):
        signals.remove(s)
    for r in list(root.iter("Rule")):
        if r.get("type") == "IfThen":
            pmap[r].remove(r)

    referenced = []
    for i, leg in enumerate(legs, 1):
        entry_var = f"33333333-{i:04d}-9999-3333-333333333333"
        magic_var = f"99999999-{i:04d}-1111-1111-111111111111"
        variables.append(_make_variable(entry_var, f"Entry{i}Signal", "boolean", "false"))
        variables.append(_make_variable(magic_var, f"MagicNumber{i}", "int", str(10000 + i)))

        rc = copy.deepcopy(rc_template)
        _set_param(rc, "#Identification#", f"RandomCondition{i}")
        _set_param(rc, "#Group#", groups[leg["group"]].get("id"))
        referenced.append(leg["group"])
        sig = ET.SubElement(signals, "signal", {"variable": entry_var})
        sig.append(rc)

        rule = copy.deepcopy(entry_rule_template)
        rule.set("name", f"Entry {i}")
        iff = rule.find("If")
        assert iff is not None
        for it in iff.iter("Item"):
            if it.get("key") == "BooleanVariable":
                vp = next((p for p in it.findall("Param") if p.get("key") == "#Variable#"), None)
                if vp is not None and vp.text == _LONG_ENTRY_VAR:
                    vp.text = entry_var
                    break
        then = rule.find("Then")
        assert then is not None
        for it in list(then):
            if (it.get("key") or "").startswith("EnterAt"):
                then.remove(it)
        if leg.get("order", "market") == "market":
            order = copy.deepcopy(market_order_template)
        else:
            order = copy.deepcopy(stop_order_template)
            rv = next((it for it in order.iter("Item") if it.get("key") == "RandomValue"), None)
            if rv is None:
                raise SystemExit("stop order template has no RandomValue for the price")
            _set_param(rv, "#Group#", groups[leg["price_pool"]].get("id"))
            ridp = next((p for p in rv.findall("Param") if p.get("key") == "#Identification#"), None)
            if ridp is not None:
                ridp.text = f"RandomValue{i}"
            referenced.append(leg["price_pool"])
        _set_param(order, "#Direction#", "1")
        _set_param(order, "#MagicNumber#", magic_var)
        _set_param(order, "#AllowDuplicateTrades#", "false")
        _set_param(order, "#ExitAfterBars.ExitAfterBars#", str(leg.get("exit_bars", 0)), drop_generate=True)
        oid = next((p for p in order.findall("Param") if p.get("key") == "#Identification#"), None)
        if oid is not None:
            oid.text = f"Enter{i}"
        then.append(order)
        event.append(rule)

    rg = root.find(".//RandomGroups")
    assert rg is not None, "scaffold missing <RandomGroups>"
    for g in list(rg.findall("Group")):
        rg.remove(g)
    seen = set()
    for gn in referenced:
        if gn not in seen:
            seen.add(gn)
            rg.append(copy.deepcopy(groups[gn]))

    sn = root.find(".//StrategyName")
    if sn is not None:
        sn.text = name
    st = root.find("Strategy")
    if st is not None:
        st.set("name", name)

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    outdir = outdir or os.path.join(HERE, "out")
    outpath = os.path.join(outdir, _safe_filename(name) + ".sqx")
    # In-memory assembly + validate-before-write, same contract as _build: a failed
    # generation leaves NO file on disk.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
        for n, data in members.items():
            zo.writestr(n, data)
    _validate(buf, install, display=os.path.basename(outpath))
    os.makedirs(outdir, exist_ok=True)
    with open(outpath, "wb") as f:
        f.write(buf.getvalue())
    return outpath


def _validate(src, install, shape=None, display=None):
    """src: path to a .sqx on disk OR a file-like object (io.BytesIO) holding the zip
    bytes — the generators validate in memory BEFORE anything is written to disk."""
    avail = _avail(install)
    z = zipfile.ZipFile(src)
    raw = z.read("strategy_Portfolio.xml").decode("utf-8", "replace")
    r = ET.fromstring(raw)
    z.close()
    label = display or (os.path.basename(src) if isinstance(src, (str, os.PathLike))
                        else "<in-memory>")
    emb = {g.get("id") for g in r.findall(".//RandomGroups/Group")}
    refs = {p.text for p in r.iter("Param") if p.get("key") == "#Group#"}
    miss = sorted(k for it in r.findall(".//RandomGroups/Group/Item")
                  for k in [it.get("key") or ""]
                  if k.startswith("CBlock_") and k not in avail and k != "CBlock_null")
    dangling = refs - emb
    print(f"  validate {label}:")
    print(f"    blocks resolve : {'YES' if not miss else 'NO -> ' + str(miss)}")
    print(f"    group refs      : {'all embedded' if not dangling else 'DANGLING ' + str(dangling)}")
    print(f"    embedded groups : {sorted((g.get('name') or '') for g in r.findall('.//RandomGroups/Group'))}")
    # mtf_filter: the multi-timeframe mechanic must survive generation -- a 2-stream <Datas>
    # (main + a higher-TF subchart) AND at least one entry hole bound to the subchart (#Chart#!=0).
    mtf_bad = ""
    # covers _long / _short and any future twin. `shape` is None for multi_leg, which
    # assembles its legs directly rather than going through a named skeleton.
    if (shape or "").startswith("mtf_filter"):
        streams = [(d.findtext("id"), d.findtext("timeFrame")) for d in r.findall(".//Datas/data")]
        htf = sorted({p.text for p in r.iter("Param")
                      if p.get("key") == "#Chart#" and p.text not in (None, "0")})
        print(f"    MTF data streams: {streams}")
        print(f"    higher-TF holes : {htf if htf else 'NONE'}")
        if len(streams) < 2:
            mtf_bad = f"mtf_filter lost its subchart (streams={streams})"
        elif not htf:
            mtf_bad = "mtf_filter has no entry hole bound to the subchart (#Chart#=1)"
    # trading-soundness guards (EVERY shape) -- a template that builds but never trades is still a
    # failure. The entry TRIGGER must live in the Signal rule; if a RandomCondition leaks into an
    # entry IfThen it is usually paired with the example lineage's BarsSinceOrderClosed re-entry
    # guard (builds, but suppresses all trades -- the SessionBreakout bug). Both are banned.
    trigger_leak = sorted({rule.get("name") or "?"
                           for rule in r.iter("Rule") if rule.get("type") in ("IfThen", "IfThenElse")
                           for iff in [rule.find("If")] if iff is not None
                           if any(it.get("key") == "RandomCondition" for it in iff.iter("Item"))})
    reentry_guard = "BarsSinceOrderClosed" in raw
    print(f"    trades soundly  : {'YES' if not (trigger_leak or reentry_guard) else 'NO'}"
          + (f" -> trigger in entry rule {trigger_leak}" if trigger_leak else "")
          + (" -> BarsSinceOrderClosed re-entry guard present" if reentry_guard else ""))
    if miss or dangling or mtf_bad or trigger_leak or reentry_guard:
        reasons = []
        if miss:
            reasons.append("unresolved custom blocks (not in the install's "
                           f"customBlocks.xml): {', '.join(miss)}")
        if dangling:
            reasons.append(f"#Group# refs not embedded: {', '.join(sorted(map(str, dangling)))}")
        if mtf_bad:
            reasons.append(mtf_bad)
        if trigger_leak:
            reasons.append(f"trigger leaked into entry rule(s) {trigger_leak}")
        if reentry_guard:
            reasons.append("BarsSinceOrderClosed re-entry guard (suppresses trades)")
        raise SystemExit("VALIDATION FAILED" + (f": {'; '.join(reasons)}" if reasons else ""))
    print("    OK")


if __name__ == "__main__":
    install = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INSTALL
    # one design per shape, to prove all three skeletons bind + validate
    demos = [
        dict(name="TrendFilteredBreakout_Spike", shape="stop",
             filter="TrendUP", trigger="BreakoutUP", price_pool="BreakoutChannels"),
        dict(name="TrendBreakoutMarket_Spike", shape="market",
             filter="TrendUP", trigger="BreakoutUP"),
        dict(name="TrendOnlyMarket_Spike", shape="market_single",
             condition="TrendUP"),
    ]
    for d in demos:
        p = from_design(d, install=install)
        print("written:", p, "\n")
