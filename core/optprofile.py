"""Read the Sys. Param Permutation profile SQX stores inside a .sqx, without SQX running."""

import json
import struct
import zipfile
from collections.abc import Callable
from pathlib import Path

MEMBER = "optimizationProfile.bin"
COLUMNS = {int(k): v for k, v in
           json.loads((Path(__file__).parent / "optprofile_columns.json").read_text(encoding="utf-8")).items()}
STATS = json.loads((Path(__file__).parent / "sqxstats_columns.json").read_text(encoding="utf-8"))
ARRAY = {1: "i", 2: "l", 3: "f"}


def _payload(path: Path) -> bytes:
    """Strip the Java block-data framing off the stored member.

    Args:
        path: A .sqx file that carries an optimization profile.

    Returns:
        The concatenated payload. The stream holds no objects, only 0x7a blocks with a
        4-byte length and 0x77 blocks with a 1-byte one, exactly like dailyEquity.bin.
    """
    raw = zipfile.ZipFile(path).read(MEMBER)
    i, buf = 4, bytearray()
    while i < len(raw):
        if raw[i] == 0x7A:
            size = struct.unpack(">i", raw[i + 1:i + 5])[0]
            buf += raw[i + 5:i + 5 + size]
            i += 5 + size
        elif raw[i] == 0x77:
            size = raw[i + 1]
            buf += raw[i + 2:i + 2 + size]
            i += 2 + size
        else:
            break
    return bytes(buf)


class _Reader:
    """A cursor over the payload, one Java ObjectInput primitive per method."""

    def __init__(self, data: bytes) -> None:
        """Args:
            data: The unframed payload to walk.
        """
        self.data, self.at = data, 0

    def take(self, count: int) -> bytes:
        """Advance over count bytes.

        Args:
            count: How many bytes to consume.

        Returns:
            The bytes consumed.
        """
        self.at += count
        return self.data[self.at - count:self.at]

    def int32(self) -> int:
        """Returns: The next big-endian signed 4-byte integer."""
        return struct.unpack(">i", self.take(4))[0]

    def double(self) -> float:
        """Returns: The next big-endian 8-byte float."""
        return struct.unpack(">d", self.take(8))[0]

    def boolean(self) -> bool:
        """Returns: The next single byte read as a flag."""
        return self.take(1)[0] != 0

    def text(self) -> str:
        """Returns: The next writeUTF string — a 2-byte length then UTF-8."""
        return self.take(struct.unpack(">H", self.take(2))[0]).decode("utf8")

    def sq_text(self) -> str:
        """Returns: The next `SQUtils.writeUTF` string — a marker byte, then a 2-byte
        length when the marker is 1 and a 4-byte one otherwise, then UTF-8."""
        wide = self.take(1)[0] != 1
        size = struct.unpack(">i" if wide else ">H", self.take(4 if wide else 2))[0]
        return self.take(size).decode("utf8")

    def stats(self) -> dict:
        """Read one `SQStats` blob.

        Returns:
            Metric name to value. Built-in metrics arrive as an array index and are named
            through the calibrated STATS table; the rest carry their own name. Format 1
            stores the float array as doubles, format 2 as floats.
        """
        wide = self.int32() == 1
        out = {}
        for _ in range(self.int32()):
            kind = struct.unpack(">b", self.take(1))[0]
            if kind < 100:
                slot = f"{ARRAY[kind]}:{self.take(1)[0]}"
                key = STATS.get(slot, f"stat:{slot}")
            else:
                key = self.sq_text()
            if kind in (1, 101):
                out[key] = self.int32()
            elif kind in (2, 102):
                out[key] = struct.unpack(">q", self.take(8))[0]
            else:
                out[key] = self.double() if wide else struct.unpack(">f", self.take(4))[0]
        return out

    def result(self) -> dict:
        """Returns: One permutation as `params` (SQX's `Name=value,` string) and `stats`."""
        self.int32()
        params = self.sq_text()
        return {"params": params, "stats": self.stats()}

    def keyed(self, value: Callable[[], object]) -> dict:
        """Read a fastutil int-keyed map, naming each key by its databank column.

        Args:
            value: Bound method reading one entry's value.

        Returns:
            Metric name to value. SQX keys these maps by a hash of the column class name
            that no longer resolves, so the names come from the calibrated COLUMNS table;
            a key it does not hold is reported as id:<key>.
        """
        return {COLUMNS.get(k, f"id:{k}"): v
                for k, v in ((self.int32(), value()) for _ in range(self.int32()))}


def read(path: Path) -> dict:
    """Everything one strategy's SPP cross-check left behind.

    Args:
        path: A .sqx file holding an optimization profile.

    Returns:
        Keys `permutations`, `profitable`, `losing`, `zero`, `profitable_pct`, `avg_profit`,
        `top_profit`, `stdev`, `uniform_changes`, `params` (the permuted parameter names),
        `medians` and `orig` (metric name to value), `charts` (metric name to the stored
        histogram) and `distribution` (the profit distribution chart).

        `permutation_results` says whether SQX kept the run permutation by permutation —
        it does only while "Don't store data for 3D charts in Optimization profile" is
        off. When it did, `original` and `results` hold one `{params, stats}` per run.
        A permutation carries its parameter string and its statistics and nothing else:
        `SQStats.deserialize` reads six numeric record types and never an object, so no
        order list is stored anywhere and permutation trades cannot be recovered.
    """
    r = _Reader(_payload(path))
    r.int32()
    out = {"permutation_results": r.boolean()}
    if out["permutation_results"]:
        out["original"] = r.result() if r.boolean() else None
        out["results"] = [r.result() for _ in range(r.int32())]
    out["medians"] = r.keyed(r.double)
    out["orig"] = r.keyed(r.double)
    out["charts"] = r.keyed(lambda: json.loads(r.text()))
    out["params"] = json.loads(r.text())
    json.loads(r.text())
    out |= dict(zip(("permutations", "profitable", "losing", "last_count", "zero"),
                    (r.int32() for _ in range(5))))
    out |= dict(zip(("profitable_pct", "avg_profit", "uniform_changes", "top_profit",
                     "stdev", "stdev_computed"), (r.double() for _ in range(6))))
    out["distribution"] = json.loads(r.text())
    return out


def histogram(chart: dict) -> list[dict]:
    """Flatten one stored metric chart into its bins.

    Args:
        chart: One entry of `read()["charts"]`.

    Returns:
        One dict per bin with `bin`, `edge` (the bin's lower label, blank where SQX left it
        out), `frequency`, and the flags `is_median` and `is_orig` marking the bins SQX
        highlights. The frequencies are the permutation counts; the median and orig series
        carry only the bar height, so they are reduced to flags.
    """
    sets = {d["label"]: d["data"] for d in chart["chart"]["data"]["datasets"]}
    labels = chart["chart"]["data"]["labels"]
    return [{"bin": i, "edge": labels[i], "frequency": int(float(sets["Frequency"][i])),
             "is_median": float(sets["Median"][i]) > 0,
             "is_orig": float(sets["Orig. value"][i]) > 0}
            for i in range(len(labels))]
