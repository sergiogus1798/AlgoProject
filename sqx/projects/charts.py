#!/usr/bin/env python3
"""The extra chart a multi-timeframe template needs, in the three places SQX reads it."""

import re
from pathlib import Path

from core.sqxfile import xml
from sqx.projects.patch import NO_TEMPLATE

# SQX names a Setup chart by its timeframe code and the builder's chart list by "<code> chart".
# A stream whose timeframe is not here is refused rather than guessed: the name is what
# BlockSettingsConverter indexes by, and an invented one binds the hole to nothing.
TF_NAME = {240: "H4", 1440: "D1", 10080: "W1"}

STRATEGY_TYPE = re.compile(r"<StrategyType[^>]*>")
SETUP = re.compile(r"<Setup\b.*?</Setup>", re.S)
# Every chart of a Setup, in SQX's own spelling. The RulesComplexity charts carry `name=`
# instead of `symbol=` and are a different list, indexed by the builder, not a data source.
SETUP_CHART = re.compile(r'<Chart symbol="([^"]*)" timeframe="([^"]*)" spread="([^"]*)"\s*/>')
MAIN_RULE_CHART = re.compile(r'<Chart name="Main chart"([^>]*)/>')


def wanted(template: Path) -> list[int]:
    """The extra data streams a template declares, in minutes.

    Args:
        template: A template or strategy .sqx.

    Returns:
        One entry per stream above the main chart, which carries timeFrame 0 and takes the
        task's own. Empty for a single-chart template.
    """
    streams = [int(d.findtext("timeFrame")) for d in xml(template).iterfind(".//Datas/data")]
    return [tf for tf in streams if tf > 0]


def template_of(text: str) -> Path | None:
    """The template a task builds from.

    Args:
        text: A task XML.

    Returns:
        None when the task builds generically, names SQX's Simple-Strategy placeholder, or
        names a file this machine does not have — a template the install is missing is
        `template_check`'s finding, not this module's.
    """
    tag = STRATEGY_TYPE.search(text)
    if not tag or 'type="template"' not in tag.group(0):
        return None
    named = re.search(r'templateFile="([^"]*)"', tag.group(0))
    if not named or named.group(1) in ("", NO_TEMPLATE):
        return None
    path = Path(named.group(1))
    return path if path.exists() else None


def streams(members: dict[str, bytes]) -> list[int]:
    """The extra data streams the strategies of a project carry, in minutes.

    Args:
        members: The .cfx contents by member name.

    Returns:
        What the Build task's template declares; empty for a single-chart project. Needing
        a second chart is a property of the project's STRATEGIES, so every task that tests
        them needs it — and most retest tasks name no template of their own to read it from.
    """
    for name in sorted(members):
        if name.endswith(".xml") and name != "config.xml":
            template = template_of(members[name].decode("utf-8"))
            if template and wanted(template):
                return wanted(template)
    return []


def _one_chart_per_setup(text: str) -> str:
    """Drop every data chart of a Setup but the first.

    Args:
        text: A task XML.

    Returns:
        The text with each Setup back to its main chart alone. `set_timeframe` rewrites the
        timeframe of every chart it finds, so a second pass over an already-wired project
        would otherwise leave the extra chart flattened onto the main timeframe and
        `ensure` would add a third. Normalising first makes the pair idempotent.
    """
    for setup in SETUP.findall(text):
        if len(SETUP_CHART.findall(setup)) < 2:
            continue
        first = SETUP_CHART.search(setup)
        kept = setup[:first.end()] + SETUP_CHART.sub("", setup[first.end():])
        text = text.replace(setup, kept, 1)
    return text


def ensure(text: str, extra: list[int]) -> tuple[str, int]:
    """Make a task able to test strategies that read more than one chart.

    Args:
        text: A task XML, after the timeframe and the costs are written.
        extra: Output of `streams` for the task's project.

    Returns:
        The text and how many charts were added. A no-op for a single-chart project.

    Three insertions, all required (reverse-engineered 2026-07-18, confirmed by a live run):
    a chart in EVERY Setup, the cross-checks' included, or SQX refuses the project with
    "Strategy from template file requires 2 charts, 1 defined"; a `<data>` stream in the
    task's own `<Datas>`, when the donor carries one; and a chart under `<RulesComplexity>`,
    which is the list the builder indexes `#Chart#` against — without it every `#Chart#=1`
    binding degrades to the main chart in silence and the strategies read the filter on the
    wrong timeframe.
    """
    if not extra or not SETUP_CHART.search(text):
        return text, 0
    unknown = [tf for tf in extra if tf not in TF_NAME]
    if unknown:
        raise SystemExit(f"el flujo de {unknown[0]} min no tiene nombre de gráfico en SQX. "
                         "Hay que añadirlo a charts.TF_NAME, no se adivina.")
    text, added = _one_chart_per_setup(text), 0
    for stream, tf in enumerate(extra, start=1):
        name = TF_NAME[tf]
        text, n = SETUP_CHART.subn(
            rf'\g<0>\n        <Chart symbol="\g<1>" timeframe="{name}" spread="\g<3>" />', text)
        added += n
        if (re.search(r"</data>\s*</Datas>", text)
                and f"<timeFrame>{tf}</timeFrame>" not in text):
            text = re.sub(r"</data>\s*</Datas>",
                          "</data>\n            <data>\n"
                          f"              <id>{stream}</id>\n"
                          "              <symbol>NULL</symbol>\n"
                          "              <chart>Main chart</chart>\n"
                          f"              <timeFrame>{tf}</timeFrame>\n"
                          "            </data>\n          </Datas>", text, count=1)
        if MAIN_RULE_CHART.search(text) and f'<Chart name="{name} chart"' not in text:
            text = MAIN_RULE_CHART.sub(rf'\g<0><Chart name="{name} chart"\g<1>/>', text, count=1)
    return text, added


def missing(text: str, extra: list[int]) -> list[str]:
    """Why this task cannot test its project's multi-chart strategies, one line each.

    Args:
        text: A task XML.
        extra: Output of `streams` for the task's project.

    Returns:
        Empty when it can. A Setup short of charts is the hard error SQX raises at start; a
        Build task without the RulesComplexity chart is worse, because it builds and lies
        about which timeframe the filter was read on.
    """
    out = []
    for setup in SETUP.findall(text) if extra else []:
        found = len(SETUP_CHART.findall(setup))
        if found != len(extra) + 1:
            out.append(f"las estrategias piden {len(extra) + 1} gráficos y un Setup define "
                       f"{found}: SQX abortará con «requires {len(extra) + 1} charts, "
                       f"{found} defined».")
    for tf in extra:
        if MAIN_RULE_CHART.search(text) and f'<Chart name="{TF_NAME[tf]} chart"' not in text:
            out.append(f"la plantilla lee en {TF_NAME[tf]} y <RulesComplexity> no lista ese "
                       "gráfico: cada hueco #Chart#=1 caería al gráfico principal sin avisar, "
                       "y las estrategias leerían el filtro en el timeframe de la señal.")
    return out
