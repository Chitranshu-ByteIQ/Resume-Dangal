import json
import os
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


load_dotenv(override=True)


class S3Service:
    """Service responsible for Resume Dangal S3 operations."""

    def __init__(self):
        self.region = os.getenv("AWS_REGION")
        self.bucket = os.getenv("AWS_S3_BUCKET")

        if not self.region:
            raise ValueError(
                "AWS_REGION is not configured."
            )

        if not self.bucket:
            raise ValueError(
                "AWS_S3_BUCKET is not configured."
            )

        self.s3 = boto3.client(
            "s3",
            region_name=self.region,
        )

    # ========================================================
    # Upload Resume
    # ========================================================

    def upload_resume(
        self,
        file,
        s3_key: str,
    ) -> str:
        """
        Upload resume file to S3.

        Returns:
            S3 key of uploaded resume.
        """

        try:
            self.s3.upload_fileobj(
                file,
                self.bucket,
                s3_key,
            )

            return s3_key

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to upload resume: {error}"
            ) from error

    # ========================================================
    # Upload JSON
    # ========================================================

    def upload_json(
        self,
        data: dict,
        s3_key: str,
    ) -> str:
        """
        Upload a Python dictionary as JSON to S3.

        Returns:
            S3 key of uploaded JSON.
        """

        try:
            body = json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8")

            self.s3.upload_fileobj(
                BytesIO(body),
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/json",
                },
            )

            return s3_key

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to upload JSON: {error}"
            ) from error

    # ========================================================
    # Get JSON
    # ========================================================

    def get_json(
        self,
        s3_key: str,
    ) -> dict:
        """
        Download JSON from S3 and return it as a dictionary.
        """

        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=s3_key,
            )

            content = response[
                "Body"
            ].read().decode("utf-8")

            return json.loads(content)

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to download JSON: {error}"
            ) from error

        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Invalid JSON in S3 object: {error}"
            ) from error

    # ========================================================
    # List Objects
    # ========================================================

    def list_objects(
        self,
        prefix: str,
    ) -> list[dict]:
        """
        List objects under an S3 prefix.
        """

        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
            )

            return response.get(
                "Contents",
                [],
            )

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to list S3 objects: {error}"
            ) from error

    # ========================================================
    # Delete Object
    # ========================================================

    def delete_object(
        self,
        s3_key: str,
    ) -> None:
        """
        Delete an object from S3.
        """

        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=s3_key,
            )

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to delete S3 object: {error}"
            ) from error

    # ========================================================
    # Delete Prefix
    # ========================================================

    def delete_prefix(
        self,
        prefix: str,
    ) -> int:
        """
        Delete all objects under an S3 prefix.

        Returns:
            Number of deleted objects.
        """

        objects = self.list_objects(prefix)

        if not objects:
            return 0

        delete_objects = [
            {
                "Key": obj["Key"]
            }
            for obj in objects
        ]

        try:
            self.s3.delete_objects(
                Bucket=self.bucket,
                Delete={
                    "Objects": delete_objects,
                },
            )

            return len(delete_objects)

        except (ClientError, BotoCoreError) as error:
            raise RuntimeError(
                f"Failed to delete S3 prefix: {error}"
            ) from error