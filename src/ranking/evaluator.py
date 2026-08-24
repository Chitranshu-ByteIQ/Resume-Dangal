from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.schemas.ranking import (
    CandidateRanking,
    RankingResponse,
)
from src.ranking.hybrid import HybridRanker


class RankingEvaluator:
    """
    Evaluates and ranks multiple candidates against one job.
    """

    def __init__(
        self,
        hybrid_ranker: HybridRanker | None = None,
    ):
        self.hybrid = (
            hybrid_ranker
            or HybridRanker()
        )

    def evaluate(
        self,
        job: JobDescription,
        candidates: list[CandidateProfile],
    ) -> RankingResponse:

        results = []

        for candidate in candidates:

            result = self.hybrid.rank_candidate(
                candidate=candidate,
                job=job,
            )

            results.append(result)

        # Sort highest score first
        results.sort(
            key=lambda item: (
                item["breakdown"].final_score
            ),
            reverse=True,
        )

        rankings = []

        for rank, result in enumerate(
            results,
            start=1,
        ):
            candidate = result["candidate"]

            deterministic = result[
                "deterministic"
            ]

            breakdown = result[
                "breakdown"
            ]

            llm_evaluation = result[
                "llm_evaluation"
            ]

            missing_skills = deterministic[
                "missing_required_skills"
            ]

            recommendation = self._recommendation(
                breakdown.final_score,
                missing_skills,
            )

            explanation = self._build_explanation(
                candidate=candidate,
                breakdown=breakdown,
                missing_skills=missing_skills,
            )

            rankings.append(
                CandidateRanking(
                    rank=rank,
                    candidate_id=candidate.candidate_id,
                    candidate_name=candidate.name,
                    scores=breakdown,
                    matched_required_skills=deterministic[
                        "matched_required_skills"
                    ],
                    missing_required_skills=missing_skills,
                    matched_preferred_skills=deterministic[
                        "matched_preferred_skills"
                    ],
                    llm_evaluation=llm_evaluation,
                    strengths=llm_evaluation.strengths,
                    gaps=llm_evaluation.gaps,
                    recommendation=recommendation,
                    explanation=explanation,
                )
            )

        return RankingResponse(
            job_id=job.job_id,
            total_candidates=len(candidates),
            rankings=rankings,
        )

    @staticmethod
    def _recommendation(
        score: float,
        missing_skills: list[str],
    ) -> str:

        if missing_skills:

            if score >= 85:
                return (
                    "Strong candidate with some "
                    "required skill gaps."
                )

            if score >= 70:
                return (
                    "Potential candidate but "
                    "requires skill-gap review."
                )

            return (
                "Weak match with significant "
                "skill gaps."
            )

        if score >= 90:
            return "Excellent match."

        if score >= 80:
            return "Strong match."

        if score >= 70:
            return "Moderate match."

        return "Low match."

    @staticmethod
    def _build_explanation(
        candidate,
        breakdown,
        missing_skills,
    ) -> str:

        explanation = (
            f"{candidate.name} received a final score "
            f"of {breakdown.final_score}/100. "
            f"Deterministic match: "
            f"{breakdown.deterministic_score}/100. "
            f"Semantic match: "
            f"{breakdown.semantic_score}/100. "
            f"LLM evaluation: "
            f"{breakdown.llm_score}/100."
        )

        if missing_skills:
            explanation += (
                " Missing required skills: "
                + ", ".join(missing_skills)
                + ". A transparent mandatory-skill cap was "
                "applied so semantic similarity cannot hide "
                "hard requirement gaps."
            )

        return explanation
