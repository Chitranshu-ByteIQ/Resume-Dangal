import json
import os
import shutil
import logging
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger("resume-dangal.s3-service")


class S3Service:
    """Service responsible for Resume Dangal S3 operations with local fallback."""

    def __init__(self):
        self.region = os.getenv("AWS_REGION")
        self.bucket = os.getenv("AWS_S3_BUCKET")

        if not self.region:
            raise ValueError("AWS_REGION is not configured.")

        if not self.bucket:
            raise ValueError("AWS_S3_BUCKET is not configured.")

        self.s3 = boto3.client(
            "s3",
            region_name=self.region,
        )

        # Initialize local fallback directory under workspace root
        self.local_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "local_s3_fallback"
            )
        )
        os.makedirs(self.local_dir, exist_ok=True)
        logger.info("S3 Service initialized. Local fallback cache at: %s", self.local_dir)

    def _local_path(self, s3_key: str) -> str:
        """Get safe absolute local path preventing path traversal."""
        clean_key = s3_key.replace("\\", "/").lstrip("/")
        parts = clean_key.split("/")
        safe_parts = [p for p in parts if p and p != ".."]
        target_path = os.path.abspath(os.path.join(self.local_dir, *safe_parts))
        if not target_path.startswith(self.local_dir):
            raise ValueError(f"Path traversal detected: {s3_key}")
        return target_path

    def upload_resume(self, file, s3_key: str) -> str:
        """Upload original resume file to S3 with local cache write."""
        # 1. Mirror locally first
        local_path = self._local_path(s3_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        try:
            file.seek(0)
            with open(local_path, "wb") as f:
                shutil.copyfileobj(file, f)
            logger.info("Saved resume locally: %s", local_path)
        except Exception as err:
            logger.error("Failed to write resume to local cache: %s", err)

        # 2. Try uploading to S3
        try:
            file.seek(0)
            self.s3.upload_fileobj(
                file,
                self.bucket,
                s3_key,
            )
            logger.info("Uploaded resume to S3: %s", s3_key)
            return s3_key
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 upload failed, using local copy. Error: %s", error)
            return s3_key

    def upload_json(self, data: dict, s3_key: str) -> str:
        """Upload structured JSON data to S3 with local cache write."""
        # 1. Mirror locally first
        local_path = self._local_path(s3_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        try:
            body = json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(body)
            logger.info("Saved JSON locally: %s", local_path)
        except Exception as err:
            logger.error("Failed to write JSON to local cache: %s", err)

        # 2. Try uploading to S3
        try:
            body_bytes = json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8")
            self.s3.upload_fileobj(
                BytesIO(body_bytes),
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/json",
                },
            )
            logger.info("Uploaded JSON to S3: %s", s3_key)
            return s3_key
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 JSON upload failed, using local copy. Error: %s", error)
            return s3_key

    def get_json(self, s3_key: str) -> dict:
        """Download JSON from S3, falling back to local cache on failure."""
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=s3_key,
            )
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 get_object failed for %s. Attempting local fallback. Error: %s", s3_key, error)
            local_path = self._local_path(s3_key)
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            raise RuntimeError(
                f"Failed to download JSON from S3 and local cache does not exist for: {s3_key}"
            ) from error
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Invalid JSON in S3 object: {error}"
            ) from error

    def list_objects(self, prefix: str) -> list[dict]:
        """List objects under an S3 prefix, falling back to local directory listing on failure."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
            )
            return response.get("Contents", [])
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 list_objects failed for prefix %s. Attempting local fallback. Error: %s", prefix, error)
            local_prefix_path = self._local_path(prefix)
            if not os.path.exists(local_prefix_path):
                return []
            
            contents = []
            for root, _, files in os.walk(local_prefix_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Convert absolute path back to relative S3 key format
                    rel_path = os.path.relpath(full_path, self.local_dir)
                    s3_key = rel_path.replace("\\", "/")
                    contents.append({"Key": s3_key})
            return contents

    def delete_object(self, s3_key: str) -> None:
        """Delete one S3 object and clean local copy."""
        # 1. Clean local first
        try:
            local_path = self._local_path(s3_key)
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("Deleted local copy: %s", local_path)
        except Exception as err:
            logger.error("Failed to delete local copy: %s", err)

        # 2. Try deleting from S3
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=s3_key,
            )
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 delete_object failed. Error: %s", error)

    def delete_prefix(self, prefix: str) -> int:
        """Delete all objects under a prefix from S3 and local cache."""
        # Get list from S3 or local cache first
        objects = self.list_objects(prefix)
        if not objects:
            return 0

        # Delete local copies first
        deleted_count = 0
        for obj in objects:
            key = obj["Key"]
            try:
                local_path = self._local_path(key)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    deleted_count += 1
            except Exception as err:
                logger.error("Failed to delete local copy for %s: %s", key, err)

        # Delete S3 objects
        try:
            delete_objects = [{"Key": obj["Key"]} for obj in objects]
            self.s3.delete_objects(
                Bucket=self.bucket,
                Delete={
                    "Objects": delete_objects,
                },
            )
            logger.info("Deleted S3 prefix: %s", prefix)
        except (ClientError, BotoCoreError) as error:
            logger.warning("S3 delete_objects prefix failed. Error: %s", error)

        # Also clean up any empty directories locally
        try:
            local_prefix_path = self._local_path(prefix)
            if os.path.exists(local_prefix_path):
                shutil.rmtree(local_prefix_path)
        except Exception as err:
            logger.error("Failed to clean local prefix directory: %s", err)

        return len(objects)