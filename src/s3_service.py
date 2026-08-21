import os
import logging
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


class S3Service:
    """Service responsible for uploading files to AWS S3."""

    def __init__(self):
        load_dotenv(override=True)

        self.region = os.getenv("AWS_REGION")
        self.bucket = os.getenv("AWS_S3_BUCKET")

        if not self.region:
            logger.error("AWS_REGION is not configured.")
            raise ValueError("AWS_REGION is not configured.")

        if not self.bucket:
            logger.error("AWS_S3_BUCKET is not configured.")
            raise ValueError("AWS_S3_BUCKET is not configured.")

        logger.info(
            "Initializing S3 service | bucket=%s | region=%s",
            self.bucket,
            self.region,
        )

        self.s3 = boto3.client(
            "s3",
            region_name=self.region,
        )

        logger.info("S3 client initialized successfully.")

    def upload_file(self, file_path: str, s3_key: str) -> bool:
        """Upload a single file to S3."""

        file = Path(file_path)

        if not file.exists():
            logger.error("File not found: %s", file)
            return False

        if not file.is_file():
            logger.error("Path is not a file: %s", file)
            return False

        try:
            logger.info(
                "Uploading file | file=%s | s3_key=%s",
                file.name,
                s3_key,
            )

            self.s3.upload_file(
                str(file),
                self.bucket,
                s3_key,
            )

            logger.info(
                "Upload successful | file=%s | s3_key=%s",
                file.name,
                s3_key,
            )

            print(f"✅ Uploaded: {file.name}")
            print(f"   → s3://{self.bucket}/{s3_key}")

            return True

        except (ClientError, BotoCoreError):
            logger.exception(
                "Upload failed | file=%s | s3_key=%s",
                file.name,
                s3_key,
            )

            print(f"❌ Failed to upload: {file.name}")

            return False

    def upload_folder(
        self,
        folder_path: str,
        s3_prefix: str = "resumes/",
    ) -> None:
        """Upload supported resume files from a folder."""

        folder = Path(folder_path)

        if not folder.exists():
            logger.error("Resume folder does not exist: %s", folder)
            raise FileNotFoundError(
                f"Folder does not exist: {folder}"
            )

        if not folder.is_dir():
            logger.error("Resume path is not a directory: %s", folder)
            raise NotADirectoryError(
                f"Path is not a directory: {folder}"
            )

        allowed_extensions = {
            ".pdf",
            ".docx",
            ".doc",
        }

        files = [
            file
            for file in folder.iterdir()
            if file.is_file()
            and file.suffix.lower() in allowed_extensions
        ]

        if not files:
            logger.warning(
                "No supported resume files found in: %s",
                folder,
            )

            print("⚠️ No resume files found.")
            return

        logger.info(
            "Found %d resume files in %s",
            len(files),
            folder,
        )

        print(f"Found {len(files)} resume(s).\n")

        successful = 0
        failed = 0

        for file in files:

            s3_key = (
                f"{s3_prefix.rstrip('/')}/{file.name}"
            )

            success = self.upload_file(
                file_path=str(file),
                s3_key=s3_key,
            )

            if success:
                successful += 1
            else:
                failed += 1

        logger.info(
            "Upload process completed | total=%d | successful=%d | failed=%d",
            len(files),
            successful,
            failed,
        )

        print("\n" + "=" * 50)
        print("UPLOAD SUMMARY")
        print("=" * 50)
        print(f"Total files : {len(files)}")
        print(f"Successful  : {successful}")
        print(f"Failed      : {failed}")
        print("=" * 50)