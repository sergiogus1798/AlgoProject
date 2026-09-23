#!/usr/bin/env python3
"""Task settings that must be identical across a whole project: timeframe, engine, MM, hours."""

import re
from pathlib import Path

BUILDMODE_MODEL = Path(__file__).with_name("buildmode_model.xml")
BUILDMODE = re.compile(r"<BuildMode\b.*?</BuildMode>", re.S)
CROSSCHECKS = re.compile(r"<CrossChecks\b.*?</CrossChecks>", re.S)


def set_timeframe(text: str, timeframe: str) -> tuple[str, int]:
    """Put every chart of every Setup on one timeframe.

    Args:
        text: A task XML.
        timeframe: SQX timeframe name, e.g. "M30".

    Returns:
        The text and how many charts moved. Every chart, including a cross-check on a
        second market: a project whose retest runs on a different timeframe than its
        build is not testing the strategy it built.
    """
    tags = re.findall(r'<Chart symbol="[^"]*"[^>]*>', text)
    for tag in tags:
        text = text.replace(tag, re.sub(r'timeframe="[^"]*"', f'timeframe="{timeframe}"', tag), 1)
    return text, len(tags)


def set_engine(text: str, engine: str) -> str:
    """Put every Setup on one backtest engine.

    Args:
        text: A task XML.
        engine: Engine name exactly as SQX writes it, e.g. "MetaTrader5 (hedged)".

    Returns:
        The text with the engine attribute rewritten on every <Setup>.
    """
    return re.sub(r'(<Setup\b[^>]*?)engine="[^"]*"', rf'\g<1>engine="{engine}"', text)


def set_precision(text: str, precision: int) -> str:
    """Put every Setup of a task on one backtest precision.

    Args:
        text: A task XML.
        precision: SQX's testPrecision — 1 is the selected timeframe only, 2 is one minute.

    Returns:
        The text with the precision rewritten on every <Setup>. The build runs at the
        selected timeframe because a minute-precision build would never finish, and leans
        on the high-precision cross-check to drop what only exists on the big bars.
        Everything after it runs at one minute, the main backtest included.
    """
    return re.sub(r'(<Setup\b[^>]*?)testPrecision="[^"]*"',
                  rf'\g<1>testPrecision="{precision}"', text)


def set_params(text: str, values: dict) -> tuple[str, int]:
    """Rewrite named <Param key="…"> entries wherever they appear in a task.

    Args:
        text: A task XML.
        values: Param key to its new text value.

    Returns:
        The text and how many params were actually rewritten. The count is returned
        because these params carry a className attribute after the key, and a pattern
        that assumes they do not matches nothing and changes nothing, in silence.
    """
    done = 0
    for key, value in values.items():
        text, n = re.subn(rf'(<Param key="{key}"[^>]*>)[^<]*', rf"\g<1>{value}", text)
        done += n
    return text, done


def set_session(text: str, session: str) -> tuple[str, int]:
    """Point the task at the trading session of the asset it trades.

    Args:
        text: A task XML.
        session: Session name as SQX defines it under <Resources><Sessions>.

    Returns:
        The text and how many charts' sessions were rewritten.
    """
    return set_params(text, {"MarketOpenSession": session})


def session_defined(text: str, session: str) -> bool:
    """Whether the session the task names actually exists in the project's resources.

    Args:
        text: A task XML.
        session: Session name.

    Returns:
        True when <Resources><Sessions> defines it. A task naming a session the project
        does not carry loads without complaint and trades the wrong hours.
    """
    return f'<Session name="{session}"' in text


def set_money_management(text: str, mm: dict) -> str:
    """Make one sizing method the only one in use, with its parameters.

    Args:
        text: A task XML.
        mm: The doctrine's `money_management` mapping.

    Returns:
        The text with that method on, every other off, and the capital and drawdown cap
        applied. This has to be identical in every task of a project: return and drawdown
        are sizing-dependent, so an IS and an OOS sized differently cannot be compared.
    """
    section = re.search(r"<MoneyManagement>.*?</MoneyManagement>", text, re.S).group(0)
    out = re.sub(r'(<Method type="(\w+)"[^>]*?)use="[^"]*"',
                 lambda m: f'{m.group(1)}use="{str(m.group(2) == mm["method"]).lower()}"', section)
    chosen = re.search(rf'<Method type="{mm["method"]}".*?</Method>', out, re.S).group(0)
    fixed = chosen
    for key, value in mm["params"].items():
        fixed = re.sub(rf'(<Param key="{key}"[^>]*>)[^<]*', rf"\g<1>{value}", fixed)
    out = out.replace(chosen, fixed, 1)
    out = re.sub(r"<InitialCapital>[^<]*</InitialCapital>",
                 f"<InitialCapital>{mm['initial_capital']}</InitialCapital>", out)
    text = text.replace(section, out, 1)
    return re.sub(r'(<RiskManagement\b[^>]*?)maxDrawdown="[^"]*"',
                  rf'\g<1>maxDrawdown="{mm["max_drawdown"]}"', text)


def set_crosschecks(text: str, cc: dict, spread: float, enabled: list) -> str:
    """Leave only the cross-checks the doctrine turns on, priced like the main test.

    Args:
        text: A task XML.
        cc: The doctrine's `crosschecks` mapping.
        spread: The segment's spread, in points.
        enabled: The cross-checks to leave on in this task. Empty for everything after the
            build: once the task itself runs at minute precision, re-running it at minute
            precision proves nothing.

    Returns:
        The text with every cross-check off except the listed ones. The high-precision
        retest carries a <Spread> of its own under CustomSpread: the donor ships it at
        zero, which reruns the strategy for free and calls the result a robustness check.
    """
    found = CROSSCHECKS.search(text)
    if not found:
        return text
    out = found.group(0)
    for name in re.findall(r"<(\w+) use=\"(?:true|false)\">", out):
        out = re.sub(rf'(<{name} )use="[^"]*"', rf'\g<1>use="{str(name in enabled).lower()}"', out)
    hp = re.search(r"<RetestWithHigherPrecision.*?</Settings>", out, re.S)
    if hp:
        fixed = re.sub(r"<Spread>[^<]*</Spread>", f"<Spread>{spread}</Spread>", hp.group(0))
        fixed = re.sub(r"<Precision>[^<]*</Precision>", f"<Precision>{cc['precision']}</Precision>",
                       fixed)
        out = out.replace(hp.group(0), fixed, 1)
    return text.replace(found.group(0), out, 1)


def set_genetic(text: str) -> bool | str:
    """Replace the genetic settings with the owner's model project, verbatim.

    Args:
        text: A task XML.

    Returns:
        The text, or it unchanged when the task has no <BuildMode> — only a Build task
        does. The block is a copy of his own tuned project rather than values chosen
        here; `buildmode_model.xml` says where it came from and when.
    """
    if not BUILDMODE.search(text):
        return text
    model = BUILDMODE.search(BUILDMODE_MODEL.read_text(encoding="utf-8")).group(0)
    return BUILDMODE.sub(lambda _: model, text, count=1)


def set_databank_caps(text: str, databank: dict) -> str:
    """Set what stops the run.

    Args:
        text: A task XML.
        databank: The doctrine's `databank` mapping.

    Returns:
        The text with the stop condition's type applied. How many strategies the databank
        holds is the caller's, because a smoke test and a real build differ in exactly
        that one number and nothing else.
    """
    return re.sub(r'(<StopCondition\b[^>]*?)type="[^"]*"',
                  rf'\g<1>type="{databank["stop_condition"]}"', text)


def session_block(text: str, session: str) -> str | None:
    """The definition of one trading session, as the task carries it.

    Args:
        text: A task XML.
        session: Session name.

    Returns:
        The <Session>…</Session> element, or None when this task does not define it.
    """
    found = re.search(rf'<Session name="{re.escape(session)}">.*?</Session>', text, re.S)
    return found.group(0) if found else None


def add_session(text: str, block: str) -> str:
    """Give a task the session definition it names but does not carry.

    Args:
        text: A task XML.
        block: A <Session>…</Session> element.

    Returns:
        The text with that session added under <Resources><Sessions>. The donor's own
        tasks disagree: its Build defines XAUUSD_the5ers and its Retest XAUUSD_ftmo, each
        defining only its own. Pointing every task at one session is only half the job —
        a task that names a session it does not define trades the wrong hours in silence.
    """
    return text.replace("</Sessions>", f"{block}</Sessions>", 1)
