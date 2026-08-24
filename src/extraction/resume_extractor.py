from src.schemas.candidate import CandidateProfile
from src.schemas.extraction import (
    ExtractionValidationResult,
    ResumeExtractionRequest,
)
from src.services.document_service import DocumentService
from src.services.llm_service import LLMService
from src.extraction.validator import DocumentValidator


class ResumeExtractor:
    """
    Complete resume extraction pipeline.

    Flow:

        File
         ↓
        Text extraction
         ↓
        Deterministic validation
         ↓
        LLM validation
         ↓
        Structured LLM extraction
         ↓
        Pydantic CandidateProfile
    """

    def __init__(
        self,
        document_service: DocumentService | None = None,
        llm_service: LLMService | None = None,
        validator: DocumentValidator | None = None,
    ):
        self.document_service = (
            document_service
            or DocumentService()
        )

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
        file_bytes: bytes,
        filename: str,
        candidate_id: str,
    ) -> CandidateProfile:
        """
        Extract a validated CandidateProfile from a resume.

        Raises:
            ValueError: If the uploaded document is invalid.
        """

        # ==========================================
        # STEP 1 — Extract text
        # ==========================================

        text = self.document_service.extract_text(
            file_bytes=file_bytes,
            filename=filename,
        )

        # ==========================================
        # STEP 2 — Deterministic validation
        # ==========================================

        validation = (
            self.validator.validate_resume_text(text)
        )

        if not validation.is_valid:
            raise ValueError(
                f"Invalid resume: {validation.reason}"
            )

        # ==========================================
        # STEP 3 — LLM validation
        # ==========================================

        llm_validation = (
            self.llm_service.validate_resume(text)
        )

        if not llm_validation.is_valid:
            raise ValueError(
                "Invalid resume: "
                f"{llm_validation.reason}"
            )

        if llm_validation.detected_type != "resume":
            raise ValueError(
                "Invalid resume: "
                "The uploaded document does not appear "
                "to be a resume."
            )

        # ==========================================
        # STEP 4 — Structured extraction
        # ==========================================

        profile = self.llm_service.extract_candidate(
            resume_text=text,
            candidate_id=candidate_id,
            resume_file=filename,
        )

        # ==========================================
        # STEP 5 — Final validation
        # ==========================================

        if not profile.name.strip():
            raise ValueError(
                "Resume extraction failed: "
                "candidate name could not be identified."
            )

        if not (
            profile.tech_stack
            or profile.work_experience
            or profile.projects
            or profile.education
        ):
            raise ValueError(
                "Resume extraction failed: "
                "no meaningful candidate information "
                "could be identified."
            )

        return profile

    def extract_with_text(
        self,
        request: ResumeExtractionRequest,
    ) -> CandidateProfile:
        """
        Extract candidate profile when resume text
        has already been extracted.
        """

        validation = (
            self.validator.validate_resume_text(
                request.text
            )
        )

        if not validation.is_valid:
            raise ValueError(
                validation.reason
            )

        llm_validation = (
            self.llm_service.validate_resume(
                request.text
            )
        )

        if not llm_validation.is_valid:
            raise ValueError(
                llm_validation.reason
            )

        return self.llm_service.extract_candidate(
            resume_text=request.text,
            candidate_id=request.candidate_id,
            resume_file=request.resume_file,
        )