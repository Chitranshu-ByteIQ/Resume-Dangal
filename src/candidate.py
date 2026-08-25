# candidate.py

from __future__ import annotations

import io
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pypdf import PdfReader

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


load_dotenv(override=True)


# ============================================================
# EXPERIENCE
# ============================================================

class Experience(BaseModel):

    role: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None

    highlights: list[str] = Field(
        default_factory=list
    )

    technologies: list[str] = Field(
        default_factory=list
    )


# ============================================================
# PROJECT
# ============================================================

class Project(BaseModel):

    name: Optional[str] = None
    description: Optional[str] = None

    technologies: list[str] = Field(
        default_factory=list
    )


# ============================================================
# EDUCATION
# ============================================================

class Education(BaseModel):

    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None


# ============================================================
# CANDIDATE PROFILE
# ============================================================

class CandidateProfile(BaseModel):

    # 1
    candidate_id: str

    # 2
    name: Optional[str] = None

    # 3
    resume_score: float = Field(
        ge=0,
        le=100,
    )

    # 4
    summary: Optional[str] = None

    # 5
    skills: list[str] = Field(
        default_factory=list
    )

    # 6
    experience: list[Experience] = Field(
        default_factory=list
    )

    # 7
    projects: list[Project] = Field(
        default_factory=list
    )

    # 8
    education: list[Education] = Field(
        default_factory=list
    )


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_text(
    file_bytes: bytes,
) -> str:

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    pages = []

    for page in reader.pages:

        text = page.extract_text() or ""

        if text.strip():

            pages.append(
                text.strip()
            )

    return "\n\n".join(pages)


# ============================================================
# LLM
# ============================================================

def get_llm():

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


# ============================================================
# EXTRACT CANDIDATE
# ============================================================

def extract_candidate(
    resume_text: str,
    candidate_id: str,
) -> CandidateProfile:

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            CandidateProfile
        )
    )

    prompt = ChatPromptTemplate.from_messages(
        [

            (
                "system",
                """
Extract a compact candidate profile for
future job-description matching and ranking.

Extract ONLY:

1. Candidate name
2. Overall resume score
3. Short summary
4. Important skills
5. Relevant work experience
6. Important projects
7. Education

RULES:

- Extract only information explicitly present.
- Never invent information.
- Do not extract email or phone.
- Do not extract LinkedIn or GitHub.
- Do not extract hobbies.
- Do not extract publications.
- Do not extract unnecessary achievements.
- Do not repeat information.
- Keep the output compact.

SUMMARY:
Maximum 40 words.

SKILLS:
Only important technical/professional skills.

EXPERIENCE:
Only important roles.
Keep highlights short.
Include important technologies.

PROJECTS:
Only important projects.
Keep descriptions short.
Include important technologies.

EDUCATION:
Only the main degree/education.

RESUME SCORE:
Give a 0-100 overall resume quality score.

Consider:
- clarity
- technical skills
- practical experience
- projects
- education
- technical depth

IMPORTANT:
This is NOT a JD match score.

The JD will be provided later and a separate
ranking system will calculate the JD match score.

Return only CandidateProfile.
""",
            ),

            (
                "human",
                """
Candidate ID:
{candidate_id}

Resume:

{resume_text}
""",
            ),
        ]
    )

    chain = (
        prompt
        | structured_llm
    )

    profile = chain.invoke(
        {
            "candidate_id": candidate_id,
            "resume_text": resume_text,
        }
    )

    # Candidate ID must always come from backend.
    profile.candidate_id = candidate_id

    return profile