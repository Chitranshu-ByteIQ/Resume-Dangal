import re

from src.schemas.extraction import ExtractionValidationResult


class DocumentValidator:
    """
    Performs deterministic validation before using the LLM.

    The goal is to reject obviously invalid documents cheaply
    before spending an LLM request.
    """

    RESUME_KEYWORDS = {
        "resume",
        "cv",
        "experience",
        "education",
        "skills",
        "projects",
        "employment",
        "work experience",
        "certifications",
        "professional summary",
        "career",
        "objective",
    }

    JD_KEYWORDS = {
        "job description",
        "responsibilities",
        "requirements",
        "qualifications",
        "skills",
        "experience",
        "role",
        "position",
        "employment",
        "education",
    }

    MIN_RESUME_TEXT_LENGTH = 150
    MIN_JD_TEXT_LENGTH = 100

    def validate_resume_text(
        self,
        text: str,
    ) -> ExtractionValidationResult:
        """
        Validate whether extracted text looks like a resume.

        This is deterministic validation only.
        LLM validation is performed separately.
        """

        if not text or not text.strip():
            return ExtractionValidationResult(
                is_valid=False,
                confidence=100,
                reason="The document contains no readable text.",
                detected_type="unknown",
            )

        normalized = self._normalize(text)

        if len(normalized) < self.MIN_RESUME_TEXT_LENGTH:
            return ExtractionValidationResult(
                is_valid=False,
                confidence=95,
                reason=(
                    "The document contains too little readable "
                    "content to be a resume."
                ),
                detected_type="unknown",
            )

        keyword_matches = self._count_keyword_matches(
            normalized,
            self.RESUME_KEYWORDS,
        )

        if keyword_matches < 2:
            return ExtractionValidationResult(
                is_valid=False,
                confidence=85,
                reason=(
                    "The document does not contain enough "
                    "resume-related sections."
                ),
                detected_type="unknown",
            )

        return ExtractionValidationResult(
            is_valid=True,
            confidence=min(
                60 + keyword_matches * 8,
                95,
            ),
            reason="The document contains resume-like content.",
            detected_type="resume",
        )

    def validate_jd_text(
        self,
        text: str,
    ) -> ExtractionValidationResult:
        """Validate whether text looks like a Job Description."""

        if not text or not text.strip():
            return ExtractionValidationResult(
                is_valid=False,
                confidence=100,
                reason="Job description is empty.",
                detected_type="unknown",
            )

        normalized = self._normalize(text)

        if len(normalized) < self.MIN_JD_TEXT_LENGTH:
            return ExtractionValidationResult(
                is_valid=False,
                confidence=95,
                reason="Job description is too short.",
                detected_type="unknown",
            )

        keyword_matches = self._count_keyword_matches(
            normalized,
            self.JD_KEYWORDS,
        )

        if keyword_matches < 2:
            return ExtractionValidationResult(
                is_valid=False,
                confidence=80,
                reason=(
                    "The text does not contain enough "
                    "job-description indicators."
                ),
                detected_type="unknown",
            )

        return ExtractionValidationResult(
            is_valid=True,
            confidence=min(
                60 + keyword_matches * 8,
                95,
            ),
            reason="The text contains job-description content.",
            detected_type="job_description",
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _count_keyword_matches(
        text: str,
        keywords: set[str],
    ) -> int:
        return sum(
            1
            for keyword in keywords
            if keyword in text
        )