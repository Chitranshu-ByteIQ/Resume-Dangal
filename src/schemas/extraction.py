from pydantic import BaseModel, Field


class ResumeExtractionRequest(BaseModel):
    """
    Request used when extracting structured information
    from a resume.
    """

    candidate_id: str

    resume_file: str

    text: str = Field(
        ...,
        min_length=50,
        description="Extracted text from the resume",
    )


class JobExtractionRequest(BaseModel):
    """
    Request used when extracting structured information
    from a Job Description.
    """

    job_id: str

    text: str = Field(
        ...,
        min_length=20,
        description="Raw Job Description text",
    )


class ExtractionValidationResult(BaseModel):
    """
    Result of validating whether extracted content is
    suitable for further processing.
    """

    is_valid: bool

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str

    detected_type: str = Field(
        ...,
        description="Expected values: resume, job_description, unknown",
    )