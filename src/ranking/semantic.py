from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.services.hf_service import HFService


class SemanticRanker:
    """
    Semantic candidate-JD matching using the Hugging Face model.
    """

    def __init__(
        self,
        hf_service: HFService | None = None,
    ):
        self.hf = hf_service or HFService()

    def score(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> float:
        resume_text = self._candidate_text(
            candidate
        )

        job_text = self._job_text(
            job
        )

        return self.hf.score(
            resume_text=resume_text,
            job_text=job_text,
        )

    @staticmethod
    def _candidate_text(
        candidate: CandidateProfile,
    ) -> str:

        return "\n".join(
            [
                f"Title: {candidate.suitable_title or ''}",
                f"Experience: {candidate.experience_years or 0} years",
                f"Skills: {', '.join(candidate.tech_stack)}",
                f"Education: {', '.join(candidate.education)}",
                f"Projects: {' '.join(candidate.projects)}",
                f"Work Experience: {' '.join(candidate.work_experience)}",
                f"Summary: {candidate.profile_summary or ''}",
            ]
        )

    @staticmethod
    def _job_text(
        job: JobDescription,
    ) -> str:

        return "\n".join(
            [
                f"Title: {job.title}",
                f"Required Skills: {', '.join(job.required_skills)}",
                f"Preferred Skills: {', '.join(job.preferred_skills)}",
                f"Experience: {job.experience_required or 0} years",
                f"Responsibilities: {' '.join(job.responsibilities)}",
                f"Education: {', '.join(job.education)}",
                f"Description: {job.description or ''}",
            ]
        )