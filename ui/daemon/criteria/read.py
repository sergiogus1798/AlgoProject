"""What the Criterios zone shows: criteria.yaml step by step, the Build filters, the freeze."""

import hashlib
import json

import pyarrow.parquet as pq
import yaml

from core import buildfilters
from core.assetyaml import hint, read
from core.paths import ROOT
from core.researchpaths import autopilot_runs
from ui.daemon.results.catalogue import STUDIES
from ui.daemon.workflow.steps import STEPS
from ui.text.glossary import label

# The file the autopilot judges with and the history of what the window changed in it. A dict
# so a test points both at copies.
FILES = {"criteria": ROOT / "pipeline" / "autopilot" / "criteria.yaml",
         "history": ROOT / "ledger" / "criteria-history.jsonl",
         "offered": ROOT / "pipeline" / "autopilot" / "offered.yaml"}
WORDS = {"pass": "Aprobado", "fail": "Suspenso"}
GROUPS = {"all": "Todas", "any": "Alguna"}
SHOWN = 30      # history rows sent to the window, newest first


def plain(node: object) -> object:
    """A document read with its comments, as plain dicts, lists and scalars."""
    return json.loads(json.dumps(node, default=str))


def sha(steps: dict) -> str:
    """What the rules and cuts are, in twelve characters: a freeze records it, so a file edited
    by hand afterwards shows."""
    return hashlib.sha256(json.dumps(steps, sort_keys=True).encode()).hexdigest()[:12]


def name(fact: str) -> str:
    """A fact key in words: its study's title on screen and its last part, humanised."""
    study, _, rest = fact.partition(".")
    title = STUDIES[study][2] if study in STUDIES else label(study)
    return f"{title} · {label(rest.split('.')[-1])}" if rest else title


def kind(rule: dict) -> str:
    """The column «Tipo»: a compound, a verdict, or a number SQX computed or the app did.

    A fact is SQX's own when its key says so (`pf_sqx_oos`, `neto_sqx_is`, `net_sqx`): the
    studies name what they copy from the databank that way.
    """
    if "all" in rule or "any" in rule:
        return "Compuesto"
    if "is" in rule:
        return "Veredicto"
    return "Métrica SQX" if "sqx" in rule["fact"].rsplit(".", 1)[-1].lower() else "Test de la app"


def test(rule: dict) -> tuple[str, str]:
    """A rule's two conditions as the table says them.

    Args:
        rule: One rule, or the fields of a `by` entry folded over its rule.

    Returns:
        (what passes, what is limbo). «—» where the rule has no limbo band: not passing
        is then a fail.
    """
    if "all" in rule or "any" in rule:
        word = "all" if "all" in rule else "any"
        parts = [f"{name(r['fact']) if 'fact' in r else GROUPS['all' if 'all' in r else 'any']} "
                 f"{test(r)[0]}" for r in rule[word]]
        return f"{GROUPS[word]}:\n" + "\n".join(parts), "—"
    other = "Si no cumple" if rule.get("else") == "limbo" else "—"
    if "is" in rule:
        return WORDS[rule["is"]], other
    if "near_median" in rule:
        band = "A ±{:g} % de la mediana".format
        return (band(100 * rule["near_median"]),
                band(100 * rule["limbo_near_median"]) if "limbo_near_median" in rule else other)
    return str(rule["pass"]), str(rule.get("limbo", other))


def row(rule: dict) -> dict:
    """One rule as a table row.

    Args:
        rule: As criteria.yaml holds it.

    Returns:
        `rule` itself (what an edit sends back as `was`), `label` and `tip` for «Criterio»,
        `kind`, `passes`, `limbo`, and `by` — one sentence per exception. `state` adds `why`,
        the comment the file carries above the rule.
    """
    passes, limbo = test(rule)
    own = {k: v for k, v in rule.items() if k != "by"}
    by = [f"{tags}: {' · limbo '.join(t for t in test(own | fields) if t != '—')}"
          for tags, fields in (rule.get("by") or {}).items()]
    fact = rule.get("fact", "")
    parts = rule.get("all") or rule.get("any") or []
    shown = name(fact) if fact else f"{GROUPS['all' if 'all' in rule else 'any']} de {len(parts)}"
    return {"rule": rule, "label": rule.get("name") or shown, "tip": fact or passes,
            "kind": kind(rule), "passes": passes, "limbo": limbo, "by": "; ".join(by)}


def offered(n: str, used: list[dict]) -> list[dict]:
    """The facts offered.yaml lists for step `n` that no rule names yet, as rows with no threshold.

    Args:
        n: Step number.
        used: The step's rules.

    Returns:
        Rows shaped as `row`'s, `passes` and `limbo` «—»: computed, shown, judging nothing.
    """
    ruled = {r.get("fact") for r in used}
    listed = yaml.safe_load(FILES["offered"].read_text(encoding="utf-8")).get(n) or []
    return [{"fact": o["fact"], "label": o["name"], "kind": "Test de la app", "passes": "—",
             "limbo": "—", "by": "",
             "tip": f"{o['fact']}\n\nDisponible, sin umbral todavía: no juzga hasta que se "
                    f"le ponga uno. Lo que da sin ventaja: {o['card']}"}
            for o in listed if o["fact"] not in ruled]


def menu(n: str, used: list[dict]) -> list[dict]:
    """The facts a rule of step `n` may name: those of the newest autopilot run that judged it,
    the ones offered.yaml lists for it, plus the ones its rules already name.

    Args:
        n: Step number.
        used: The step's rules.

    Returns:
        `{fact, label, sqx}` sorted by label. Empty for a step no run has gathered yet: the
        dialog still takes a key typed by hand.
    """
    found = sorted(autopilot_runs().glob(f"*/*/paso-{n}/hechos.parquet"),
                   key=lambda p: p.parts[-3])
    keys = set(pq.read_table(found[-1], columns=["key"]).column("key").unique().to_pylist()) \
        if found else set()
    keys |= {r["fact"] for rule in used for r in [rule, *(rule.get("all") or rule.get("any") or [])]
             if "fact" in r}
    keys |= {o["fact"] for o in offered(n, [])}
    return sorted(({"fact": k, "label": name(k), "sqx": "sqx" in k.rsplit(".", 1)[-1].lower()}
                   for k in keys), key=lambda f: (f["label"], f["fact"]))


def build() -> dict:
    """Step 6: the Build's acceptance filters of assets/_study.yaml, the only criteria SQX
    itself applies. Read only here."""
    study = yaml.safe_load(buildfilters.STUDY.read_text(encoding="utf-8"))
    base, sample = study["defaults"], study["sample"]
    own = {**(study.get("classes") or {}), **(study.get("symbols") or {})}
    per_year = " · ".join(f"{tf}: {v['min']:g}" + (f" a {v['max']:g}" if v.get("max") is not None else " o más")
                          for tf, v in base["trades_per_year"].items())
    rows = [("Operaciones por año", "NumberOfTrades", per_year),
            ("Profit Factor", "ProfitFactor", f">= {base['profit_factor_min']:g}"),
            ("Net Profit", "NetProfit", f"> {base['net_profit_min']:g}")]
    keys = ("trades_per_year", "profit_factor_min", "net_profit_min")
    return {"where": "assets/_study.yaml", "rows": [
        {"label": f"{text} · {sample}", "tip": f"{metric} ({sample}) — `{key}` de _study.yaml",
         "kind": "Métrica SQX", "passes": passes, "limbo": "—",
         "by": ", ".join(who for who, fields in own.items() if key in fields),
         "why": "\n".join(f"{w}: {json.dumps(f[key])}" for w, f in own.items() if key in f)}
        for (text, metric, passes), key in zip(rows, keys)]}


def said(rule: object) -> str:
    """One side of a history line in words: a rule; a step's whole list of rules, replaced at
    once, as its lines joined; a plain value (a cut) as itself; «—» for none
    and for the freeze's own mark."""
    if isinstance(rule, list):
        return "; ".join(map(said, rule)) or "—"
    if not isinstance(rule, dict):
        return "—" if rule is None else str(rule)
    if not rule or "sha" in rule:
        return "—"
    if not ({"fact", "all", "any"} & rule.keys()):   # a setting, like `medoids`
        return "; ".join(f"{k} = {v}" for k, v in rule.items())
    return f"{row(rule)['label']}: " + " · limbo ".join(t for t in test(rule) if t != "—")


def history() -> list[dict]:
    """The newest changes the window wrote, newest first, `was` and `now` worded."""
    file = FILES["history"]
    lines = file.read_text(encoding="utf-8").splitlines() if file.exists() else []
    return [h | {"was": said(h["before"]), "now": said(h["after"])}
            for h in map(json.loads, lines[-SHOWN:][::-1])]


def state() -> dict:
    """Everything the zone paints, in one round trip.

    Returns:
        `frozen` (None, or `on`, `by` and `changed`: the file no longer matches what was
        frozen), `build` (step 6), `steps` — every step that has tests or an entry in
        criteria.yaml, in WORKFLOW's order, each with `n`, `title`, `cut` (None: the file gives
        it no databank to cut, so no rule can be added from here), `rows`, `facts` and
        `offered` (facts published for a criterion with no threshold yet) — and `history`.
    """
    noted = read(FILES["criteria"])
    lines = FILES["criteria"].read_text(encoding="utf-8").splitlines()
    doc = plain(noted)
    frozen, steps = doc.get("frozen"), []
    for s in STEPS:
        if s["n"] not in doc["steps"] and (not s["studies"] or s["n"] == "6"):
            continue
        spec = doc["steps"].get(s["n"], {})
        rules = spec.get("rules") or []
        at = noted["steps"][s["n"]]["rules"].lc.data if rules else {}
        steps.append({"n": s["n"], "title": s["title"], "cut": spec.get("cut"),
                      "rows": [row(r) | {"why": hint(lines, at[i][0])}
                               for i, r in enumerate(rules)],
                      "facts": menu(s["n"], rules), "offered": offered(s["n"], rules)})
    return {"frozen": frozen and {**frozen, "changed": frozen["sha"] != sha(doc["steps"])},
            "build": build(), "steps": steps, "history": history()}
