import json
import os
from io import BytesIO
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


load_dotenv(override=True)


class S3Service:
    """
    AWS S3 service for Resume Dangal.
    """

    def __init__(self):

        self.region = os.getenv(
            "AWS_REGION"
        )

        self.bucket = os.getenv(
            "AWS_S3_BUCKET"
        )

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

        try:

            self.s3.upload_fileobj(
                file,
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/pdf"
                },
            )

            return s3_key

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise RuntimeError(
                f"Failed to upload resume: {error}"
            ) from error

    # ========================================================
    # Get Object Bytes
    # ========================================================

    def get_object_bytes(
        self,
        s3_key: str,
    ) -> bytes:

        try:

            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=s3_key,
            )

            return response[
                "Body"
            ].read()

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise RuntimeError(
                f"Failed to retrieve object: {error}"
            ) from error

    # ========================================================
    # List Objects
    # ========================================================

    def list_objects(
        self,
        prefix: str,
    ) -> list[dict[str, Any]]:

        try:

            objects = []

            paginator = (
                self.s3.get_paginator(
                    "list_objects_v2"
                )
            )

            for page in paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix,
            ):

                objects.extend(
                    page.get(
                        "Contents",
                        [],
                    )
                )

            return objects

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise RuntimeError(
                f"Failed to list S3 objects: {error}"
            ) from error

    # ========================================================
    # Delete
    # ========================================================

    def delete_object(
        self,
        s3_key: str,
    ) -> None:

        try:

            self.s3.delete_object(
                Bucket=self.bucket,
                Key=s3_key,
            )

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise RuntimeError(
                f"Failed to delete object: {error}"
            ) from error

    # ========================================================
    # JSON Upload
    # ========================================================

    def upload_json(
        self,
        data: dict,
        s3_key: str,
    ) -> str:

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
                    "ContentType": "application/json"
                },
            )

            return s3_key

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise RuntimeError(
                f"Failed to upload JSON: {error}"
            ) from error