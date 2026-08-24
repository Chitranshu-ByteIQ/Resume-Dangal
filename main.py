import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)

from services.s3_service import S3Service


load_dotenv(override=True)


# ==========================================================
# FastAPI
# ==========================================================

app = FastAPI(
    title="Resume Dangal API",
    description="Backend API for Resume Dangal",
    version="1.0.0",
)


# ==========================================================
# Services
# ==========================================================

s3_service = S3Service()


# ==========================================================
# Constants
# ==========================================================

RESUME_PREFIX = "resumes/"

ALLOWED_EXTENSIONS = {
    ".pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================================
# Health Check
# ==========================================================

@app.get("/")
def root():
    return {
        "message": "Resume Dangal API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==========================================================
# Upload Resume
# ==========================================================

@app.post(
    "/api/resumes/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...)
):
    """
    Upload a resume to S3.
    """

    # ------------------------------------------------------
    # Validate extension
    # ------------------------------------------------------

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are allowed.",
        )

    # ------------------------------------------------------
    # Read file
    # ------------------------------------------------------

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ------------------------------------------------------
    # Validate file size
    # ------------------------------------------------------

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size cannot exceed 10 MB.",
        )

    # ------------------------------------------------------
    # Generate unique S3 key
    # ------------------------------------------------------

    resume_id = uuid.uuid4().hex

    filename = Path(
        file.filename
    ).name

    s3_key = (
        f"{RESUME_PREFIX}"
        f"{resume_id}_{filename}"
    )

    # ------------------------------------------------------
    # Upload to S3
    # ------------------------------------------------------

    try:
        from io import BytesIO

        s3_service.upload_resume(
            BytesIO(content),
            s3_key,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "message": "Resume uploaded successfully.",
        "resume_id": resume_id,
        "filename": filename,
        "s3_key": s3_key,
        "size": len(content),
    }


# ==========================================================
# List Resumes
# ==========================================================

@app.get("/api/resumes")
def list_resumes():
    """
    Return all resumes stored in S3.
    """

    try:
        objects = s3_service.list_objects(
            RESUME_PREFIX
        )

        resumes = []

        for obj in objects:

            key = obj["Key"]

            if key.endswith("/"):
                continue

            filename = key.split(
                f"{RESUME_PREFIX}",
                1
            )[-1]

            resumes.append(
                {
                    "s3_key": key,
                    "filename": filename,
                    "size": obj.get("Size", 0),
                    "last_modified": (
                        obj.get(
                            "LastModified"
                        ).isoformat()
                        if obj.get("LastModified")
                        else None
                    ),
                }
            )

        return {
            "count": len(resumes),
            "resumes": resumes,
        }

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ==========================================================
# Delete Resume
# ==========================================================

@app.delete("/api/resumes")
def delete_resume(
    s3_key: str,
):
    """
    Delete a resume from S3.
    """

    # ------------------------------------------------------
    # Security check
    # ------------------------------------------------------

    if not s3_key.startswith(
        RESUME_PREFIX
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid resume S3 key.",
        )

    try:
        s3_service.delete_object(
            s3_key
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return {
        "message": "Resume deleted successfully.",
        "s3_key": s3_key,
    }