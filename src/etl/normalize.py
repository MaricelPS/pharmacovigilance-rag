"""Normalization utilities for FAERS drug names and demographics."""
import re
import polars as pl


def normalize_drug_name(name: str | None) -> str | None:
    """Lowercase, strip, and remove common noise from FAERS drug names.

    FAERS drug names come as free text with inconsistent capitalization,
    trailing dosage info, formulation suffixes, etc. Example transformations:
        'OZEMPIC 1 MG'       -> 'ozempic'
        'Semaglutide inj.'   -> 'semaglutide'
        'WEGOVY (SEMAGLUTIDE)' -> 'wegovy'
    """
    if name is None:
        return None
    s = str(name).lower().strip()
    # Remove parenthetical content
    s = re.sub(r"\([^)]*\)", "", s)
    # Remove dosage patterns like '1 mg', '0.5mg', '10 units', etc.
    s = re.sub(r"\d+(\.\d+)?\s*(mg|mcg|g|ml|units?|iu|%)\b", "", s)
    # Remove common formulation suffixes
    s = re.sub(r"\b(injection|inj|tablet|tab|capsule|cap|solution|sol|"
               r"suspension|susp|cream|ointment|patch|xr|er|sr|cr)\b", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def build_glp1_matcher(glp1_dict: list[dict]) -> dict[str, str]:
    """Build a lookup from any name variant (active or brand) to active ingredient.

    Returns a dict where keys are normalized names and values are the canonical
    active ingredient.
    """
    matcher = {}
    for row in glp1_dict:
        ai = row["active_ingredient"]
        matcher[ai] = ai
        for brand in row["brand_names"]:
            matcher[brand.lower()] = ai
    return matcher


def match_glp1(drug_name: str | None, matcher: dict[str, str]) -> str | None:
    """Return the canonical GLP-1 active ingredient if the drug matches, else None.

    Matches by containment: any known variant appearing anywhere in the
    normalized name counts as a hit. This catches combinations like
    'insulin glargine / lixisenatide' or 'ozempic 1mg pen'.
    """
    normalized = normalize_drug_name(drug_name)
    if normalized is None:
        return None
    for variant, active in matcher.items():
        if variant in normalized:
            return active
    return None


def parse_age_to_years(age: float | None, age_unit: str | None) -> float | None:
    """Convert FAERS age + age_cod to years.

    FAERS age_cod values: DEC (decade), YR (year), MON (month), WK (week),
    DY (day), HR (hour). Missing units are treated as years.
    """
    if age is None:
        return None
    unit = (age_unit or "YR").upper()
    factors = {"DEC": 10.0, "YR": 1.0, "MON": 1 / 12, "WK": 1 / 52,
               "DY": 1 / 365, "HR": 1 / 8760}
    factor = factors.get(unit, 1.0)
    return float(age) * factor


def add_glp1_flag(drug_df: pl.DataFrame, matcher: dict[str, str]) -> pl.DataFrame:
    """Add a `glp1_active_ingredient` column to the drug DataFrame."""
    # Build a mapping applied via python function (small drug universe is fine)
    def _match(row):
        return (
                match_glp1(row.get("drugname"), matcher)
                or match_glp1(row.get("prod_ai"), matcher)
        )

    return drug_df.with_columns(
        pl.struct(["drugname", "prod_ai"])
        .map_elements(_match, return_dtype=pl.Utf8)
        .alias("glp1_active_ingredient")
    )