from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """
    Structured representation of a Job Description.

    This schema is stored as JSON in S3 and later
    used by the ranking engine.
    """

    job_id: str

    title: str = Field(
        ...,
        min_length=1,
        description="Job title",
    )

    required_skills: list[str] = Field(
        default_factory=list,
        description="Mandatory technical skills",
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Preferred but non-mandatory skills",
    )

    experience_required: float | None = Field(
        default=None,
        ge=0,
        description="Required experience in years",
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities",
    )

    education: list[str] = Field(
        default_factory=list,
        description="Required or preferred education",
    )

    description: str | None = Field(
        default=None,
        description="Original or summarized job description",
    )