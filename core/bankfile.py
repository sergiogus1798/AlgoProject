"""Read an `.abk`: one databank as the AlgoBank snippet wrote it from SQX's memory.

THE FORMAT, version 1 — the one spec `AlgoBank.java` and the writer in
`tests/test_perf66_algobank.py` follow. Little-endian throughout, no alignment padding.

    0         "ALGOBANK" | u4 version = 1 | u4 data (0 = main result only, 1 = every result)
    16        ten sections, back to back, in the order of the table below
    size-204  trailer: 10 x (u8 offset, u8 length), in the same order
              | u4 n strategies | u4 K | u8 n_orders | u8 written_ms | u8 size | u4 crc32 | "KNABOGLA"

    section  record                                                                    bytes
    orders   u4 strategy, i4 ticket, i8 open_ms, i8 close_ms, f4 open, f4 close,          64
             f4 size, f4 pl, f4 balance, f4 mae, f4 mfe, u2 sym, u2 res, u2 type,
             u2 sample, u2 close_type, u1 flags, u1 zero
    equity   i4 day, f4 value                                                              8
    stats    u4 strategy, u4 result, i1 sample, 3 zero bytes, K x f8                  12 + 8K
    xml      the strategies' XML, UTF-8, concatenated                                      -
    index    u4 name, u4 main, u4 symbol, u4 tf, u4 filter, i4 problems,                  32
             u4 n_orders, u4 xml_len
    eqruns   u4 strategy, u4 result, u4 n                                                 12
    symdec   u4 sym, i4 decimals                                                           8
    keys     u4                                                                            4
    labels   string table                                                                  -
    strings  string table                                                                  -

- `strategy` is a row of `index`; `index` is in databank order and `orders` and `xml` follow it,
  each strategy's orders contiguous and in SQX's own order. `n_orders` counts the records
  written: balance orders are never written, an unfilled pending order is, with `flags` bit 0.
- A string table is u4 count, u4 offsets[count + 1], then the UTF-8 bytes; id 0 is "". The five
  u2 of an order index `labels` (under 65,536 entries); `symdec.sym` does too; every other id
  indexes `strings`.
- `res` is the name of the result the order belongs to. `type`, `sample` and `close_type` are
  SQX's own trade-list texts ("Buy", "IST", "Exit Signal"). **One that is "" or "N/A" is a code
  SQX had no label for, and it rejects the whole file** (owner, 2026-10-12): the snippet raises
  before the file gets its name, and `load` refuses it again.
- `mae` carries the trade list's sign (zero or negative). `symdec.decimals` is the symbol's price
  decimals as SQX knows them, -1 when it does not.
- `equity` holds one run per `eqruns` row, in that order: `n` points, `day` = floor(ms / 86,400,000).
- `stats`: one row per (strategy, result, sample type) SQX holds, direction Both, P/L in money.
  `keys` names its K columns: each string is "name<TAB>type", type `i`, `l` or `f` — what the
  value is in SQX; all travel as f8, which holds a float32 and an int32 exactly. NaN means «key absent»:
  a statistic SQX really stores as NaN is the same bits.
- `crc32` covers bytes [0, size - 12). The snippet writes `<name>.abk.tmp` and renames it, so a
  file under its final name is whole; `size` and the closing magic say so again.
"""

import zlib
from pathlib import Path

import numpy as np
import pandas as pd

MAGIC, END, VERSION, TRAILER = b"ALGOBANK", b"KNABOGLA", 1, 204
ORDER = np.dtype([("strategy", "<u4"), ("ticket", "<i4"), ("open_ms", "<i8"), ("close_ms", "<i8"),
                  ("open", "<f4"), ("close", "<f4"), ("size", "<f4"), ("pl", "<f4"),
                  ("balance", "<f4"), ("mae", "<f4"), ("mfe", "<f4"), ("sym", "<u2"), ("res", "<u2"),
                  ("type", "<u2"), ("sample", "<u2"), ("close_type", "<u2"), ("flags", "u1"),
                  ("_", "u1")])
EQ = np.dtype([("day", "<i4"), ("v", "<f4")])
INDEX = np.dtype([(c, "<u4") for c in ("name", "main", "symbol", "tf", "filter")]
                 + [("problems", "<i4"), ("n_orders", "<u4"), ("xml_len", "<u4")])
EQRUN = np.dtype([("strategy", "<u4"), ("res", "<u4"), ("n", "<u4")])
SYMDEC = np.dtype([("sym", "<u4"), ("dec", "<i4")])
SECTIONS = ("orders", "equity", "stats", "xml", "index", "eqruns", "symdec", "keys", "labels",
            "strings")
UNLABELLED = ("", "N/A")
PENDING = 1                                  # `flags` bit 0: an order that never filled
CODED = ("type", "sample", "close_type")     # the three whose label must exist


class Unreadable(Exception):
    """The file is not a whole, valid `.abk`: the caller falls to its next source."""


def stat(k: int) -> np.dtype:
    """The record of the `stats` section for K keys."""
    return np.dtype([("strategy", "<u4"), ("res", "<u4"), ("sample", "i1"), ("_", "V3"),
                     ("v", "<f8", (k,))])


def half_up(x: np.ndarray, decimals: int | np.ndarray) -> np.ndarray:
    """Round float32 values the way SQX prints them: halves away from zero.

    🔬 2026-10-12: numpy's round-half-even left 48,091 balances of 4.54 M trades off by 0.01
    against orderstocsv; this one, none.
    """
    scale = 10.0 ** np.asarray(decimals, dtype="f8")
    x = np.asarray(x, dtype="f8")
    return np.sign(x) * np.floor(np.abs(x) * scale + 0.5) / scale


def _table(raw: np.ndarray, what: str) -> np.ndarray:
    """A string table as an object array, id -> text."""
    n = int(raw[:4].view("<u4")[0]) if len(raw) >= 8 else -1
    if n < 1 or len(raw) < 8 + 4 * n:
        raise Unreadable(f"la tabla de cadenas «{what}» no cabe en su sección")
    off = raw[4:8 + 4 * n].view("<u4")
    text = bytes(raw[8 + 4 * n:])
    if off[-1] != len(text) or (np.diff(off.astype("i8")) < 0).any():
        raise Unreadable(f"la tabla de cadenas «{what}» no cuadra con su sección")
    try:
        return np.array([text[a:b].decode("utf-8") for a, b in zip(off[:-1], off[1:])], dtype=object)
    except UnicodeDecodeError as err:
        raise Unreadable(f"la tabla de cadenas «{what}» no es UTF-8: {err}") from err


def load(path: Path, check: bool = False) -> dict:
    """Open one `.abk` and validate it.

    Args:
        path: The file.
        check: Also verify the CRC32, ~1 s per GB: for tests and for a file that was copied.
            The rename already protects a reader from a half-written one.

    Returns:
        The ten sections under their names — `orders`, `equity`, `stats`, `index`, `eqruns`
        and `symdec` as structured arrays mapped from the file, `xml` as bytes, `keys` as
        [(name, type)], `labels` and `strings` as object arrays — plus `data` ("main" or
        "all"), `names` (strategy names in databank order) and `written_ms`.

    Raises:
        Unreadable: Truncated, not version 1, sizes that do not add up, a wrong CRC, or an
            order whose type, sample type or close type has no label.
    """
    path = Path(path)
    size = path.stat().st_size
    if size < 16 + TRAILER:
        raise Unreadable(f"{path}: truncado, {size} bytes no llegan a cabecera y cola")
    m = np.memmap(path, np.uint8, "r")
    if bytes(m[:8]) != MAGIC or int(m[8:12].view("<u4")[0]) != VERSION:
        raise Unreadable(f"{path}: no es un .abk versión {VERSION}")
    t = np.array(m[-TRAILER:])
    told = int(t[184:192].view("<u8")[0])
    if bytes(t[-8:]) != END or told != size:
        raise Unreadable(f"{path}: truncado o a medias — mide {size} bytes y su cola "
                         f"{'no está' if bytes(t[-8:]) != END else f'dice {told}'}")
    if check and zlib.crc32(m[:-12]) != int(t[192:196].view("<u4")[0]):
        raise Unreadable(f"{path}: el CRC no cuadra, el contenido cambió después de escribirse")
    n, k = (int(v) for v in t[160:168].view("<u4"))
    kinds = dict(orders=ORDER, equity=EQ, stats=stat(k), xml=np.dtype("u1"), index=INDEX,
                 eqruns=EQRUN, symdec=SYMDEC, keys=np.dtype("<u4"), labels=np.dtype("u1"),
                 strings=np.dtype("u1"))
    got = {}
    for name, (at, length) in zip(SECTIONS, t[:160].view("<u8").reshape(10, 2).tolist()):
        if at < 16 or at + length > size - TRAILER or length % kinds[name].itemsize:
            raise Unreadable(f"{path}: la sección «{name}» ({at}+{length}) no cabe en el fichero")
        got[name] = m[at:at + length].view(kinds[name])
    labels, strings = _table(got["labels"], "labels"), _table(got["strings"], "strings")
    o, index, runs = got["orders"], got["index"], got["eqruns"]
    if len(index) != n or (len(o) and int(o["strategy"].max()) >= n):
        raise Unreadable(f"{path}: sus secciones no cuadran entre sí (estrategias)")
    if (len(got["keys"]) != k or len(o) != int(t[168:176].view("<u8")[0])
            or (np.bincount(o["strategy"], minlength=n) != index["n_orders"]).any()
            or (np.diff(o["strategy"].astype("i8")) < 0).any()
            or int(index["xml_len"].sum(dtype="u8")) != len(got["xml"])
            or int(runs["n"].sum(dtype="u8")) != len(got["equity"])
            or any(len(a) and int(a.max()) >= n for a in (runs["strategy"], got["stats"]["strategy"]))
            or any(len(a) and int(a.max()) >= len(strings)
                   for a in (got["keys"], runs["res"], got["stats"]["res"],
                             *(index[c] for c in ("name", "main", "symbol", "tf", "filter"))))
            or any(len(o) and int(o[c].max()) >= len(labels) for c in ("sym", "res") + CODED)
            or (len(got["symdec"]) and int(got["symdec"]["sym"].max()) >= len(labels))):
        raise Unreadable(f"{path}: sus secciones no cuadran entre sí")
    blank = np.flatnonzero(np.isin(labels, UNLABELLED))
    for c in CODED:
        if np.isin(np.unique(o[c]), blank).any():
            raise Unreadable(f"{path}: hay órdenes con «{c}» sin etiqueta — fichero rechazado")
    got.update(labels=labels, strings=strings, xml=got["xml"], names=strings[index["name"]],
               keys=[tuple(strings[i].split("\t")) for i in got["keys"]],
               data="all" if int(m[12:16].view("<u4")[0]) else "main",
               written_ms=int(t[176:184].view("<u8")[0]))
    return got


def trades(bank: dict, per_market: bool = False) -> pd.DataFrame:
    """Every filled trade of the databank: the frame `core.tradepack.pack` writes from the CSVs.

    Args:
        bank: What `load` returned.
        per_market: True for a `data == "all"` file: `Symbol` and `block` are kept, `block`
            by the k-th-ticket rule of `core.tradestore.blocks_of`.

    Returns:
        `core.tradestore.KEEP`, then `Symbol` and `block`, then `strategy`; strategies in the
        order of their file names (`tradepack.pack`'s), each one's rows in SQX's own. Prices are rounded half-up to their symbol's decimals, money to 2. `Ticket`
        is there only when some strategy's row order does not carry it
        (`core.tradestore.ordered`), NaN for the strategies that did not need it — placed
        and typed as `pack` does: before `strategy` when the first strategy kept it, int64
        when all did.

    Raises:
        Unreadable: A traded symbol SQX gave no decimals for.
    """
    o = bank["orders"]
    o = o[o["flags"] & PENDING == 0]
    labels, names = bank["labels"], bank["names"]
    # Sorted on read (owner, 2026-10-13): SQX's memory holds a databank in its own order, the
    # trade library in the order of the strategies' file names (🔬 same day, 50 + 50 strategies).
    first = sorted(range(len(names)), key=lambda i: names[i] + ".csv")
    rank = np.empty(len(names), "i8")
    rank[first] = np.arange(len(names))
    o = o[np.argsort(rank[o["strategy"]], kind="stable")]
    known = np.full(len(labels), -1)
    known[bank["symdec"]["sym"]] = bank["symdec"]["dec"]
    dec = known[o["sym"]]
    if (dec < 0).any():
        raise Unreadable(f"símbolos sin decimales en SQX: {sorted(set(labels[o['sym'][dec < 0]]))}")

    def cat(ids: np.ndarray, of: np.ndarray = labels) -> pd.Categorical:
        """The labels of `ids` as a categorical over just the labels used."""
        return pd.Categorical(of[ids], categories=sorted(set(of[np.unique(ids)])))

    def when(ms: np.ndarray) -> np.ndarray:
        """Epoch milliseconds as datetime64[ns], whole seconds."""
        return (ms // 1000 * 1000).astype("datetime64[ms]").astype("datetime64[ns]")

    f = pd.DataFrame({
        "Type": cat(o["type"]), "Open time": when(o["open_ms"]),
        "Open price": half_up(o["open"], dec), "Size": half_up(o["size"], 2),
        "Close time": when(o["close_ms"]), "Close price": half_up(o["close"], dec),
        "Profit/Loss": half_up(o["pl"], 2), "Balance": half_up(o["balance"], 2),
        "Sample type": cat(o["sample"]), "Close type": cat(o["close_type"]),
        "MAE ($)": half_up(o["mae"], 2), "MFE ($)": half_up(o["mfe"], 2)})
    if per_market:
        f["Symbol"] = cat(o["sym"])
        f["block"] = pd.DataFrame({"s": o["strategy"], "t": o["ticket"]}).groupby(["s", "t"]).cumcount()
    same = o["strategy"][1:] == o["strategy"][:-1]
    op, cl = o["open_ms"] // 1000, o["close_ms"] // 1000      # whole seconds, as the CSVs `tradepack.pack` reads
    torn = same & ((op[1:] <= op[:-1]) | (op[1:] < cl[:-1]))
    kept = np.unique(o["strategy"][1:][torn])
    if len(kept) and len(kept) == len(names):
        f["Ticket"] = o["ticket"].astype("int64")
    elif len(kept):
        f["Ticket"] = np.where(np.isin(o["strategy"], kept), o["ticket"], np.nan)
    f["strategy"] = cat(o["strategy"], names)
    if len(kept) and first[0] not in kept:
        f["Ticket"] = f.pop("Ticket")
    return f
