# main.py

from __future__ import annotations

import uuid
from io import BytesIO

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from src.candidate import (
    extract_candidate,
    extract_text,
)

from services.s3_service import S3Service
from services.s3_service import S3InvalidJSON
from services.s3_service import S3ObjectNotFound
from services.s3_service import S3ServiceError


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Resume Dangal",
    version="1.0.0",
)


s3 = S3Service()


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
# UPLOAD
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
                detail="Could not extract text from PDF.",
            )

        # ----------------------------------------------------
        # LLM → CandidateProfile
        # ----------------------------------------------------

        profile = extract_candidate(
            resume_text,
            candidate_id,
        )

        # ----------------------------------------------------
        # Store profile
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

            profile["candidate_id"] = (
                profile.get("candidate_id")
                or candidate_id
            )

            # ------------------------------------------------
            # Candidate
            # ------------------------------------------------

            candidates.append(
                candidate_response(
                    profile
                )
            )

        # ----------------------------------------------------
        # Highest resume score first
        # ----------------------------------------------------

        candidates.sort(
            key=lambda x: (
                x.get(
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
            profile.get("candidate_id")
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

        s3.delete(
            resume_key
        )

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
