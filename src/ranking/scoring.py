import re

from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription


class DeterministicScorer:
    """
    Explainable rule-based scoring engine.

    Components:

        Required skills   -> 40%
        Preferred skills  -> 15%
        Experience        -> 20%
        Title             -> 10%
        Projects          -> 15%
    """

    REQUIRED_WEIGHT = 0.40
    PREFERRED_WEIGHT = 0.15
    EXPERIENCE_WEIGHT = 0.20
    TITLE_WEIGHT = 0.10
    PROJECT_WEIGHT = 0.15
    SKILL_ALIASES = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "js": "javascript",
        "javascript": "javascript",
        "ts": "typescript",
        "typescript": "typescript",
    }

    def score(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> dict:
        required_score, matched_required, missing_required = (
            self._skill_score(
                job.required_skills,
                candidate.tech_stack,
            )
        )

        preferred_score, matched_preferred, _ = (
            self._skill_score(
                job.preferred_skills,
                candidate.tech_stack,
            )
        )

        experience_score = self._experience_score(
            candidate.experience_years,
            job.experience_required,
        )

        title_score = self._title_score(
            candidate.suitable_title,
            job.title,
        )

        project_score = self._project_score(
            candidate,
            job,
        )

        final_score = (
            required_score * self.REQUIRED_WEIGHT
            + preferred_score * self.PREFERRED_WEIGHT
            + experience_score * self.EXPERIENCE_WEIGHT
            + title_score * self.TITLE_WEIGHT
            + project_score * self.PROJECT_WEIGHT
        )

        return {
            "score": round(final_score, 2),
            "required_skills_score": round(
                required_score,
                2,
            ),
            "preferred_skills_score": round(
                preferred_score,
                2,
            ),
            "experience_score": round(
                experience_score,
                2,
            ),
            "title_score": round(
                title_score,
                2,
            ),
            "project_score": round(
                project_score,
                2,
            ),
            "matched_required_skills": matched_required,
            "missing_required_skills": missing_required,
            "matched_preferred_skills": matched_preferred,
        }

    def _skill_score(
        self,
        required: list[str],
        candidate_skills: list[str],
    ):
        if not required:
            return 100.0, [], []

        candidate_normalized = {
            self._normalize(skill)
            for skill in candidate_skills
        }
        candidate_tokens = set()

        for skill in candidate_skills:
            candidate_tokens.update(
                self._normalize(skill).split()
            )

        matched = []
        missing = []

        for skill in required:
            normalized = self._normalize(skill)

            if (
                normalized in candidate_normalized
                or normalized in candidate_tokens
            ):
                matched.append(skill)
            else:
                missing.append(skill)

        score = (
            len(matched)
            / len(required)
            * 100
        )

        return score, matched, missing

    def _experience_score(
        self,
        candidate_experience: float | None,
        required_experience: float | None,
    ) -> float:

        if required_experience is None:
            return 100.0

        if candidate_experience is None:
            return 0.0

        if candidate_experience >= required_experience:
            return 100.0

        return min(
            candidate_experience
            / required_experience
            * 100,
            100,
        )

    def _title_score(
        self,
        candidate_title: str | None,
        job_title: str,
    ) -> float:

        if not candidate_title:
            return 0.0

        candidate_words = set(
            self._normalize(candidate_title).split()
        )

        job_words = set(
            self._normalize(job_title).split()
        )

        if not job_words:
            return 100.0

        overlap = candidate_words & job_words

        return (
            len(overlap)
            / len(job_words)
            * 100
        )

    def _project_score(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> float:

        if not candidate.projects:
            return 0.0

        job_text = " ".join(
            [
                job.title,
                *job.required_skills,
                *job.preferred_skills,
                *job.responsibilities,
            ]
        )

        job_words = set(
            self._normalize(job_text).split()
        )

        if not job_words:
            return 0.0

        project_text = " ".join(
            candidate.projects
        )

        project_words = set(
            self._normalize(project_text).split()
        )

        overlap = job_words & project_words

        return min(
            len(overlap)
            / max(len(job_words), 1)
            * 100,
            100,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(
            r"[^a-z0-9+#.]",
            " ",
            text,
        )
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        normalized = text.strip()

        return DeterministicScorer.SKILL_ALIASES.get(
            normalized,
            normalized,
        )
