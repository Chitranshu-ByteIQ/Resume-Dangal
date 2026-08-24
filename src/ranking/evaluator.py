"""
Candidate evaluation and ranking engine.

This module:
    1. Retrieves candidates and JD
    2. Calculates candidate scores
    3. Sorts candidates by score
    4. Produces an explainable ranking result
"""

from dataclasses import asdict, dataclass

from src.ranking.retrieval import RankingRetriever
from src.ranking.scoring import (
    ScoreBreakdown,
    calculate_score,
)
from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription


# ============================================================
# Ranking Result
# ============================================================

@dataclass
class CandidateRanking:
    """Ranking result for one candidate."""

    rank: int
    candidate_id: str
    candidate_name: str

    total_score: float

    required_skills_score: float
    preferred_skills_score: float
    experience_score: float
    title_score: float
    project_score: float

    matched_required_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]

    recommendation: str


# ============================================================
# Recommendation
# ============================================================

def generate_recommendation(
    score: float,
    missing_required_skills: list[str],
) -> str:
    """
    Generate a simple recommendation based on
    deterministic score and missing mandatory skills.
    """

    if missing_required_skills:
        if score >= 75:
            return (
                "Strong candidate, but missing "
                "some required skills."
            )

        if score >= 50:
            return (
                "Potential candidate, but requires "
                "skill-gap review."
            )

        return (
            "Low match due to missing required skills."
        )

    if score >= 85:
        return "Excellent match."

    if score >= 70:
        return "Strong match."

    if score >= 55:
        return "Moderate match."

    return "Low match."


# ============================================================
# Convert Score
# ============================================================

def build_ranking(
    candidate: CandidateProfile,
    score: ScoreBreakdown,
    rank: int,
) -> CandidateRanking:
    """Convert scoring result into ranking result."""

    return CandidateRanking(
        rank=rank,
        candidate_id=candidate.candidate_id,
        candidate_name=candidate.name,

        total_score=score.total,

        required_skills_score=score.required_skills,
        preferred_skills_score=score.preferred_skills,
        experience_score=score.experience,
        title_score=score.title,
        project_score=score.projects,

        matched_required_skills=(
            score.matched_required_skills
        ),

        missing_required_skills=(
            score.missing_required_skills
        ),

        matched_preferred_skills=(
            score.matched_preferred_skills
        ),

        recommendation=generate_recommendation(
            score.total,
            score.missing_required_skills,
        ),
    )


# ============================================================
# Evaluator
# ============================================================

class CandidateEvaluator:
    """
    Main ranking engine.

    This class coordinates:

        Retrieval
            ↓
        Scoring
            ↓
        Ranking
    """

    def __init__(
        self,
        retriever: RankingRetriever | None = None,
    ):
        self.retriever = (
            retriever
            or RankingRetriever()
        )

    # ========================================================
    # Rank Candidates
    # ========================================================

    def rank_candidates(
        self,
        job: JobDescription,
        candidates: list[CandidateProfile],
    ) -> list[CandidateRanking]:
        """
        Rank candidates against a Job Description.
        """

        results = []

        for candidate in candidates:

            score = calculate_score(
                candidate=candidate,
                job=job,
            )

            results.append(
                (
                    candidate,
                    score,
                )
            )

        # ----------------------------------------------------
        # Sort by total score
        # ----------------------------------------------------

        results.sort(
            key=lambda item: item[1].total,
            reverse=True,
        )

        # ----------------------------------------------------
        # Assign ranks
        # ----------------------------------------------------

        rankings = []

        for rank, (
            candidate,
            score,
        ) in enumerate(
            results,
            start=1,
        ):

            ranking = build_ranking(
                candidate=candidate,
                score=score,
                rank=rank,
            )

            rankings.append(ranking)

        return rankings

    # ========================================================
    # Rank From S3
    # ========================================================

    def rank_job(
        self,
        job_id: str,
    ) -> list[CandidateRanking]:
        """
        Load JD and candidates from S3 and rank them.
        """

        job, candidates = (
            self.retriever
            .get_candidates_for_job(
                job_id
            )
        )

        return self.rank_candidates(
            job=job,
            candidates=candidates,
        )

    # ========================================================
    # JSON Output
    # ========================================================

    def rank_job_as_dict(
        self,
        job_id: str,
    ) -> list[dict]:
        """
        Return ranking results as JSON-compatible
        dictionaries.
        """

        rankings = self.rank_job(
            job_id
        )

        return [
            asdict(ranking)
            for ranking in rankings
        ]