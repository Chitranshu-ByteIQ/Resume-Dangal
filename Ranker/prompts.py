EVALUATION_SYSTEM_PROMPT = """
Evaluate one candidate against one job description.

Use only evidence present in the candidate profile:
skills, experience, projects, education, and summary.
Do not infer missing skills or experience.

Score only these components from 0 to 100:
- required_skill_score
- preferred_skill_score
- experience_score
- project_score
- responsibility_score
- education_score

Do not calculate the final match score.
Do not rank candidates.
Do not use resume_score or jd_score.

For each required skill, classify the match:
EXACT: same skill is clearly present.
RELATED: different but closely related skill with useful evidence.
PARTIAL: narrow or incomplete evidence.
MISSING: no evidence.

Missing required skills must be reflected strongly in
required_skill_score. Give no credit without evidence.

Return concise strengths and gaps tied to actual evidence.
Avoid generic statements.
"""


EVALUATION_HUMAN_PROMPT = """
Job Description:
{jd}

Candidate:
{candidate}
"""
