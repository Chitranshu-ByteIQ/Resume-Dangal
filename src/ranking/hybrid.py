from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.schemas.ranking import ScoreBreakdown
from src.ranking.scoring import DeterministicScorer
from src.ranking.semantic import SemanticRanker
from src.ranking.llm_evaluator import LLMRanker


class HybridRanker:
    """
    Hybrid AI ranking engine.

    Final score:

        40% deterministic
        40% semantic
        20% LLM reasoning
    """

    DETERMINISTIC_WEIGHT = 0.40
    SEMANTIC_WEIGHT = 0.40
    LLM_WEIGHT = 0.20
    NO_REQUIRED_MATCH_CAP = 55.0
    PARTIAL_REQUIRED_MATCH_CAP = 75.0
    MOST_REQUIRED_MATCH_CAP = 88.0

    def __init__(
        self,
        deterministic_scorer: DeterministicScorer | None = None,
        semantic_ranker: SemanticRanker | None = None,
        llm_ranker: LLMRanker | None = None,
    ):
        self.deterministic = (
            deterministic_scorer
            or DeterministicScorer()
        )

        self.semantic = (
            semantic_ranker
            or SemanticRanker()
        )

        self.llm = (
            llm_ranker
            or LLMRanker()
        )

    def rank_candidate(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> dict:

        # ==========================================
        # 1. Deterministic score
        # ==========================================

        deterministic = self.deterministic.score(
            candidate,
            job,
        )

        # ==========================================
        # 2. Semantic model score
        # ==========================================

        semantic_score = self.semantic.score(
            candidate,
            job,
        )

        # ==========================================
        # 3. LLM evaluation
        # ==========================================

        llm_evaluation = self.llm.evaluate(
            candidate,
            job,
        )

        llm_score = llm_evaluation.overall_score

        # ==========================================
        # 4. Hybrid score
        # ==========================================

        base_score = (
            deterministic["score"]
            * self.DETERMINISTIC_WEIGHT
            + semantic_score
            * self.SEMANTIC_WEIGHT
            + llm_score
            * self.LLM_WEIGHT
        )

        final_score = self._apply_required_skill_cap(
            base_score=base_score,
            deterministic=deterministic,
            job=job,
        )

        breakdown = ScoreBreakdown(
            deterministic_score=deterministic["score"],
            semantic_score=semantic_score,
            llm_score=llm_score,
            final_score=round(
                final_score,
                2,
            ),
        )

        return {
            "candidate": candidate,
            "breakdown": breakdown,
            "deterministic": deterministic,
            "llm_evaluation": llm_evaluation,
            "base_score": round(base_score, 2),
        }

    def _apply_required_skill_cap(
        self,
        base_score: float,
        deterministic: dict,
        job: JobDescription,
    ) -> float:
        required_count = len(job.required_skills)

        if required_count == 0:
            return round(base_score, 2)

        missing_count = len(
            deterministic["missing_required_skills"]
        )

        if missing_count == 0:
            return round(base_score, 2)

        matched_ratio = (
            required_count - missing_count
        ) / required_count

        if matched_ratio <= 0:
            cap = self.NO_REQUIRED_MATCH_CAP
        elif matched_ratio < 0.5:
            cap = self.PARTIAL_REQUIRED_MATCH_CAP
        else:
            cap = self.MOST_REQUIRED_MATCH_CAP

        return round(
            min(base_score, cap),
            2,
        )
