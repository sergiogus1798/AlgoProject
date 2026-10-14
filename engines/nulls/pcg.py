"""numpy's PCG64 stream reproduced inside numba: the same numbers, generated where a kernel uses them."""

from typing import Any, cast

import numpy as np
from numba import njit

MULTIPLIER = 0x2360ED051FC65DA44385DF649FCCF645  # PCG_DEFAULT_MULTIPLIER_128, numpy's
WORD = (1 << 64) - 1
_M32, _S32, _S58, _S11 = (
    np.uint64(0xFFFFFFFF),
    np.uint64(32),
    np.uint64(58),
    np.uint64(11),
)
_U64, _U63 = np.uint64(64), np.uint64(63)
_UNIT = 1.0 / 9007199254740992.0


def jump(inc: int, steps: int) -> np.ndarray:
    """The affine map that moves a state `steps` draws ahead at once, for step().

    Args:
        inc: The stream's increment, `bit_generator.state["state"]["inc"]`.
        steps: How many 64-bit words to skip, >= 0.

    Returns:
        (multiplier high, low, increment high, low) as uint64; `jump(inc, 1)` is one draw.
    """
    mult, plus, by, add, full = 1, 0, MULTIPLIER, inc, (1 << 128) - 1
    while steps:
        if steps & 1:
            mult, plus = mult * by & full, (plus * by + add) & full
        add, by, steps = (by + 1) * add & full, by * by & full, steps >> 1
    return np.array([mult >> 64, mult & WORD, plus >> 64, plus & WORD], np.uint64)


def load(rng: np.random.Generator) -> tuple[np.ndarray, int]:
    """Where a numpy generator stands, in the form the compiled functions read and move.

    Args:
        rng: A Generator over PCG64 (what `np.random.default_rng` gives); anything else raises.

    Returns:
        (state, inc): `state` is (high word, low word, has_uint32, uinteger) as uint64 —
        the last two are the half word numpy keeps between calls on a 32-bit range.
    """
    seen = rng.bit_generator.state
    if seen["bit_generator"] != "PCG64":
        raise TypeError(f"pcg reproduces PCG64 only, not {seen['bit_generator']}")
    word = seen["state"]["state"]
    return np.array(
        [word >> 64, word & WORD, seen["has_uint32"], seen["uinteger"]], np.uint64
    ), seen["state"]["inc"]


def store(rng: np.random.Generator, state: np.ndarray) -> None:
    """Leave a numpy generator where the compiled draws left `state`, so its next call follows on.

    Args:
        rng: The generator load() read.
        state: What load() returned, after the kernel moved it.
    """
    seen = cast(dict[str, Any], rng.bit_generator.state)
    seen["state"]["state"] = (int(state[0]) << 64) | int(state[1])
    seen["has_uint32"], seen["uinteger"] = int(state[2]), int(state[3])
    rng.bit_generator.state = seen


@njit(inline="always")
def _high(a: np.uint64, b: np.uint64) -> np.uint64:
    """The high 64 bits of a 64 x 64 product (numba has no 128-bit integer)."""
    al, ah, bl, bh = a & _M32, a >> _S32, b & _M32, b >> _S32
    low, mid, dim, top = al * bl, al * bh, ah * bl, ah * bh
    return (
        top
        + (mid >> _S32)
        + (dim >> _S32)
        + (((low >> _S32) + (mid & _M32) + (dim & _M32)) >> _S32)
    )


@njit(inline="always")
def step(
    high: np.uint64, low: np.uint64, by: np.ndarray
) -> tuple[np.uint64, np.uint64]:
    """The state `by` draws further on: state * multiplier + increment, modulo 2**128.

    Args:
        high, low: The state's two words.
        by: What jump() returned.
    """
    carried = low * by[1]
    moved = carried + by[3]
    return (
        _high(low, by[1])
        + high * by[1]
        + low * by[0]
        + by[2]
        + np.uint64(moved < carried)
    ), moved


@njit(inline="always")
def word(high: np.uint64, low: np.uint64) -> np.uint64:
    """The 64 random bits numpy reads off a state (XSL-RR), taken AFTER the step that made it."""
    mixed, turn = high ^ low, high >> _S58
    return (mixed >> turn) | (mixed << ((_U64 - turn) & _U63))


@njit(inline="always")
def uniform(high: np.uint64, low: np.uint64) -> np.float64:
    """`rng.random()` of that state: its top 53 bits, in [0, 1)."""
    return np.float64(word(high, low) >> _S11) * _UNIT
