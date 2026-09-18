"""The five family sections of a strategy's page: its tables, its figures and its verdict
line. Split one file per family; common.py holds only what they share."""

from strategies.monteCarlo.render.families.a_order import family_a
from strategies.monteCarlo.render.families.b_composition import family_b
from strategies.monteCarlo.render.families.c_execution import family_c
from strategies.monteCarlo.render.families.common import LABELS, MODELS_ES, MONEY, SHARE, fmt
from strategies.monteCarlo.render.families.d_regime import family_d
from strategies.monteCarlo.render.families.e_significance import family_e

__all__ = ["family_a", "family_b", "family_c", "family_d", "family_e", "fmt",
          "LABELS", "MODELS_ES", "MONEY", "SHARE"]
