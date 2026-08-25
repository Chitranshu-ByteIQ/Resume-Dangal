# main.py

from __future__ import annotations

import uuid
from io import BytesIO

from fastapi import (
    Body,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from services.s3_service import (
    S3InvalidJSON,
    S3ObjectNotFound,
    S3Service,
    S3ServiceError,
)

from src.extractor.candidate import (
    extract_candidate,
    extract_text,
)

from src.extractor.job_description import (
    extract_job_description,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Resume Dangal",
    version="1.0.0",
)


s3 = S3Service()


# ============================================================
# CONSTANTS
# ============================================================

MAX_JD_CHARS = 30000


# ============================================================
# CANDIDATE RESPONSE
# ============================================================

def candidate_response(
    profile: dict,
) -> dict:

    candidate_id = profile.get(
        "candidate_id"
    )

    resume_key = (
        f"resumes/"
        f"{candidate_id}/"
        f"resume.pdf"
    )

    return {
        "candidate_id": candidate_id,

        "name": profile.get(
            "name"
        ),

        "resume_score": profile.get(
            "resume_score"
        ),

        "summary": profile.get(
            "summary"
        ),

        "skills": profile.get(
            "skills",
            []
        ),

        "experience": profile.get(
            "experience",
            []
        ),

        "projects": profile.get(
            "projects",
            []
        ),

        "education": profile.get(
            "education",
            []
        ),

        "resume_url": s3.download_url(
            resume_key
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def health():

    return {
        "status": "ok",
        "message": "Resume Dangal API is running",
    }


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.post(
    "/resumes/upload",
    status_code=201,
)
async def upload_resume(
    file: UploadFile = File(...)
):

    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    try:

        # ----------------------------------------------------
        # Candidate ID
        # ----------------------------------------------------

        candidate_id = str(
            uuid.uuid4()
        )

        # ----------------------------------------------------
        # Read PDF
        # ----------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:

            raise HTTPException(
                status_code=400,
                detail="File is empty.",
            )

        # ----------------------------------------------------
        # Resume S3 key
        # ----------------------------------------------------

        resume_key = (
            f"resumes/"
            f"{candidate_id}/"
            f"resume.pdf"
        )

        # ----------------------------------------------------
        # Upload PDF
        # ----------------------------------------------------

        s3.upload(
            BytesIO(file_bytes),
            resume_key,
            "application/pdf",
        )

        # ----------------------------------------------------
        # Extract text
        # ----------------------------------------------------

        resume_text = extract_text(
            file_bytes
        )

        if not resume_text.strip():

            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not extract text "
                    "from PDF."
                ),
            )

        # ----------------------------------------------------
        # LLM → CandidateProfile
        # ----------------------------------------------------

        profile = extract_candidate(
            resume_text,
            candidate_id,
        )

        # ----------------------------------------------------
        # Store candidate profile
        # ----------------------------------------------------

        profile_key = (
            f"candidates/"
            f"{candidate_id}/"
            f"profile.json"
        )

        s3.upload_json(
            profile.model_dump(),
            profile_key,
        )

        # ----------------------------------------------------
        # Resume URL
        # ----------------------------------------------------

        resume_url = s3.download_url(
            resume_key
        )

        return {
            "success": True,

            "candidate": profile.model_dump(),

            "resume": {
                "s3_key": resume_key,
                "download_url": resume_url,
            },
        }

    except HTTPException:
        raise

    except S3ServiceError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


# ============================================================
# LIST CANDIDATES
# ============================================================

@app.get("/candidates")
def list_candidates():

    try:

        # ----------------------------------------------------
        # Profiles are the source of truth
        # ----------------------------------------------------

        profiles = s3.list_objects(
            "candidates/"
        )

        candidates = []

        for profile_object in profiles:

            profile_key = profile_object.get(
                "Key"
            )

            if not profile_key:
                continue

            if not profile_key.endswith(
                "/profile.json"
            ):
                continue

            # candidates/{candidate_id}/profile.json
            parts = profile_key.split("/")

            if len(parts) != 3:
                continue

            candidate_id = parts[1]

            try:

                profile = s3.get_json(
                    profile_key
                )

            except S3ObjectNotFound:

                continue

            # Backend controls candidate ID
            profile["candidate_id"] = (
                profile.get(
                    "candidate_id"
                )
                or candidate_id
            )

            candidates.append(
                candidate_response(
                    profile
                )
            )

        # ----------------------------------------------------
        # Highest resume score first
        # ----------------------------------------------------

        candidates.sort(
            key=lambda candidate: (
                candidate.get(
                    "resume_score"
                )
                or 0
            ),
            reverse=True,
        )

        return {
            "count": len(
                candidates
            ),
            "candidates": candidates,
        }

    except S3InvalidJSON as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except S3ServiceError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


# ============================================================
# FIND CANDIDATE
# ============================================================

@app.get(
    "/candidates/{candidate_id}"
)
def get_candidate(
    candidate_id: str
):

    profile_key = (
        f"candidates/"
        f"{candidate_id}/"
        f"profile.json"
    )

    try:

        profile = s3.get_json(
            profile_key
        )

        profile["candidate_id"] = (
            profile.get(
                "candidate_id"
            )
            or candidate_id
        )

        return candidate_response(
            profile
        )

    except S3ObjectNotFound:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Candidate not found: "
                f"{candidate_id}"
            ),
        )

    except S3InvalidJSON as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except S3ServiceError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


# ============================================================
# DELETE CANDIDATE
# ============================================================

@app.delete(
    "/candidates/{candidate_id}"
)
def delete_candidate(
    candidate_id: str
):

    resume_key = (
        f"resumes/"
        f"{candidate_id}/"
        f"resume.pdf"
    )

    profile_key = (
        f"candidates/"
        f"{candidate_id}/"
        f"profile.json"
    )

    try:

        # ----------------------------------------------------
        # Check candidate exists
        # ----------------------------------------------------

        if not s3.exists(
            profile_key
        ):

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Candidate not found: "
                    f"{candidate_id}"
                ),
            )

        # ----------------------------------------------------
        # Delete resume
        # ----------------------------------------------------

        s3.delete(
            resume_key
        )

        # ----------------------------------------------------
        # Delete profile
        # ----------------------------------------------------

        s3.delete(
            profile_key
        )

        return {
            "success": True,
            "candidate_id": candidate_id,
            "deleted": True,
        }

    except HTTPException:
        raise

    except S3ServiceError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


# ============================================================
# EXTRACT JOB DESCRIPTION
# ============================================================

def validate_jd_text(
    jd_text: str,
) -> str:

    jd_text = jd_text.strip()

    if not jd_text:

        raise HTTPException(
            status_code=400,
            detail="Job description is empty.",
        )

    if len(jd_text) > MAX_JD_CHARS:

        raise HTTPException(
            status_code=413,
            detail=(
                "Job description exceeds "
                f"{MAX_JD_CHARS} characters."
            ),
        )

    return jd_text


def extract_jd_pdf_text(
    file_bytes: bytes,
) -> str:

    try:

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text() or ""

            if text.strip():

                pages.append(
                    text.strip()
                )

        return "\n\n".join(
            pages
        )

    except PdfReadError as error:

        raise HTTPException(
            status_code=400,
            detail="Malformed PDF file.",
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not read PDF file."
            ),
        ) from error


def build_job_description_response(
    jd_text: str,
) -> dict:

    jd_text = validate_jd_text(
        jd_text
    )

    try:

        jd_profile = extract_job_description(
            jd_text
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return {
        "success": True,
        "job_description": (
            jd_profile.model_dump()
        ),
    }


@app.post(
    "/jobs/extract",
    summary="Paste Job Description",
    description=(
        "Paste a raw multiline job description as text/plain. "
        "Do not wrap it in JSON and do not escape newlines."
    ),
)
def extract_job(
    jd_text: str = Body(
        ...,
        media_type="text/plain",
        description=(
            "Raw multiline job description text."
        ),
    )
):

    return build_job_description_response(
        jd_text
    )


@app.post(
    "/jobs/extract/text",
    summary="Paste Job Description",
    description=(
        "Paste a raw multiline job description as text/plain. "
        "Use this endpoint from Swagger when you want text input."
    ),
)
def extract_job_text(
    jd_text: str = Body(
        ...,
        media_type="text/plain",
        description=(
            "Raw multiline job description text."
        ),
    )
):

    return build_job_description_response(
        jd_text
    )


@app.post(
    "/jobs/extract/pdf",
    summary="Upload Job Description PDF",
    description=(
        "Upload a PDF job description. The API extracts text "
        "with pypdf and then uses the same LLM extraction path "
        "as pasted text."
    ),
)
async def extract_job_pdf(
    file: UploadFile = File(
        ...,
        description="Job description PDF file.",
    )
):

    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="PDF file is empty.",
        )

    jd_text = extract_jd_pdf_text(
        file_bytes
    )

    if not jd_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract text "
                "from PDF."
            ),
        )

    return build_job_description_response(
        jd_text
    )
