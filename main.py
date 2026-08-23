import logging
import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, UploadFile
from pydantic import BaseModel

load_dotenv(override=True)

AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET")
S3_PREFIX = "resumes/"

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Dangal API",
    description="Backend API for managing and screening resumes",
    version="1.0.0",
)


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


# --- Response Schemas ---
class ResumeItem(BaseModel):
    Key: str
    Size: int


class ChatRequest(BaseModel):
    prompt: str
    job_description: str | None = None


class ChatResponse(BaseModel):
    response: str


# --- API Routes ---
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/resumes", response_model=List[ResumeItem])
async def list_resumes() -> List[Dict[str, Any]]:
    s3 = get_s3_client()
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_PREFIX)
        objects = response.get("Contents", [])
        return [obj for obj in objects if obj["Key"] != S3_PREFIX]
    except ClientError as e:
        logger.exception("Failed to retrieve resumes from S3.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 Error: {str(e)}",
        )


@app.post("/resumes/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile) -> Dict[str, str]:
    s3 = get_s3_client()
    s3_key = f"{S3_PREFIX}{file.filename}"
    try:
        s3.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        logger.info("Resume uploaded successfully: %s", file.filename)
        return {"message": f"Successfully uploaded {file.filename}"}
    except ClientError as e:
        logger.exception("Failed to upload resume: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload Error: {str(e)}",
        )


@app.delete("/resumes")
async def delete_resume(s3_key: str) -> Dict[str, str]:
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        logger.info("Resume deleted: %s", s3_key)
        return {"message": f"Successfully deleted {s3_key}"}
    except ClientError as e:
        logger.exception("Failed to delete resume: %s", s3_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete Error: {str(e)}",
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest) -> Dict[str, str]:
    # Placeholder for Agent logic integration (LangChain/LlamaIndex)
    logger.info("Processing chat prompt: %s", payload.prompt)
    return {"response": "Your AI agent will process this query."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)