# s3_service.py

from __future__ import annotations

import json
import os
from io import BytesIO
from typing import Any, BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


load_dotenv(override=True)


class S3ServiceError(RuntimeError):
    pass


class S3ObjectNotFound(S3ServiceError):
    pass


class S3InvalidJSON(S3ServiceError):
    pass


class S3Service:

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
    # UPLOAD FILE
    # ========================================================

    def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str,
    ) -> str:

        try:

            self.s3.upload_fileobj(
                file,
                self.bucket,
                key,
                ExtraArgs={
                    "ContentType": content_type
                },
            )

            return key

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise S3ServiceError(
                f"S3 upload failed: {error}"
            ) from error

    # ========================================================
    # UPLOAD JSON
    # ========================================================

    def upload_json(
        self,
        data: dict[str, Any],
        key: str,
    ) -> str:

        body = json.dumps(
            data,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

        return self.upload(
            BytesIO(body),
            key,
            "application/json",
        )

    # ========================================================
    # GET JSON
    # ========================================================

    def get_json(
        self,
        key: str,
    ) -> dict[str, Any]:

        try:

            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=key,
            )

            content = response["Body"].read()

            return json.loads(
                content.decode("utf-8")
            )

        except ClientError as error:

            if self._is_not_found(error):
                raise S3ObjectNotFound(key) from error

            raise S3ServiceError(
                f"S3 read failed: {error}"
            ) from error

        except (
            BotoCoreError,
            UnicodeDecodeError,
        ) as error:

            raise S3ServiceError(
                f"Failed to read S3 JSON: {error}"
            ) from error

        except json.JSONDecodeError as error:

            raise S3InvalidJSON(
                f"Invalid JSON in S3 object {key}: {error}"
            ) from error

    # ========================================================
    # LIST OBJECTS
    # ========================================================

    def list_objects(
        self,
        prefix: str,
    ) -> list[dict[str, Any]]:

        try:

            objects = []

            paginator = self.s3.get_paginator(
                "list_objects_v2"
            )

            for page in paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix,
            ):

                objects.extend(
                    page.get("Contents", [])
                )

            return objects

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise S3ServiceError(
                f"S3 list failed: {error}"
            ) from error

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        key: str,
    ) -> bool:

        try:

            self.s3.head_object(
                Bucket=self.bucket,
                Key=key,
            )

            return True

        except ClientError as error:

            if self._is_not_found(error):
                return False

            raise S3ServiceError(
                f"S3 head failed: {error}"
            ) from error

        except BotoCoreError as error:

            raise S3ServiceError(
                f"S3 head failed: {error}"
            ) from error

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        key: str,
    ) -> None:

        try:

            self.s3.delete_object(
                Bucket=self.bucket,
                Key=key,
            )

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise S3ServiceError(
                f"S3 delete failed: {error}"
            ) from error

    # ========================================================
    # DOWNLOAD URL
    # ========================================================

    def download_url(
        self,
        key: str,
        expires: int = 3600,
    ) -> str:

        try:

            return self.s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                },
                ExpiresIn=expires,
            )

        except (
            ClientError,
            BotoCoreError,
        ) as error:

            raise S3ServiceError(
                f"Failed to create download URL: {error}"
            ) from error

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _is_not_found(
        error: ClientError,
    ) -> bool:

        error_code = (
            error.response
            .get("Error", {})
            .get("Code")
        )

        return error_code in {
            "NoSuchKey",
            "404",
            "NotFound",
        }
