import uuid

from src.schemas.extraction import (
    JobExtractionRequest,
)
from src.schemas.job import JobDescription
from src.services.llm_service import LLMService
from src.extraction.validator import DocumentValidator


class JobDescriptionExtractor:
    """
    Extract structured JobDescription from raw JD text.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
        validator: DocumentValidator | None = None,
    ):
        self.llm_service = (
            llm_service
            or LLMService()
        )

        self.validator = (
            validator
            or DocumentValidator()
        )

    def extract(
        self,
        text: str,
        job_id: str | None = None,
    ) -> JobDescription:
        """
        Convert raw Job Description text into a
        validated JobDescription object.
        """

        if not job_id:
            job_id = str(uuid.uuid4())

        # ==========================================
        # STEP 1 — Deterministic validation
        # ==========================================

        validation = (
            self.validator.validate_jd_text(text)
        )

        if not validation.is_valid:
            raise ValueError(
                f"Invalid job description: "
                f"{validation.reason}"
            )

        # ==========================================
        # STEP 2 — LLM structured extraction
        # ==========================================

        job = self.llm_service.extract_job(
            jd_text=text,
            job_id=job_id,
        )

        # ==========================================
        # STEP 3 — Final sanity validation
        # ==========================================

        if not job.title.strip():
            raise ValueError(
                "Job description extraction failed: "
                "job title could not be identified."
            )

        if not (
            job.required_skills
            or job.preferred_skills
            or job.responsibilities
        ):
            raise ValueError(
                "Job description extraction failed: "
                "no meaningful requirements could be identified."
            )

        return job

    def extract_from_request(
        self,
        request: JobExtractionRequest,
    ) -> JobDescription:
        """Extract a JobDescription from a request schema."""

        return self.extract(
            text=request.text,
            job_id=request.job_id,
        )