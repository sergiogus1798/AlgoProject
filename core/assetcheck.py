"""What is missing or wrong about an asset: undecided values, and windows the data cannot fill."""

from datetime import date

from core.assetdata import fields, load, schema

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
        `commission` is a special shape (owner, 2026-09-29): its `use` is `null` until the
        first broker table is written, and after that one `{method, value}` per segment —
        blocked while ANY segment still carries a null `value`, not while the field itself
        is null.
    """
    def blocked(field: str) -> bool:
        """Whether this field still has a real decision missing."""
        use = data["costs"][field]["use"]
        if isinstance(use, dict):
            return any(v["value"] is None for v in use.values())
        return use is None

    return [k for k in REQUIRED[data["class"]] if blocked(k)]



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
        Names of the ranges that resolve to nothing at all. A range the asset leaves null
        now falls back to `mc_retest.default_multiples` of `_policy.yaml`, so this is empty
        unless the policy has no multiple for it either. These never block authoring: an
        undecided range only makes that one MC Retest task uninterpretable.
    """
    # Imported here and not at the top: assetcheck is the pure-file half and assetdata reads
    # the policy, so importing it up here would make the two modules circular.
    from core.assetranges import mc_retest

    return [k for k, v in mc_retest(data).items() if v["min"] is None or v["max"] is None]
