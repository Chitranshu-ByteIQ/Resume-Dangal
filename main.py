"""
Resume Dangal - FastAPI Backend

Responsibilities:
- Upload resumes to AWS S3
- List stored resumes
- Retrieve a specific resume
- Delete resumes
- Run the resume ranking engine
"""

import logging
import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.s3_service import S3Service
from src.graph.workflow import app as ranking_graph
from src.utils.file_handler import extract_text_from_pdf


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Resume Dangal API",
    description="AI-powered resume ranking backend",
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SERVICES
# ============================================================

s3_service = S3Service()


# ============================================================
# CONSTANTS
# ============================================================

RESUME_PREFIX = "resumes/"

ALLOWED_EXTENSIONS = {".pdf"}

MAX_FILE_SIZE = 10 * 1024 * 1024


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ResumeItem(BaseModel):
    resume_id: str
    filename: str
    s3_key: str
    size: int
    last_modified: str | None = None


class ResumeListResponse(BaseModel):
    count: int
    resumes: list[ResumeItem]


class UploadResponse(BaseModel):
    message: str
    resume_id: str
    filename: str
    size: int


class RankingRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=20,
        description="Job description used for ranking",
    )

    resume_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Resume IDs selected for ranking",
    )


# ============================================================
# HELPERS
# ============================================================

def safe_filename(filename: str) -> str:
    """
    Prevent unsafe characters in S3 filenames.
    """

    filename = Path(filename).name

    filename = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename,
    )

    return filename


def extract_resume_id(s3_key: str) -> str:
    """
    Extract UUID from:

    resumes/<uuid>_<filename>.pdf
    """

    filename = s3_key.removeprefix(RESUME_PREFIX)

    return filename.split("_", 1)[0]


def find_resume_by_id(resume_id: str) -> dict[str, Any]:
    """
    Find resume metadata from S3.
    """

    objects = s3_service.list_objects(
        RESUME_PREFIX
    )

    for obj in objects:

        key = obj.get("Key", "")

        if key.endswith("/"):
            continue

        current_id = extract_resume_id(key)

        if current_id == resume_id:

            filename = key.removeprefix(
                RESUME_PREFIX
            )

            if "_" in filename:
                filename = filename.split(
                    "_",
                    1,
                )[1]

            return {
                "resume_id": current_id,
                "filename": filename,
                "s3_key": key,
                "size": obj.get("Size", 0),
                "last_modified": (
                    obj["LastModified"].isoformat()
                    if obj.get("LastModified")
                    else None
                ),
            }

    raise HTTPException(
        status_code=404,
        detail=f"Resume '{resume_id}' not found.",
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": "Resume Dangal API",
        "version": "2.0.0",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    try:

        # Check S3 connectivity.
        s3_service.list_objects(
            RESUME_PREFIX
        )

        return {
            "status": "healthy",
            "storage": "connected",
        }

    except Exception as error:

        logger.exception(
            "Health check failed"
        )

        return {
            "status": "degraded",
            "storage": "unavailable",
            "error": str(error),
        }


# ============================================================
# LIST RESUMES
# ============================================================

@app.get(
    "/api/resumes",
    response_model=ResumeListResponse,
)
async def list_resumes():

    try:

        objects = s3_service.list_objects(
            RESUME_PREFIX
        )

        resumes = []

        for obj in objects:

            key = obj.get("Key", "")

            if not key or key.endswith("/"):
                continue

            resume_id = extract_resume_id(
                key
            )

            filename = key.removeprefix(
                RESUME_PREFIX
            )

            if "_" in filename:

                filename = filename.split(
                    "_",
                    1,
                )[1]

            resumes.append(
                ResumeItem(
                    resume_id=resume_id,
                    filename=filename,
                    s3_key=key,
                    size=obj.get("Size", 0),
                    last_modified=(
                        obj["LastModified"].isoformat()
                        if obj.get("LastModified")
                        else None
                    ),
                )
            )

        # Newest first.
        resumes.sort(
            key=lambda x: x.last_modified or "",
            reverse=True,
        )

        return ResumeListResponse(
            count=len(resumes),
            resumes=resumes,
        )

    except RuntimeError as error:

        logger.exception(
            "Failed to retrieve resumes"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.post(
    "/api/resumes/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...)
):

    filename = file.filename or ""

    extension = Path(
        filename
    ).suffix.lower()

    # --------------------------------------------------------
    # Extension
    # --------------------------------------------------------

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are allowed.",
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    content = await file.read()

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    if len(content) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Resume cannot exceed 10 MB.",
        )

    # --------------------------------------------------------
    # Generate ID
    # --------------------------------------------------------

    resume_id = uuid.uuid4().hex

    filename = safe_filename(
        filename
    )

    s3_key = (
        f"{RESUME_PREFIX}"
        f"{resume_id}_"
        f"{filename}"
    )

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    try:

        s3_service.upload_resume(
            BytesIO(content),
            s3_key,
        )

        logger.info(
            "Resume uploaded: %s",
            s3_key,
        )

        return UploadResponse(
            message="Resume uploaded successfully.",
            resume_id=resume_id,
            filename=filename,
            size=len(content),
        )

    except RuntimeError as error:

        logger.exception(
            "Resume upload failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# GET SINGLE RESUME
# ============================================================

@app.get(
    "/api/resumes/{resume_id}"
)
async def get_resume(
    resume_id: str
):

    resume = find_resume_by_id(
        resume_id
    )

    return resume


# ============================================================
# DELETE RESUME
# ============================================================

@app.delete(
    "/api/resumes/{resume_id}"
)
async def delete_resume(
    resume_id: str
):

    resume = find_resume_by_id(
        resume_id
    )

    try:

        s3_service.delete_object(
            resume["s3_key"]
        )

        logger.info(
            "Resume deleted: %s",
            resume["s3_key"],
        )

        return {
            "message": "Resume deleted successfully.",
            "resume_id": resume_id,
        }

    except RuntimeError as error:

        logger.exception(
            "Resume deletion failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# RANK RESUMES
# ============================================================

@app.post(
    "/api/ranking"
)
async def rank_resumes(
    payload: RankingRequest
):

    job_description = (
        payload.job_description.strip()
    )

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty.",
        )

    if not payload.resume_ids:

        raise HTTPException(
            status_code=400,
            detail="Select at least one resume.",
        )

    logger.info(
        "Ranking %s resumes",
        len(payload.resume_ids),
    )

    resumes = []

    # --------------------------------------------------------
    # Retrieve selected resumes
    # --------------------------------------------------------

    for resume_id in payload.resume_ids:

        resume = find_resume_by_id(
            resume_id
        )

        try:

            pdf_bytes = (
                s3_service.get_object_bytes(
                    resume["s3_key"]
                )
            )

            text = extract_text_from_pdf(
                BytesIO(pdf_bytes)
            )

            if not text.strip():

                logger.warning(
                    "No text extracted from %s",
                    resume["filename"],
                )

                continue

            resumes.append(
                {
                    "id": resume["resume_id"],
                    "name": resume["filename"],
                    "text": text,
                }
            )

        except Exception as error:

            logger.exception(
                "Failed processing %s",
                resume["filename"],
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Failed to process "
                    f"{resume['filename']}: {error}"
                ),
            )

    if not resumes:

        raise HTTPException(
            status_code=400,
            detail="No readable resumes were found.",
        )

    # --------------------------------------------------------
    # LangGraph
    # --------------------------------------------------------

    try:

        result = ranking_graph.invoke(
            {
                "job_description": job_description,
                "resumes": resumes,
            }
        )

        ranked = result.get(
            "ranked"
        )

        if ranked is None:

            raise RuntimeError(
                "Ranking engine returned no results."
            )

        # Pandas DataFrame -> JSON
        if hasattr(
            ranked,
            "to_dict",
        ):

            ranking_results = ranked.to_dict(
                orient="records"
            )

        else:

            ranking_results = ranked

        return {
            "success": True,
            "total_resumes": len(resumes),
            "results": ranking_results,
        }

    except HTTPException:
        raise

    except Exception as error:

        logger.exception(
            "Ranking failed"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Ranking failed: {error}",
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )