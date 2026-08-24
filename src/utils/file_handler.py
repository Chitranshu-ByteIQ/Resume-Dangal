from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(
    uploaded_file,
) -> str:
    """
    Extract text from a PDF file.

    uploaded_file can be:
    - BytesIO
    - file object
    - binary stream
    """

    try:

        if isinstance(
            uploaded_file,
            bytes,
        ):

            uploaded_file = BytesIO(
                uploaded_file
            )

        reader = PdfReader(
            uploaded_file
        )

        pages = []

        for page in reader.pages:

            page_text = (
                page.extract_text()
            )

            if page_text:

                pages.append(
                    page_text
                )

        return "\n".join(
            pages
        ).strip()

    except Exception as error:

        raise RuntimeError(
            f"Failed to extract PDF text: {error}"
        ) from error