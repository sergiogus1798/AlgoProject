"""The five family sections of a strategy's page: its tables, its figures and its verdict
line. Split one file per family; common.py holds only what they share."""

from strategies.monteCarlo.familypage.a import family_a
from strategies.monteCarlo.familypage.b import family_b
from strategies.monteCarlo.familypage.c import family_c
from strategies.monteCarlo.familypage.common import LABELS, MODELS_ES, MONEY, SHARE, fmt
from strategies.monteCarlo.familypage.d import family_d
from strategies.monteCarlo.familypage.e import family_e

__all__ = ["family_a", "family_b", "family_c", "family_d", "family_e", "fmt",
          "LABELS", "MODELS_ES", "MONEY", "SHARE"]
