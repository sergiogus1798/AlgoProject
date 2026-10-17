"""One-use proof that a launcher's confirmation was computed: a nonce bound to the plan it was shown with."""

import hashlib
import json
import secrets
import time

TTL_S = 600  # a confirmation left open longer is asked again
KEEP = 512  # preflights are polled; only the newest proofs are worth holding
ISSUED: dict[
    str, tuple[str, float]
] = {}  # nonce → (the plan's hash, when it was issued)
UNKNOWN = (
    "esta confirmación no existe o ya se usó: vuelve a pulsar el botón y confirma lo "
    "que te enseñe"
)
EXPIRED = "la confirmación caducó (más de 10 minutos): vuelve a pulsar y confirma"
CHANGED = "el plan cambió desde que lo viste: vuelve a pulsar y confirma el nuevo"


def digest(kind: str, plan: dict) -> str:
    """The hash a nonce is bound to: the launcher, what was asked and the sentence shown."""
    said = json.dumps([kind, plan], sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(said.encode()).hexdigest()


def issue(kind: str, plan: dict) -> str:
    """A fresh nonce for a preflight that answered ok.

    Args:
        kind: The launcher's label — a nonce of one launcher proves nothing to another.
        plan: What was asked plus the confirmation text returned: everything the owner reads
            before «Sí». Its counts and names are the state, so a state that moves changes it.

    Returns:
        The nonce the `run` route must receive back. Kept in memory: a daemon restarted
        forgets them all, and the window asks again.
    """
    now = time.monotonic()
    for old in [n for n, (_, when) in ISSUED.items() if now - when > TTL_S]:
        del ISSUED[old]
    while len(ISSUED) >= KEEP:
        del ISSUED[next(iter(ISSUED))]
    nonce = secrets.token_urlsafe(16)
    ISSUED[nonce] = (digest(kind, plan), now)
    return nonce


def refusal(kind: str, nonce: str, plan: dict) -> str | None:
    """Spend a nonce against the plan the preflight gives NOW.

    Args:
        kind: The launcher's label.
        nonce: What the `run` request carried.
        plan: The same dict `issue` took, rebuilt from the preflight re-run by `run`.

    Returns:
        None when the nonce is known, unused, younger than `TTL_S` and bound to this very
        plan; otherwise the sentence for the owner. The nonce is spent either way.
    """
    held = ISSUED.pop(nonce, None)
    if held is None:
        return UNKNOWN
    if time.monotonic() - held[1] > TTL_S:
        return EXPIRED
    return None if held[0] == digest(kind, plan) else CHANGED
