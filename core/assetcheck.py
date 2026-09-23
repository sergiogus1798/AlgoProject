"""What is missing or wrong about an asset: undecided values, and windows the data cannot fill."""

from datetime import date

from core.assetdata import fields, load, schema, sqx_settings

# Cost fields that block authoring while undecided, per class. The swaps do not block.
REQUIRED = {"forex": ("spread", "commission"),
            "no_forex": ("spread_is", "spread_oos", "commission")}



def validate(data: dict) -> list[str]:
    """What this asset's file gets wrong against its class.

    Args:
        data: One asset as load() returned it.

    Returns:
        One line per problem, empty when the file matches its class. Checked rather than
        remembered: a forex file with two spreads is an error, not a convention to know.
    """
    want, have, cls = set(fields(data)), set(data["costs"]), data["class"]
    return ([f"falta `{f}`, que exige la clase `{cls}`" for f in sorted(want - have)]
            + [f"sobra `{f}`, la clase `{cls}` no lo tiene" for f in sorted(have - want)]
            + [f"falta `mc_retest.{k}`" for k in ("spread", "slippage")
               if k not in (data.get("mc_retest") or {})]
            + [f"`instrument.{k}` no es un número: {v!r} — comentario pegado al valor"
               for k, v in data["instrument"].items() if not isinstance(v, (int, float))]
            + before_data(data))



def pending(data: dict) -> list[str]:
    """Fields whose real value the owner has not decided yet.

    Args:
        data: One asset as load() returned it.

    Returns:
        Names of required fields still carrying a null `use` value, per the asset's class.
    """
    return [k for k in REQUIRED[data["class"]] if data["costs"][k]["use"] is None]



def provisional(data: dict) -> list[str]:
    """Required fields decided with a stand-in rather than the broker's real figure.

    Args:
        data: One asset as load() returned it.

    Returns:
        EVERY cost field whose `why` says PROVISIONAL, not only the blocking ones. Such a
        value is a decision and does not block, but it stamps every result built on it —
        and a run priced with a stand-in swap is as provisional as one with a stand-in
        spread.
    """
    return [k for k in fields(data) if "PROVISIONAL" in data["costs"][k]["why"]]



def segments_pending(data: dict) -> list[str]:
    """Segments whose dates the owner has not set for this asset.

    Args:
        data: One asset as load() returned it.

    Returns:
        Segment names still carrying a null bound. They do not block authoring — the costs
        already do — but window() refuses to invent one.
    """
    return [n for n, s in data["segments"].items() if s["from"] is None or s["to"] is None]



def before_data(data: dict) -> list[str]:
    """Segments that ask for history SQX does not have.

    Args:
        data: One asset as load() returned it.

    Returns:
        One line per segment starting before the feed's first bar. This is the error the
        per-asset windows exist to prevent: gold has data from 2003 and builds from 2008,
        while the DAX40 has nothing before 2013 and a 2008 window would silently run short.
    """
    if not data["data"]:
        return [f"SQX no tiene datos de `{data['sqx_symbol']}`, así que ninguna ventana es válida"]
    first = data["data"]["from"]
    year = lambda b: b if isinstance(b, int) else b.year
    return [f"el tramo `{n}` empieza en {s['from']} y los datos de `{data['sqx_symbol']}` "
            f"empiezan en {first}"
            for n, s in data["segments"].items()
            if s["from"] is not None and year(s["from"]) < first.year]



def past_data(data: dict) -> list[str]:
    """Segments that run past the last bar SQX holds.

    Args:
        data: One asset as load() returned it.

    Returns:
        One line per segment ending after the feed's last bar. A warning and not an error:
        the window is right and the data is simply not synced yet, which is the normal state
        of the newest segment.
    """
    if not data["data"]:
        return []
    last = data["data"]["to"]
    end = lambda b: date(b, 12, 31) if isinstance(b, int) else b
    return [f"el tramo `{n}` llega a {s['to']} y los datos de `{data['sqx_symbol']}` acaban "
            f"en {last}" for n, s in data["segments"].items()
            if s["to"] is not None and end(s["to"]) > last]



def mc_pending(data: dict) -> list[str]:
    """MC Retest ranges the owner has not decided yet.

    Args:
        data: One asset as load() returned it.

    Returns:
        Names of the ranges still carrying a null bound. These do NOT block authoring: an
        undecided range only makes that one MC Retest task uninterpretable, and the report
        says so rather than stopping the work.
    """
    return [k for k, v in data["mc_retest"].items() if v["min"] is None or v["max"] is None]


def cost_gap(data: dict, segment: str) -> list[str]:
    """Costs the run will NOT be priced with, because SQX carries something else.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread on a no_forex asset.

    Returns:
        One line per cost whose declared `use` differs from the `sqx_now` the master
        carries. Measured 2026-09-23: a task whose <InstrumentInfo> disagrees with SQX's
        instrument registry makes the project refuse to start, and that registry lives in
        `user/data/data.db`, which every worker start copies from the master. So a worker
        is always priced with the master's figures and declaring others here changes
        nothing until the owner edits the master's own instrument list.
    """
    def same(a: object, b: object) -> bool:
        """Whether two cost values mean the same number; 10 and 10.0 do."""
        try:
            return float(a) == float(b)
        except (TypeError, ValueError):
            return str(a) == str(b)

    use = sqx_settings(data, segment)
    now = data["costs"]
    out = []
    spread = "spread" if data["class"] == "forex" else f"spread_{data['segments'][segment]['spread']}"
    if not same(now[spread]["sqx_now"], use["defaultSpread"]):
        out.append(f"spread: assets dice {use['defaultSpread']}, SQX lleva {now[spread]['sqx_now']}")
    slip = f"slippage_{data['segments'][segment]['spread']}"
    if not same(now[slip]["sqx_now"], use["defaultSlippage"]):
        out.append(f"slippage: assets dice {use['defaultSlippage']}, SQX lleva "
                   f"{now[slip]['sqx_now']}")
    method = (now["commission"]["sqx_now"] or {}).get("method")
    if method != use["commission"]["method"]:
        out.append(f"comision: assets dice {use['commission']['method']} "
                   f"{use['commission']['value']}, SQX lleva {method} "
                   f"{(now['commission']['sqx_now'] or {}).get('value')}")
    if (now["swap_long"]["sqx_now"] or {}).get("type") != use["swap"]["type"]:
        out.append(f"swap: assets dice {use['swap']['type']} {use['swap']['long']}/"
                   f"{use['swap']['short']}, SQX lleva "
                   f"{(now['swap_long']['sqx_now'] or {}).get('type')} "
                   f"{(now['swap_long']['sqx_now'] or {}).get('value')}/"
                   f"{(now['swap_short']['sqx_now'] or {}).get('value')}")
    return out
