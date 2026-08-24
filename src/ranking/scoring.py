"""
Deterministic scoring engine for Resume Dangal.

The scorer compares a CandidateProfile against a JobDescription
using transparent, explainable signals.

Current prototype signals:
    - Required skills
    - Preferred skills
    - Experience
    - Job title
    - Responsibilities/projects

The final score is between 0 and 100.
"""

from dataclasses import dataclass

from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription


# ============================================================
# Configuration
# ============================================================

REQUIRED_SKILLS_WEIGHT = 40.0
PREFERRED_SKILLS_WEIGHT = 15.0
EXPERIENCE_WEIGHT = 20.0
TITLE_WEIGHT = 10.0
PROJECT_WEIGHT = 15.0


# ============================================================
# Result
# ============================================================

@dataclass
class ScoreBreakdown:
    """Detailed scoring result."""

    required_skills: float
    preferred_skills: float
    experience: float
    title: float
    projects: float
    total: float

    matched_required_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]


# ============================================================
# Utility Functions
# ============================================================

def normalize(value: str) -> str:
    """Normalize text for comparison."""

    return (
        value
        .strip()
        .lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("_", " ")
    )


def normalize_list(values: list[str]) -> set[str]:
    """Normalize a list of strings."""

    return {
        normalize(value)
        for value in values
        if value.strip()
    }


# ============================================================
# Skill Matching
# ============================================================

def calculate_skill_score(
    candidate_skills: list[str],
    required_skills: list[str],
) -> tuple[float, list[str], list[str]]:
    """
    Calculate required-skill coverage.

    Example:

        Required:
            Python, SQL, AWS

        Candidate:
            Python, SQL

        Score:
            66.67%
    """

    required = normalize_list(required_skills)
    candidate = normalize_list(candidate_skills)

    if not required:
        return 100.0, [], []

    matched = required.intersection(candidate)

    missing = required - candidate

    percentage = (
        len(matched) / len(required)
    ) * 100

    return (
        percentage,
        sorted(matched),
        sorted(missing),
    )


# ============================================================
# Preferred Skills
# ============================================================

def calculate_preferred_skill_score(
    candidate_skills: list[str],
    preferred_skills: list[str],
) -> float:
    """Calculate preferred skill coverage."""

    preferred = normalize_list(preferred_skills)
    candidate = normalize_list(candidate_skills)

    if not preferred:
        return 100.0

    matched = preferred.intersection(candidate)

    return (
        len(matched) / len(preferred)
    ) * 100


# ============================================================
# Experience
# ============================================================

def calculate_experience_score(
    candidate_experience: float | None,
    required_experience: float | None,
) -> float:
    """
    Calculate experience score.

    Candidate meeting or exceeding the requirement
    receives 100.

    Candidates below the requirement receive a
    proportional score.
    """

    if required_experience is None:
        return 100.0

    if candidate_experience is None:
        return 0.0

    if required_experience <= 0:
        return 100.0

    if candidate_experience >= required_experience:
        return 100.0

    return (
        candidate_experience
        / required_experience
    ) * 100


# ============================================================
# Title Matching
# ============================================================

def calculate_title_score(
    candidate_title: str | None,
    job_title: str,
) -> float:
    """
    Simple title similarity.

    This is intentionally basic.

    Later this can be replaced with
    embedding-based semantic similarity.
    """

    if not candidate_title:
        return 0.0

    candidate = normalize(candidate_title)
    job = normalize(job_title)

    if candidate == job:
        return 100.0

    candidate_words = set(candidate.split())
    job_words = set(job.split())

    if not candidate_words or not job_words:
        return 0.0

    overlap = candidate_words.intersection(
        job_words
    )

    return (
        len(overlap)
        / len(job_words)
    ) * 100


# ============================================================
# Project Matching
# ============================================================

def calculate_project_score(
    projects: list[str],
    responsibilities: list[str],
) -> float:
    """
    Basic keyword overlap between projects and
    job responsibilities.

    This is a baseline.

    Semantic embeddings will replace this later.
    """

    if not responsibilities:
        return 100.0

    if not projects:
        return 0.0

    project_text = normalize(
        " ".join(projects)
    )

    responsibility_text = normalize(
        " ".join(responsibilities)
    )

    responsibility_words = set(
        responsibility_text.split()
    )

    project_words = set(
        project_text.split()
    )

    if not responsibility_words:
        return 100.0

    overlap = project_words.intersection(
        responsibility_words
    )

    return (
        len(overlap)
        / len(responsibility_words)
    ) * 100


# ============================================================
# Main Scoring Function
# ============================================================

def calculate_score(
    candidate: CandidateProfile,
    job: JobDescription,
) -> ScoreBreakdown:
    """
    Calculate complete candidate score.

    Total =

        Required Skills  → 40%
        Preferred Skills → 15%
        Experience       → 20%
        Title            → 10%
        Projects         → 15%

        Total             → 100%
    """

    # --------------------------------------------------------
    # Required skills
    # --------------------------------------------------------

    (
        required_percentage,
        matched_required,
        missing_required,
    ) = calculate_skill_score(
        candidate.tech_stack,
        job.required_skills,
    )

    required_score = (
        required_percentage
        * REQUIRED_SKILLS_WEIGHT
        / 100
    )

    # --------------------------------------------------------
    # Preferred skills
    # --------------------------------------------------------

    preferred_percentage = (
        calculate_preferred_skill_score(
            candidate.tech_stack,
            job.preferred_skills,
        )
    )

    preferred_score = (
        preferred_percentage
        * PREFERRED_SKILLS_WEIGHT
        / 100
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience_percentage = (
        calculate_experience_score(
            candidate.experience_years,
            job.experience_required,
        )
    )

    experience_score = (
        experience_percentage
        * EXPERIENCE_WEIGHT
        / 100
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title_percentage = (
        calculate_title_score(
            candidate.suitable_title,
            job.title,
        )
    )

    title_score = (
        title_percentage
        * TITLE_WEIGHT
        / 100
    )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    project_percentage = (
        calculate_project_score(
            candidate.projects,
            job.responsibilities,
        )
    )

    project_score = (
        project_percentage
        * PROJECT_WEIGHT
        / 100
    )

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    total = (
        required_score
        + preferred_score
        + experience_score
        + title_score
        + project_score
    )

    return ScoreBreakdown(
        required_skills=round(
            required_score,
            2,
        ),
        preferred_skills=round(
            preferred_score,
            2,
        ),
        experience=round(
            experience_score,
            2,
        ),
        title=round(
            title_score,
            2,
        ),
        projects=round(
            project_score,
            2,
        ),
        total=round(
            total,
            2,
        ),
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=sorted(
            normalize_list(
                job.preferred_skills
            ).intersection(
                normalize_list(
                    candidate.tech_stack
                )
            )
        ),
    )