"""A study's English or lowercase verdict words, in Spanish for the databank table."""

# The verdict words a study writes in English or lowercase, as the databank table shows them
# (the raw word stays the sort key). Spanish verdicts a study already writes are not here.
VERDICT_WORDS = {
    "pass": "Pasa", "fail": "Falla", "watch": "Vigilar", "none": "Sin juicio",
    "fails": "Falla", "survives": "Sobrevive", "inherited": "Heredada",
    "unusable": "No utilizable", "silent": "Silenciosa", "control_failed": "Control fallido",
    "no_data": "Sin datos", "FAIL": "Falla", "PASS": "Pasa", "INCONCLUSIVE": "No concluyente",
    "Blind ρ": "ρ ciega", "Perverse ρ": "ρ perversa", "Predicts ρ": "ρ predice",
    "True": "Sí", "False": "No",
    "blind": "Ciega", "predicts": "Predice", "perverse": "Perversa", "unjudged": "Sin juicio",
}


def verdict_word(value: object) -> object:
    """A study's verdict word in Spanish, sentence case; any other value comes back unchanged.

    A word with no entry that is a raw id — snake_case, or all lower case — is shown with
    spaces and a capital: «beneficio_no_robusto» → «Beneficio no robusto».
    """
    if not isinstance(value, str):
        return value
    if value in VERDICT_WORDS:
        return VERDICT_WORDS[value]
    if "_" in value or value.islower():
        text = value.replace("_", " ")
        return text[:1].upper() + text[1:]
    return value
