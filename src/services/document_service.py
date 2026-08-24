from io import BytesIO

import docx2txt
import fitz


class DocumentService:
    """Extract text from supported resume documents."""

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
    }

    def extract_text(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> str:
        """
        Extract text from PDF or DOCX.

        Raises:
            ValueError: If the format is unsupported or
                       text extraction fails.
        """

        extension = self._get_extension(filename)

        if extension == ".pdf":
            text = self._extract_pdf(file_bytes)

        elif extension == ".docx":
            text = self._extract_docx(file_bytes)

        else:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                "Only PDF and DOCX are supported."
            )

        text = self._clean_text(text)

        if len(text) < 50:
            raise ValueError(
                "The uploaded document does not contain "
                "enough readable text."
            )

        return text

    def _extract_pdf(self, file_bytes: bytes) -> str:
        try:
            document = fitz.open(
                stream=file_bytes,
                filetype="pdf",
            )

            pages = [
                page.get_text()
                for page in document
            ]

            document.close()

            return "\n".join(pages)

        except Exception as error:
            raise ValueError(
                "Unable to read the PDF document."
            ) from error

    def _extract_docx(self, file_bytes: bytes) -> str:
        try:
            return docx2txt.process(
                BytesIO(file_bytes)
            )

        except Exception as error:
            raise ValueError(
                "Unable to read the DOCX document."
            ) from error

    @staticmethod
    def _get_extension(filename: str) -> str:
        filename = filename.lower().strip()

        if "." not in filename:
            raise ValueError(
                "Uploaded file has no extension."
            )

        return "." + filename.rsplit(".", 1)[-1]

    @staticmethod
    def _clean_text(text: str) -> str:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return "\n".join(lines)