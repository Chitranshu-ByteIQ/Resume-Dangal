from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from Ranker.prompts import EVALUATION_HUMAN_PROMPT
from Ranker.prompts import EVALUATION_SYSTEM_PROMPT
from Ranker.schemas import EvaluationDraft
from Ranker.schemas import MatchResult


load_dotenv(override=True)


WEIGHTS = {
    "required_skill_score": 0.40,
    "experience_score": 0.20,
    "project_score": 0.15,
    "preferred_skill_score": 0.10,
    "responsibility_score": 0.10,
    "education_score": 0.05,
}


STATUS_CREDIT = {
    "EXACT": 1.0,
    "RELATED": 0.75,
    "PARTIAL": 0.50,
    "MISSING": 0.0,
}


def get_llm() -> ChatGroq:

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    )

    if not api_key:

        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return ChatGroq(
        model=model,
        temperature=0,
        api_key=api_key,
    )


def evaluate_candidate(
    candidate: Any,
    jd: Any,
) -> MatchResult:

    candidate_payload = _compact_candidate(
        candidate
    )
    jd_payload = _compact_jd(
        jd
    )

    draft = _llm_evaluate(
        candidate_payload,
        jd_payload,
    )

    required_skill_score = _required_skill_score(
        draft
    )

    raw_match_score = _weighted_score(
        required_skill_score=required_skill_score,
        preferred_skill_score=draft.preferred_skill_score,
        experience_score=draft.experience_score,
        project_score=draft.project_score,
        responsibility_score=draft.responsibility_score,
        education_score=draft.education_score,
    )

    match_score = _apply_required_skill_cap(
        raw_match_score,
        draft,
    )

    strengths = _clean_items(
        draft.strengths
    )
    gaps = _clean_items(
        draft.gaps
    )

    gaps.extend(
        _missing_required_skill_gaps(
            draft
        )
    )

    return MatchResult(
        candidate_id=str(
            candidate_payload.get(
                "candidate_id",
                "",
            )
        ),
        candidate_name=candidate_payload.get(
            "name"
        ),
        match_score=match_score,
        required_skill_score=required_skill_score,
        preferred_skill_score=_round_score(
            draft.preferred_skill_score
        ),
        experience_score=_round_score(
            draft.experience_score
        ),
        project_score=_round_score(
            draft.project_score
        ),
        responsibility_score=_round_score(
            draft.responsibility_score
        ),
        education_score=_round_score(
            draft.education_score
        ),
        strengths=strengths,
        gaps=_dedupe(
            gaps
        ),
        recommendation=_recommendation(
            match_score
        ),
    )


def _llm_evaluate(
    candidate_payload: dict[str, Any],
    jd_payload: dict[str, Any],
) -> EvaluationDraft:

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                EVALUATION_SYSTEM_PROMPT,
            ),
            (
                "human",
                EVALUATION_HUMAN_PROMPT,
            ),
        ]
    )

    structured_llm = get_llm().with_structured_output(
        EvaluationDraft
    )

    chain = prompt | structured_llm

    try:

        return chain.invoke(
            {
                "candidate": _json(candidate_payload),
                "jd": _json(jd_payload),
            }
        )

    except Exception as error:

        raise RuntimeError(
            f"Candidate evaluation failed: {error}"
        ) from error


def _compact_candidate(
    candidate: Any,
) -> dict[str, Any]:

    data = _to_dict(
        candidate
    )

    return {
        "candidate_id": data.get(
            "candidate_id"
        ),
        "name": data.get(
            "name"
        ),
        "summary": data.get(
            "summary"
        ),
        "skills": data.get(
            "skills",
            [],
        ),
        "experience": data.get(
            "experience",
            [],
        ),
        "projects": data.get(
            "projects",
            [],
        ),
        "education": data.get(
            "education",
            [],
        ),
    }


def _compact_jd(
    jd: Any,
) -> dict[str, Any]:

    data = _to_dict(
        jd
    )

    return {
        "job_title": data.get(
            "job_title"
        ),
        "required_skills": data.get(
            "required_skills",
            [],
        ),
        "preferred_skills": data.get(
            "preferred_skills",
            [],
        ),
        "responsibilities": data.get(
            "responsibilities",
            [],
        ),
        "experience_requirements": data.get(
            "experience_requirements"
        ),
        "education_requirements": data.get(
            "education_requirements"
        ),
    }


def _to_dict(
    value: Any,
) -> dict[str, Any]:

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

    raise TypeError(
        "Expected a Pydantic model or dict."
    )


def _required_skill_score(
    draft: EvaluationDraft,
) -> float:

    if not draft.required_skill_matches:

        return _round_score(
            draft.required_skill_score
        )

    credits = [
        STATUS_CREDIT.get(
            match.status,
            0.0,
        )
        for match in draft.required_skill_matches
    ]

    coverage_score = (
        sum(credits)
        / len(credits)
        * 100
    )

    return _round_score(
        min(
            draft.required_skill_score,
            coverage_score,
        )
    )


def _weighted_score(
    *,
    required_skill_score: float,
    preferred_skill_score: float,
    experience_score: float,
    project_score: float,
    responsibility_score: float,
    education_score: float,
) -> float:

    score = (
        required_skill_score
        * WEIGHTS["required_skill_score"]
        + experience_score
        * WEIGHTS["experience_score"]
        + project_score
        * WEIGHTS["project_score"]
        + preferred_skill_score
        * WEIGHTS["preferred_skill_score"]
        + responsibility_score
        * WEIGHTS["responsibility_score"]
        + education_score
        * WEIGHTS["education_score"]
    )

    return _round_score(
        score
    )


def _apply_required_skill_cap(
    score: float,
    draft: EvaluationDraft,
) -> float:

    if not draft.required_skill_matches:

        return _round_score(
            score
        )

    coverage = _required_skill_coverage(
        draft
    )

    if coverage == 0:
        cap = 45
    elif coverage < 0.25:
        cap = 55
    elif coverage < 0.50:
        cap = 70
    elif coverage < 0.75:
        cap = 82
    else:
        cap = 100

    return _round_score(
        min(
            score,
            cap,
        )
    )


def _required_skill_coverage(
    draft: EvaluationDraft,
) -> float:

    if not draft.required_skill_matches:

        return 1.0

    credits = [
        STATUS_CREDIT.get(
            match.status,
            0.0,
        )
        for match in draft.required_skill_matches
    ]

    return sum(credits) / len(credits)


def _missing_required_skill_gaps(
    draft: EvaluationDraft,
) -> list[str]:

    gaps = []

    for match in draft.required_skill_matches:

        if match.status == "MISSING":

            gaps.append(
                f"No {match.skill} evidence found"
            )

    return gaps


def _recommendation(
    score: float,
) -> str:

    if score >= 90:
        return "Excellent candidate"

    if score >= 80:
        return "Strong candidate"

    if score >= 70:
        return "Good candidate"

    if score >= 60:
        return "Moderate candidate"

    return "Weak candidate"


def _clean_items(
    items: list[str],
) -> list[str]:

    return _dedupe(
        [
            item.strip()
            for item in items
            if item and item.strip()
        ]
    )


def _dedupe(
    items: list[str],
) -> list[str]:

    seen = set()
    result = []

    for item in items:

        key = item.lower()

        if key in seen:
            continue

        seen.add(
            key
        )
        result.append(
            item
        )

    return result


def _round_score(
    score: float,
) -> float:

    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        2,
    )


def _json(
    data: dict[str, Any],
) -> str:

    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )
