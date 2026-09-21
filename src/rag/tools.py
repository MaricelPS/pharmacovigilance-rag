"""Tool schemas exposed to the LLM agent for pharmacovigilance queries.

Each tool is defined as a Pydantic model whose JSON schema is passed to
Claude via the `tools` parameter. The agent calls a tool by name with
structured arguments; we execute it and return the result as tool output.
"""
from pydantic import BaseModel, Field


class SemanticEventSearch(BaseModel):
    """Translate a natural-language description of an adverse event into
    the MedDRA Preferred Terms that best match it.

    Use this FIRST when the user mentions an event in lay terms
    ('liver problems', 'stomach pain', 'vision issues') so that downstream
    tools can filter by canonical PTs.
    """
    query: str = Field(..., description="Natural-language event description")
    top_k: int = Field(10, description="Maximum PTs to return", ge=1, le=30)


class DetectSignals(BaseModel):
    """Scan every event reported with a given drug and compute
    disproportionality metrics (PRR, ROR with 95% CI, Information Component).

    Returns events that meet EMA or BCPNN signal criteria, ranked by IC.
    Use for questions like: 'What safety signals appear with semaglutide?'
    """
    drug_key: str = Field(
        ..., description="Normalized active ingredient, e.g. 'semaglutide'"
    )
    min_cases: int = Field(
        10, description="Minimum co-occurring cases to consider", ge=3
    )
    top_n: int = Field(
        20, description="Number of top signals to return", ge=1, le=50
    )


class QueryCohortEvents(BaseModel):
    """Query the GLP-1 cohort for adverse events, with optional demographic
    and outcome filters.

    Use for questions like: 'Adverse events reported for tirzepatide in
    women over 60', or 'Serious outcomes for semaglutide'.
    """
    drug_key: str | None = Field(
        None, description="Active ingredient filter (any GLP-1 if None)"
    )
    event_pts: list[str] | None = Field(
        None, description="Restrict to these MedDRA PTs (from semantic search)"
    )
    age_min: float | None = Field(None, description="Minimum age in years")
    age_max: float | None = Field(None, description="Maximum age in years")
    sex: str | None = Field(None, description="'M' or 'F'")
    serious_only: bool = Field(
        False, description="Restrict to reports with a serious outcome"
    )
    top_n: int = Field(20, description="Top N events to return", ge=1, le=50)


class CompareDrugs(BaseModel):
    """Compare disproportionality metrics for a set of drugs across the
    same events.

    Use for questions like: 'Compare pancreatitis signal between
    semaglutide, liraglutide and tirzepatide'.
    """
    drug_keys: list[str] = Field(
        ..., description="Active ingredients to compare", min_length=2, max_length=6
    )
    event_pts: list[str] = Field(
        ..., description="MedDRA PTs to compare across drugs", min_length=1, max_length=15
    )


TOOL_SCHEMAS = [
    {
        "name": "semantic_event_search",
        "description": SemanticEventSearch.__doc__,
        "input_schema": SemanticEventSearch.model_json_schema(),
    },
    {
        "name": "detect_signals",
        "description": DetectSignals.__doc__,
        "input_schema": DetectSignals.model_json_schema(),
    },
    {
        "name": "query_cohort_events",
        "description": QueryCohortEvents.__doc__,
        "input_schema": QueryCohortEvents.model_json_schema(),
    },
    {
        "name": "compare_drugs",
        "description": CompareDrugs.__doc__,
        "input_schema": CompareDrugs.model_json_schema(),
    },
]