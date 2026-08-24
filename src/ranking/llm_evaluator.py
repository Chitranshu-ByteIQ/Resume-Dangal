from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.schemas.ranking import LLMRankingEvaluation
from src.services.llm_service import LLMService


class LLMRanker:
    """
    LLM-based candidate evaluation.

    This layer provides reasoning and evidence-based
    evaluation rather than replacing deterministic scoring.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
    ):
        self._llm = llm_service

    def evaluate(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> LLMRankingEvaluation:

        return self.llm.evaluate_candidate(
            candidate=candidate,
            job=job,
        )

    @property
    def llm(self) -> LLMService:
        if self._llm is None:
            self._llm = LLMService()

        return self._llm
