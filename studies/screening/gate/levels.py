"""The gate's levels in the order they run, and which level produces each fact."""

from studies.screening.gate import (level0, level1a, level1b_centred, level1b_data,
                                    level1b_onepass, level2, level3ab, level3c)

# (level, module) in running order. A module declares `FACTS`, the scorecard columns it
# produces, and `run(data, alive, cfg) -> DataFrame` indexed by identity. A rule of step "8"
# belongs to the level that produces its fact: criteria.yaml carries no level.
LEVELS = (("0", level0), ("1a", level1a), ("1b", level1b_centred), ("1b", level1b_onepass),
          ("1b", level1b_data), ("2", level2), ("3ab", level3ab), ("3c", level3c))
FACTS = ("cayo_nivel", "cayo_regla")     # where each strategy fell: the cascade's own columns


def facts() -> dict[str, str]:
    """Every scorecard column a level produces → the level that produces it."""
    return {fact: level for level, module in LEVELS for fact in module.FACTS}
