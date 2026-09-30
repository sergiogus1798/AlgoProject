"""Temporary, one-run overrides of the build doctrine — never a `_build.yaml` edit."""

# Unset by default, so `assetdata.doctrine()` is unchanged until a session sets one for the
# one process that stages a project's tasks (owner, 2026-09-29 §2): a run-wide precision or
# MC Retest count applied to ONE project, restored by simply not setting the variable again.
PRECISION = "ALGO_PRECISION_OVERRIDE"
MC_SIMULATIONS = "ALGO_MC_SIMULATIONS"


def replace(node: object, key: str, value: int) -> object:
    """Every leaf named `key` inside a nested structure, a bare int or a `{sub: int}` pair.

    Args:
        node: A dict, a list, or a scalar — the doctrine's tree, walked recursively.
        key: The leaf's name, e.g. "precision" (a task's own int, or `{build, default}`)
            or "simulations" (the shared default, and each MC Retest task's own).
        value: What every occurrence becomes.

    Returns:
        A new tree; `node` itself is never mutated.
    """
    if isinstance(node, dict):
        return {k: ({sub: value for sub in v} if k == key and isinstance(v, dict) else
                    value if k == key else replace(v, key, value))
                for k, v in node.items()}
    if isinstance(node, list):
        return [replace(v, key, value) for v in node]
    return node
