from pydantic import BaseModel, Field, field_validator


class JobDescription(BaseModel):
    """
    Structured representation of a Job Description
    extracted from raw JD text.
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier",
    )

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
        description="Required professional experience in years",
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Major responsibilities of the role",
    )

    education: list[str] = Field(
        default_factory=list,
        description="Required or preferred educational qualifications",
    )

    description: str | None = Field(
        default=None,
        description="Original or summarized job description",
    )

    @field_validator(
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "education",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value):
        """
        Normalize extracted list fields.
        """

        if value is None:
            return []

        if isinstance(value, str):
            return [value.strip()] if value.strip() else []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]