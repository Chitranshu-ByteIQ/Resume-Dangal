import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.schemas.candidate import CandidateProfile
from src.schemas.extraction import ExtractionValidationResult
from src.schemas.job import JobDescription
from src.schemas.ranking import LLMRankingEvaluation

load_dotenv(override=True)


class LLMService:
    """LLM service for extraction, validation and ranking."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.llm = None
        self.structured_candidate_llm = None
        self.structured_job_llm = None
        self.structured_validation_llm = None
        self.structured_ranking_llm = None

    def _ensure_client(self) -> None:
        if self.llm is not None:
            return

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Set it before using LLM-powered endpoints."
            )

        self.llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.2,
            api_key=self.api_key,
        )

        self.structured_candidate_llm = (
            self.llm.with_structured_output(
                CandidateProfile
            )
        )

        self.structured_job_llm = (
            self.llm.with_structured_output(
                JobDescription
            )
        )

        self.structured_validation_llm = (
            self.llm.with_structured_output(
                ExtractionValidationResult
            )
        )

        self.structured_ranking_llm = (
            self.llm.with_structured_output(
                LLMRankingEvaluation
            )
        )

    def extract_candidate(
        self,
        resume_text: str,
        candidate_id: str,
        resume_file: str,
    ) -> CandidateProfile:
        """Extract structured candidate information."""

        self._ensure_client()

        prompt = f"""
You are an expert resume information extraction system.

Extract structured information from the resume below.

Rules:
- Do not invent information.
- Only use information explicitly supported by the resume.
- Infer a suitable professional title only when strongly supported.
- Calculate experience conservatively.
- Preserve important technical skills.
- Extract relevant projects.
- Keep the output factual.
- candidate_id MUST be: {candidate_id}
- resume_file MUST be: {resume_file}

RESUME:
----------------
{resume_text}
----------------
"""

        result = self.structured_candidate_llm.invoke(prompt)

        return result

    def extract_job(
        self,
        jd_text: str,
        job_id: str,
    ) -> JobDescription:
        """Extract structured information from a JD."""

        self._ensure_client()

        prompt = f"""
You are an expert job-description parsing system.

Convert the following Job Description into structured
information.

Rules:
- Do not invent requirements.
- Separate mandatory skills from preferred skills.
- Extract the minimum required experience when stated.
- Extract the major responsibilities.
- Extract education requirements.
- job_id MUST be: {job_id}

JOB DESCRIPTION:
----------------
{jd_text}
----------------
"""

        result = self.structured_job_llm.invoke(prompt)

        return result

    def validate_resume(
        self,
        resume_text: str,
    ) -> ExtractionValidationResult:
        """
        Determine whether extracted text represents
        a legitimate resume.
        """

        self._ensure_client()

        prompt = f"""
Determine whether the following document is a genuine
professional resume.

A resume normally contains several of:
- candidate identity
- professional summary
- education
- skills
- work experience
- projects
- certifications

Reject documents that are:
- random text
- essays
- advertisements
- unrelated documents
- empty or meaningless content

Do not judge the candidate's quality.
Only determine whether the document is a resume.

DOCUMENT:
----------------
{resume_text}
----------------
"""

        return self.structured_validation_llm.invoke(prompt)

    def evaluate_candidate(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> LLMRankingEvaluation:
        """Perform LLM-based candidate evaluation."""

        self._ensure_client()

        prompt = f"""
You are an expert technical recruiter.

Evaluate the candidate against the job description.

Do NOT evaluate based on:
- name
- gender
- age
- nationality
- religion
- race
- photograph
- other protected characteristics.

Evaluate ONLY job-relevant evidence.

JOB:
{job.model_dump_json(indent=2)}

CANDIDATE:
{candidate.model_dump_json(indent=2)}

Evaluate:
1. Required skill fit
2. Relevant experience
3. Responsibility alignment
4. Project relevance
5. Overall technical suitability

Be conservative.
Do not reward skills that are not supported by evidence.
"""

        return self.structured_ranking_llm.invoke(prompt)
