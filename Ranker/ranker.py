from __future__ import annotations

from typing import Any

from Ranker.evaluator import evaluate_candidate
from Ranker.schemas import RankingItem
from Ranker.schemas import RankingResponse


def rank_candidates(
    candidates: list[Any],
    jd: Any,
) -> RankingResponse:

    evaluations = [
        evaluate_candidate(
            candidate,
            jd,
        )
        for candidate in candidates
    ]

    evaluations.sort(
        key=lambda result: result.match_score,
        reverse=True,
    )

    rankings = []

    for index, evaluation in enumerate(
        evaluations,
        start=1,
    ):

        candidate = _find_candidate(
            candidates,
            evaluation.candidate_id,
        )

        rankings.append(
            RankingItem(
                rank=index,
                candidate_id=evaluation.candidate_id,
                candidate_name=evaluation.candidate_name,
                match_score=evaluation.match_score,
                resume_score=_resume_score(
                    candidate
                ),
                recommendation=evaluation.recommendation,
            )
        )

    return RankingResponse(
        job_title=_job_title(
            jd
        ),
        total_candidates=len(
            candidates
        ),
        rankings=rankings,
        evaluations=evaluations,
    )


def _find_candidate(
    candidates: list[Any],
    candidate_id: str,
) -> Any:

    for candidate in candidates:

        data = _to_dict(
            candidate
        )

        if str(
            data.get(
                "candidate_id",
                "",
            )
        ) == candidate_id:

            return candidate

    return None


def _resume_score(
    candidate: Any,
) -> float | None:

    if candidate is None:

        return None

    data = _to_dict(
        candidate
    )

    return data.get(
        "resume_score"
    )


def _job_title(
    jd: Any,
) -> str | None:

    data = _to_dict(
        jd
    )

    return data.get(
        "job_title"
    )


def _to_dict(
    value: Any,
) -> dict:

    if hasattr(
        value,
        "model_dump",
    ):

        return value.model_dump()

    if isinstance(
        value,
        dict,
    ):

        return value

    if value is None:

        return {}

    raise TypeError(
        "Expected a Pydantic model or dict."
    )
