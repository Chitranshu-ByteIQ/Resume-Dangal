from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


SkillMatchStatus = Literal[
    "EXACT",
    "RELATED",
    "PARTIAL",
    "MISSING",
]


class SkillAssessment(BaseModel):
    skill: str
    status: SkillMatchStatus
    evidence: Optional[str] = None


class EvaluationDraft(BaseModel):
    required_skill_score: float = Field(
        ge=0,
        le=100,
    )
    preferred_skill_score: float = Field(
        ge=0,
        le=100,
    )
    experience_score: float = Field(
        ge=0,
        le=100,
    )
    project_score: float = Field(
        ge=0,
        le=100,
    )
    responsibility_score: float = Field(
        ge=0,
        le=100,
    )
    education_score: float = Field(
        ge=0,
        le=100,
    )
    required_skill_matches: list[SkillAssessment] = Field(
        default_factory=list
    )
    strengths: list[str] = Field(
        default_factory=list
    )
    gaps: list[str] = Field(
        default_factory=list
    )


class MatchResult(BaseModel):
    candidate_id: str
    candidate_name: Optional[str] = None
    match_score: float = Field(
        ge=0,
        le=100,
    )
    required_skill_score: float = Field(
        ge=0,
        le=100,
    )
    preferred_skill_score: float = Field(
        ge=0,
        le=100,
    )
    experience_score: float = Field(
        ge=0,
        le=100,
    )
    project_score: float = Field(
        ge=0,
        le=100,
    )
    responsibility_score: float = Field(
        ge=0,
        le=100,
    )
    education_score: float = Field(
        ge=0,
        le=100,
    )
    strengths: list[str] = Field(
        default_factory=list
    )
    gaps: list[str] = Field(
        default_factory=list
    )
    recommendation: str


class RankingItem(BaseModel):
    rank: int
    candidate_id: str
    candidate_name: Optional[str] = None
    match_score: float = Field(
        ge=0,
        le=100,
    )
    resume_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )
    recommendation: str


class RankingResponse(BaseModel):
    job_title: Optional[str] = None
    total_candidates: int
    rankings: list[RankingItem] = Field(
        default_factory=list
    )
    evaluations: list[MatchResult] = Field(
        default_factory=list
    )
