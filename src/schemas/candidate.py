from pydantic import BaseModel, Field, field_validator


class CandidateProfile(BaseModel):
    """
    Structured representation of a candidate extracted from a resume.
    """

    candidate_id: str = Field(
        ...,
        description="Unique candidate identifier",
    )

    name: str = Field(
        ...,
        min_length=1,
        description="Candidate's full name",
    )

    email: str | None = Field(
        default=None,
        description="Candidate's email address",
    )

    phone: str | None = Field(
        default=None,
        description="Candidate's phone number",
    )

    location: str | None = Field(
        default=None,
        description="Candidate's location",
    )

    suitable_title: str | None = Field(
        default=None,
        description="Most suitable professional title",
    )

    experience_years: float | None = Field(
        default=None,
        ge=0,
        description="Total relevant professional experience",
    )

    education: list[str] = Field(
        default_factory=list,
        description="Educational qualifications",
    )

    tech_stack: list[str] = Field(
        default_factory=list,
        description="Technical skills and technologies",
    )

    soft_skills: list[str] = Field(
        default_factory=list,
        description="Soft skills",
    )

    projects: list[str] = Field(
        default_factory=list,
        description="Relevant projects",
    )

    work_experience: list[str] = Field(
        default_factory=list,
        description="Previous work experience",
    )

    certifications: list[str] = Field(
        default_factory=list,
        description="Professional certifications",
    )

    profile_summary: str | None = Field(
        default=None,
        description="Professional profile summary",
    )

    resume_file: str = Field(
        ...,
        description="S3 key of the original resume",
    )

    @field_validator(
        "education",
        "tech_stack",
        "soft_skills",
        "projects",
        "work_experience",
        "certifications",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value):
        """
        Ensure list fields are always represented as clean lists.
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