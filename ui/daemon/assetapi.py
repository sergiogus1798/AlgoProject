"""The routes of the asset library: every question the assets zone asks, and its writes."""

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import assets

ROUTER = APIRouter()


class ValueChange(BaseModel):
    """One value of one assets/ file, as the window typed it."""

    name: str
    path: list[str]
    text: str
    kind: str = "scalar"


class CostChange(BaseModel):
    """A cost and the line that justifies it, which are written together or not at all."""

    field: str
    text: str
    why: str


class NewAsset(BaseModel):
    """An instrument about to enter the library, with every cost still undecided."""

    symbol: str
    cls: str
    broker: str
    sqx_symbol: str
    session: str = ""
    tick_size: str
    point_value: str
    min_distance: str


class MarketChange(BaseModel):
    """One category of one asset's retest universe, complete."""

    symbol: str
    category: str
    feeds: list[dict]


@ROUTER.get("/api/assets")
def asset_state() -> dict[str, object]:
    """Every asset with what blocks it, plus the retired shelf and the class schemas.

    Returns:
        What `assets.state` builds, in one round trip.
    """
    return assets.state()


@ROUTER.get("/api/asset/{symbol}")
def asset(symbol: str) -> dict[str, object]:
    """One asset in full.

    Args:
        symbol: Asset name.

    Returns:
        Costs, windows, MC Retest ranges, retest universe, preflight complaints and the
        file's own editable leaves.
    """
    return assets.one(symbol)


@ROUTER.get("/api/assets/shared/{name}")
def shared_file(name: str) -> dict[str, object]:
    """One of the four files that decide for every asset at once.

    Args:
        name: policy, classes, markets or build.

    Returns:
        Its leaves and the path it lives at.
    """
    return assets.shared(name)


@ROUTER.get("/api/asset/{symbol}/why")
def why(symbol: str, field: str, text: str) -> dict[str, str]:
    """The justification the window offers before a cost changes.

    Args:
        symbol: Asset name.
        field: Cost field.
        text: The figure about to be written.

    Returns:
        A line stamped today naming the figure it replaces, for the owner to finish.
    """
    return {"why": assets.why_for(symbol, field, text)}


@ROUTER.post("/api/assets/value")
def set_asset_value(change: ValueChange) -> dict[str, object]:
    """Write one value into one assets/ file, comments and all the rest untouched.

    Args:
        change: Which file, which path, and what was typed.

    Returns:
        What was written.
    """
    return assets.set_value(change.name, change.path, change.text, change.kind)


@ROUTER.post("/api/asset/{symbol}/cost")
def set_cost(symbol: str, change: CostChange) -> dict[str, object]:
    """Change a cost and its `why` in the same write.

    Args:
        symbol: Asset name.
        change: The field, the figure and the line that justifies it.

    Returns:
        The field as written.
    """
    return assets.set_cost(symbol, change.field, change.text, change.why)


@ROUTER.post("/api/assets/new")
def new_asset(new: NewAsset) -> dict[str, object]:
    """Add an instrument to the library, with every cost open.

    Args:
        new: Its identity and the three instrument facts read from SQX.

    Returns:
        The asset's row, or the reason the name was refused.
    """
    return assets.create({**new.model_dump(), "class": new.cls})


@ROUTER.post("/api/asset/{symbol}/retire")
def retire_asset(symbol: str) -> dict[str, object]:
    """Take an asset out of the library without losing its file.

    Args:
        symbol: Asset name.

    Returns:
        Where the file went.
    """
    return assets.assetwrite.retire(symbol)


@ROUTER.post("/api/asset/{symbol}/restore")
def restore_asset(symbol: str) -> dict[str, object]:
    """Put a retired asset back.

    Args:
        symbol: Asset name.

    Returns:
        Where the file went back to.
    """
    return assets.assetwrite.restore(symbol)


@ROUTER.post("/api/assets/market")
def set_market(change: MarketChange) -> dict[str, object]:
    """Replace one category of one asset's retest universe.

    Args:
        change: The main asset, the category and the complete list of feeds.

    Returns:
        The category as written.
    """
    return assets.assetwrite.set_market(change.symbol, change.category, change.feeds)
