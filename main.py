import os
import logging

import boto3
import streamlit as st
from botocore.exceptions import ClientError
from dotenv import load_dotenv


# ============================================================
# Configuration
# ============================================================

load_dotenv(override=True)

AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET")

S3_PREFIX = "resumes/"


# ============================================================
# Logging
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Resume Dangal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Custom CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .main {
        padding-top: 1rem;
    }

    /* Remove Streamlit top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* Application title */
    .app-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .app-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    /* Panel */
    .panel {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 20px;
        min-height: 580px;
        background-color: #ffffff;
    }

    /* Panel headings */
    .panel-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 18px;
    }

    /* Resume count */
    .resume-count {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin: 10px 0 20px 0;
    }

    /* Resume item */
    .resume-item {
        padding: 10px;
        border-bottom: 1px solid #eeeeee;
        font-size: 14px;
    }

    /* Chat area */
    .chat-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 15px;
        margin-top: 20px;
        min-height: 220px;
    }

    /* Job description */
    .job-description {
        margin-top: 10px;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# S3 Client
# ============================================================

@st.cache_resource
def get_s3_client():
    logger.info("Creating S3 client.")

    return boto3.client(
        "s3",
        region_name=AWS_REGION,
    )


s3 = get_s3_client()


# ============================================================
# S3 Functions
# ============================================================

def get_resumes():
    """Return all resumes stored inside the resumes/ prefix."""

    try:

        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=S3_PREFIX,
        )

        objects = response.get("Contents", [])

        return [
            obj
            for obj in objects
            if obj["Key"] != S3_PREFIX
        ]

    except ClientError:

        logger.exception(
            "Failed to retrieve resumes."
        )

        st.error(
            "Unable to retrieve resumes from S3."
        )

        return []


def upload_resume(uploaded_file):
    """Upload a resume to S3."""

    try:

        s3_key = (
            f"{S3_PREFIX}{uploaded_file.name}"
        )

        s3.upload_fileobj(
            uploaded_file,
            BUCKET_NAME,
            s3_key,
        )

        logger.info(
            "Resume uploaded successfully: %s",
            uploaded_file.name,
        )

        return True

    except ClientError:

        logger.exception(
            "Failed to upload resume: %s",
            uploaded_file.name,
        )

        return False


def delete_resume(s3_key):
    """Delete a resume from S3."""

    try:

        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
        )

        logger.info(
            "Resume deleted successfully: %s",
            s3_key,
        )

        return True

    except ClientError:

        logger.exception(
            "Failed to delete resume: %s",
            s3_key,
        )

        return False


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="app-title">Resume Dangal</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-subtitle">'
    'AI-powered resume screening workspace'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# Load Resumes
# ============================================================

resumes = get_resumes()


# ============================================================
# Main Three-Column Layout
# ============================================================

left, center, right = st.columns(
    [1.2, 3.2, 1.5],
    gap="medium",
)


# ============================================================
# LEFT PANEL — UPLOAD RESUME
# ============================================================

with left:

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel-title">'
        '📤 Upload Resume'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Upload candidate resumes here."
    )

    uploaded_file = st.file_uploader(
        "Choose resume",
        type=["pdf", "doc", "docx"],
        label_visibility="collapsed",
    )

    if uploaded_file:

        st.success(
            f"Selected: {uploaded_file.name}"
        )

        st.caption(
            f"Size: {uploaded_file.size / 1024:.2f} KB"
        )

        if st.button(
            "Upload Resume",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Uploading..."
            ):

                success = upload_resume(
                    uploaded_file
                )

            if success:

                st.success(
                    "Resume uploaded successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Upload failed."
                )

    st.divider()

    st.write(
        "**Supported formats**"
    )

    st.caption(
        "PDF • DOC • DOCX"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# CENTER PANEL — JOB DESCRIPTION + CHAT
# ============================================================

with center:

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel-title">'
        '🎯 Job Description'
        '</div>',
        unsafe_allow_html=True,
    )

    job_description = st.text_area(
        "Job Description",
        placeholder=(
            "Paste the job description here...\n\n"
            "Example:\n"
            "We are looking for an AI Engineer "
            "with experience in Python, "
            "LangChain, AWS and machine learning."
        ),
        height=170,
        label_visibility="collapsed",
    )

    if job_description:

        st.caption(
            f"{len(job_description)} characters"
        )

    st.divider()

    st.markdown(
        '<div class="panel-title">'
        '💬 Chat Interface'
        '</div>',
        unsafe_allow_html=True,
    )

    # Display chat history
    if "messages" not in st.session_state:

        st.session_state.messages = []

    chat_container = st.container(
        height=220
    )

    with chat_container:

        if not st.session_state.messages:

            st.info(
                "Ask something about the uploaded "
                "resumes or job description."
            )

        for message in st.session_state.messages:

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

    prompt = st.chat_input(
        "Ask Resume Dangal..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # Temporary response.
        # Replace this with LangGraph later.
        response = (
            "Your AI agent will process this "
            "question here."
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# RIGHT PANEL — RESUME LIST
# ============================================================

with right:

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel-title">'
        '📋 All Resumes'
        '</div>',
        unsafe_allow_html=True,
    )

    # Count
    st.markdown(
        f'<div class="resume-count">'
        f'{len(resumes)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Total uploaded resumes"
    )

    st.divider()

    if not resumes:

        st.info(
            "No resumes uploaded yet."
        )

    else:

        for index, resume in enumerate(
            resumes,
            start=1,
        ):

            filename = resume[
                "Key"
            ].replace(
                S3_PREFIX,
                "",
            )

            size_kb = (
                resume["Size"] / 1024
            )

            st.markdown(
                f"""
                <div class="resume-item">
                    <b>{index}. {filename}</b>
                    <br>
                    <small>{size_kb:.2f} KB</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Delete section
    if resumes:

        st.markdown(
            "**Delete Resume**"
        )

        resume_options = {
            obj["Key"].replace(
                S3_PREFIX,
                ""
            ): obj["Key"]
            for obj in resumes
        }

        selected_resume = st.selectbox(
            "Select resume",
            options=list(
                resume_options.keys()
            ),
            label_visibility="collapsed",
        )

        if st.button(
            "🗑️ Delete Selected",
            use_container_width=True,
        ):

            success = delete_resume(
                resume_options[
                    selected_resume
                ]
            )

            if success:

                st.success(
                    "Resume deleted."
                )

                st.rerun()

            else:

                st.error(
                    "Delete failed."
                )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )