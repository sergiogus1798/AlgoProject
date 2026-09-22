"""The canonical form of a parameter tuple and its hash. Both ends of the factory use it."""

import hashlib

PREFIX = "param_"


def canonical(values: dict[str, float]) -> str:
    """One string that stands for a tuple, whatever produced it.

    Args:
        values: Parameter name to value.

    Returns:
        `name=value` pairs sorted by name and joined by `;`, the value formatted with
        `%g`. The format is type-free on purpose: the design holds 67.0 and the strategy
        file holds 67, and a hash that told those apart would report every variant as a
        mismatch between the plan and the disk.
    """
    return ";".join(f"{name}={values[name]:g}" for name in sorted(values))


def tuple_hash(values: dict[str, float]) -> str:
    """Identity of a tuple, for finding duplicates of fabrication.

    Args:
        values: Parameter name to value.

    Returns:
        First 16 hex characters of the SHA-256 of `canonical`. Short because it is read
        by a human comparing two tables, and 16 hex characters over five thousand rows
        collide with probability below 1e-9.
    """
    return hashlib.sha256(canonical(values).encode("utf-8")).hexdigest()[:16]


def columns(values: dict[str, float]) -> dict[str, float]:
    """A tuple as the manifest stores it.

    Args:
        values: Parameter name to value.

    Returns:
        The same mapping with every key prefixed `param_`, which is what contract C2
        calls the columns.
    """
    return {PREFIX + name: value for name, value in values.items()}


def from_columns(row: dict) -> dict[str, float]:
    """The tuple inside a manifest row.

    Args:
        row: A manifest row, with `param_` columns among the rest.

    Returns:
        Parameter name to value, the prefix stripped.
    """
    return {k[len(PREFIX):]: v for k, v in row.items() if k.startswith(PREFIX)}
