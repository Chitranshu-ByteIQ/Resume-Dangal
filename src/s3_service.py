import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


class S3Service:
    """Service responsible for uploading files to AWS S3."""

    def __init__(self):
        load_dotenv(override=True)

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

    def upload_file(self, file_path: str, s3_key: str) -> bool:
        """
        Upload a single file to S3.

        Args:
            file_path: Local path of the file.
            s3_key: Destination key inside the S3 bucket.

        Returns:
            True if upload succeeds, otherwise False.
        """

        file = Path(file_path)

        if not file.exists():
            print(f"❌ File not found: {file}")
            return False

        if not file.is_file():
            print(f"❌ Not a file: {file}")
            return False

        try:
            self.s3.upload_file(
                str(file),
                self.bucket,
                s3_key,
            )

            print(f"✅ Uploaded: {file.name}")
            print(f"   → s3://{self.bucket}/{s3_key}")

            return True

        except (ClientError, BotoCoreError) as error:
            print(f"❌ Failed to upload {file.name}")
            print(f"   Error: {error}")

            return False

    def upload_folder(
        self,
        folder_path: str,
        s3_prefix: str = "resumes/",
    ) -> None:
        """
        Upload all supported resume files from a local folder.

        Supported formats:
        PDF, DOCX, DOC
        """

        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(
                f"Folder does not exist: {folder}"
            )

        if not folder.is_dir():
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
            print("⚠️ No resume files found.")
            return

        print(f"Found {len(files)} resume(s).\n")

        successful = 0
        failed = 0

        for file in files:

            # Example:
            # resumes/rahul_resume.pdf
            s3_key = f"{s3_prefix.rstrip('/')}/{file.name}"

            success = self.upload_file(
                file_path=str(file),
                s3_key=s3_key,
            )

            if success:
                successful += 1
            else:
                failed += 1

        print("\n" + "=" * 50)
        print("UPLOAD SUMMARY")
        print("=" * 50)
        print(f"Total files : {len(files)}")
        print(f"Successful  : {successful}")
        print(f"Failed      : {failed}")
        print("=" * 50)