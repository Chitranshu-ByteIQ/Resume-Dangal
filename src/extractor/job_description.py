from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


load_dotenv(override=True)


# ============================================================
# JOB DESCRIPTION PROFILE
# ============================================================

class JobDescriptionProfile(BaseModel):

    # 1
    job_title: Optional[str] = None

    # 2
    summary: Optional[str] = None

    # 3
    required_skills: list[str] = Field(
        default_factory=list
    )

    # 4
    preferred_skills: list[str] = Field(
        default_factory=list
    )

    # 5
    experience_requirements: Optional[str] = None

    # 6
    education_requirements: Optional[str] = None

    # 7
    responsibilities: list[str] = Field(
        default_factory=list
    )

    # 8
    jd_score: float = Field(
        ge=0,
        le=100,
    )


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
# EXTRACT JOB DESCRIPTION
# ============================================================

def extract_job_description(
    jd_text: str,
) -> JobDescriptionProfile:

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            JobDescriptionProfile
        )
    )

    prompt = ChatPromptTemplate.from_messages(
        [

            (
                "system",
                """
Extract a compact job-description profile
for future candidate evaluation and ranking.

Extract ONLY:

1. Job title
2. Short JD summary
3. Required skills
4. Preferred skills
5. Experience requirements
6. Education requirements
7. Important responsibilities
8. Overall JD quality score

RULES:

- Extract only information explicitly present.
- Never invent requirements.
- Do not add skills that are not mentioned.
- Separate required skills from preferred skills.
- Keep the summary concise.
- Keep responsibilities concise.
- Remove duplicate skills.
- Ignore company marketing language.
- Ignore unnecessary information.

jd_score:
Give a 0-100 score representing the quality,
clarity and completeness of the job description.

This is NOT a candidate match score.

The candidate profile will be evaluated separately
against this JD later.

Return only JobDescriptionProfile.
""",
            ),

            (
                "human",
                """
Job Description:

{jd_text}
""",
            ),
        ]
    )

    chain = (
        prompt
        | structured_llm
    )

    return chain.invoke(
        {
            "jd_text": jd_text,
        }
    )