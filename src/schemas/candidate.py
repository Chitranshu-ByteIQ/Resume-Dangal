from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """
    Structured representation of a candidate.

    This schema is stored as JSON in S3 and later
    consumed by the ranking engine.
    """

    candidate_id: str

    name: str = Field(
        ...,
        min_length=1,
        description="Candidate's full name",
    )

    suitable_title: str | None = Field(
        default=None,
        description="Most suitable professional title",
    )

    experience_years: float | None = Field(
        default=None,
        ge=0,
        description="Total relevant experience in years",
    )

    tech_stack: list[str] = Field(
        default_factory=list,
        description="Technical skills and technologies",
    )

    projects: list[str] = Field(
        default_factory=list,
        description="Relevant projects",
    )

    profile_summary: str | None = Field(
        default=None,
        description="Short professional profile summary",
    )

    resume_file: str = Field(
        ...,
        description="S3 key of the original resume",
    )