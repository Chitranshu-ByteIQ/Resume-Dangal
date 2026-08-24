import logging
import os
import uuid
from functools import lru_cache
from io import BytesIO

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.extraction.jd_extractor import JobDescriptionExtractor
from src.extraction.resume_extractor import ResumeExtractor
from src.ranking.evaluator import RankingEvaluator
from src.ranking.retrieval import RankingRetriever
from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.schemas.ranking import RankingResponse
from src.services.s3_service import S3Service

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("resume-dangal")

app = FastAPI(
    title="Resume Dangal",
    description="AI-powered hybrid resume screening and ranking system.",
    version="2.0.0",
)


def _allowed_origins() -> list[str]:
    configured = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )

    return [
        origin.strip()
        for origin in configured.split(",")
        if origin.strip()
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobAnalyzeRequest(BaseModel):
    """Request body for Job Description analysis."""

    description: str = Field(
        ...,
        min_length=20,
        description="Raw Job Description text.",
    )


class CandidateResponse(BaseModel):
    """Response returned after resume processing."""

    message: str
    candidate: CandidateProfile


class JobResponse(BaseModel):
    """Response returned after JD processing."""

    message: str
    job: JobDescription


@lru_cache(maxsize=1)
def get_s3_service() -> S3Service:
    return S3Service()


def get_resume_extractor() -> ResumeExtractor:
    return ResumeExtractor()


def get_jd_extractor() -> JobDescriptionExtractor:
    return JobDescriptionExtractor()


def get_ranking_retriever() -> RankingRetriever:
    return RankingRetriever(
        s3_service=get_s3_service(),
    )


def get_ranking_evaluator() -> RankingEvaluator:
    return RankingEvaluator()


def _service_exception(
    error: Exception,
    fallback: str,
) -> HTTPException:
    message = str(error) or fallback
    lower_message = message.lower()

    if "configured" in lower_message or "credentials" in lower_message:
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return HTTPException(
        status_code=code,
        detail=message,
    )


def _file_extension(filename: str) -> str:
    sanitized = os.path.basename(filename.strip())
    extension = os.path.splitext(sanitized.lower())[1]

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid resume format. "
                "Only PDF and DOCX files are supported."
            ),
        )

    return extension


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "resume-dangal",
        "version": "2.0.0",
    }


@app.post(
    "/resumes/upload",
    response_model=CandidateResponse,
)
async def upload_resume(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was provided.",
        )

    filename = os.path.basename(file.filename.strip())
    extension = _file_extension(filename)

    try:
        file_bytes = await file.read()
    except Exception as error:
        logger.exception("Unable to read uploaded file.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read the uploaded file.",
        ) from error

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid resume: the uploaded file is empty.",
        )

    max_file_size = 10 * 1024 * 1024

    if len(file_bytes) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Resume file is too large. "
                "Maximum allowed size is 10 MB."
            ),
        )

    candidate_id = str(uuid.uuid4())

    try:
        candidate = get_resume_extractor().extract(
            file_bytes=file_bytes,
            filename=filename,
            candidate_id=candidate_id,
        )

        resume_key = f"resumes/{candidate_id}/original{extension}"
        profile_key = f"resumes/{candidate_id}/profile.json"

        candidate = candidate.model_copy(
            update={
                "resume_file": resume_key,
            }
        )

        s3_service = get_s3_service()
        s3_service.upload_resume(
            file=BytesIO(file_bytes),
            s3_key=resume_key,
        )
        s3_service.upload_json(
            data=candidate.model_dump(mode="json"),
            s3_key=profile_key,
        )

        logger.info(
            "Resume processed successfully: %s",
            candidate_id,
        )

        return CandidateResponse(
            message="Resume processed successfully.",
            candidate=candidate,
        )

    except ValueError as error:
        detail = str(error)

        if not detail.lower().startswith("invalid resume"):
            detail = f"Invalid resume: {detail}"

        logger.warning("Resume rejected: %s", detail)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        ) from error

    except Exception as error:
        logger.exception("Unexpected resume processing error.")
        raise _service_exception(
            error,
            "An unexpected error occurred while processing the resume.",
        ) from error


@app.get(
    "/resumes",
    response_model=list[CandidateProfile],
)
async def get_resumes():
    try:
        return get_ranking_retriever().get_all_candidates()
    except Exception as error:
        logger.exception("Failed to retrieve resumes.")
        raise _service_exception(
            error,
            "Unable to retrieve resumes.",
        ) from error


@app.delete("/resumes/{candidate_id}")
async def delete_resume(
    candidate_id: str,
):
    prefix = f"resumes/{candidate_id}/"

    try:
        deleted_count = get_s3_service().delete_prefix(prefix)

        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        return {
            "message": "Resume deleted successfully.",
            "candidate_id": candidate_id,
            "deleted_objects": deleted_count,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Failed to delete resume.")
        raise _service_exception(
            error,
            "Unable to delete resume.",
        ) from error


@app.post(
    "/jobs/analyze",
    response_model=JobResponse,
)
async def analyze_job(
    request: JobAnalyzeRequest,
):
    try:
        job_id = str(uuid.uuid4())
        job = get_jd_extractor().extract(
            text=request.description,
            job_id=job_id,
        )

        jd_key = f"jobs/{job_id}/jd.json"

        get_s3_service().upload_json(
            data=job.model_dump(mode="json"),
            s3_key=jd_key,
        )

        logger.info("Job Description processed: %s", job_id)

        return JobResponse(
            message="Job Description analyzed successfully.",
            job=job,
        )

    except ValueError as error:
        logger.warning("Invalid Job Description: %s", error)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to analyze Job Description.")
        raise _service_exception(
            error,
            "An unexpected error occurred while analyzing the Job Description.",
        ) from error


@app.get(
    "/jobs/{job_id}",
    response_model=JobDescription,
)
async def get_job(
    job_id: str,
):
    try:
        return get_ranking_retriever().get_job(job_id)
    except Exception as error:
        logger.exception("Job not found: %s", job_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        ) from error


@app.post(
    "/jobs/{job_id}/rank",
    response_model=RankingResponse,
)
async def rank_candidates(
    job_id: str,
):
    try:
        ranking_retriever = get_ranking_retriever()
        job = ranking_retriever.get_job(job_id)
        candidates = ranking_retriever.get_all_candidates()

        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No processed resumes found. "
                    "Upload at least one valid resume first."
                ),
            )

        ranking_result = get_ranking_evaluator().evaluate(
            job=job,
            candidates=candidates,
        )

        logger.info(
            "Ranking completed for job %s. Candidates: %d",
            job_id,
            len(candidates),
        )

        return ranking_result

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Candidate ranking failed.")
        raise _service_exception(
            error,
            "Unable to rank candidates. Check the server logs for details.",
        ) from error
