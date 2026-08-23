import os
import logging
import boto3
import streamlit as st
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# ============================================================
# Configuration & Setup
# ============================================================

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

# Page Setup
st.set_page_config(
    page_title="Resume Dangal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Manage Theme State
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

# ============================================================
# Dynamic CSS Injection (Light/Dark Mode Support)
# ============================================================

def apply_theme_css():
    if st.session_state.theme == "Dark":
        bg_color = "#0E1117"
        card_bg = "#161B22"
        border_color = "#30363D"
        text_color = "#C9D1D9"
        text_muted = "#8B949E"
        input_bg = "#0D1117"
    else:
        bg_color = "#FFFFFF"
        card_bg = "#F8F9FA"
        border_color = "#E9ECEF"
        text_color = "#212529"
        text_muted = "#6C757D"
        input_bg = "#FFFFFF"

    css = f"""
    <style>
    [data-testid="stHeader"] {{ display: none; }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1400px; }}
    
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    
    /* Application Titles */
    .app-title {{
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 2px;
        color: {text_color};
    }}
    .app-subtitle {{
        font-size: 15px;
        color: {text_muted};
        margin-bottom: 15px;
    }}
    
    /* Visual Cards (Replaces empty container HTML boxes) */
    .content-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    
    .resume-count {{
        font-size: 36px;
        font-weight: 800;
        text-align: center;
        color: {text_color};
        margin: 5px 0;
    }}
    
    .resume-item {{
        padding: 8px 0;
        border-bottom: 1px solid {border_color};
        font-size: 13px;
        color: {text_color};
    }}
    
    /* Custom input overrides */
    .stTextArea textarea, .stTextInput input {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme_css()

# ============================================================
# S3 Service Backend
# ============================================================

@st.cache_resource
def get_s3_client():
    logger.info("Creating S3 client.")
    return boto3.client("s3", region_name=AWS_REGION)

s3 = get_s3_client()

def get_resumes():
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_PREFIX)
        objects = response.get("Contents", [])
        return [obj for obj in objects if obj["Key"] != S3_PREFIX]
    except ClientError:
        logger.exception("Failed to retrieve resumes.")
        st.error("Unable to retrieve resumes from S3.")
        return []

def upload_resume(uploaded_file):
    try:
        s3_key = f"{S3_PREFIX}{uploaded_file.name}"
        s3.upload_fileobj(uploaded_file, BUCKET_NAME, s3_key)
        logger.info("Resume uploaded: %s", uploaded_file.name)
        return True
    except ClientError:
        logger.exception("Failed to upload resume: %s", uploaded_file.name)
        return False

def delete_resume(s3_key):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        logger.info("Resume deleted: %s", s3_key)
        return True
    except ClientError:
        logger.exception("Failed to delete resume: %s", s3_key)
        return False

# ============================================================
# Top Bar Header & Theme Selector
# ============================================================

header_left, header_right = st.columns([0.82, 0.18])

with header_left:
    st.markdown('<div class="app-title">Resume Dangal</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">AI-powered resume screening workspace</div>', unsafe_allow_html=True)

with header_right:
    selected_theme = st.selectbox(
        "Theme Mode",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1,
        key="theme_selector_dropdown"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

st.divider()

# Load Resumes Data
resumes = get_resumes()

# ============================================================
# Main 3-Column Workspace Layout
# ============================================================

left, center, right = st.columns([1.2, 3.2, 1.5], gap="medium")

# ------------------------------------------------------------
# LEFT PANEL — RESUME UPLOAD
# ------------------------------------------------------------
with left:
    st.subheader("📤 Upload Resume")
    st.caption("Upload candidate resumes here.")

    uploaded_file = st.file_uploader(
        "Choose resume",
        type=["pdf", "doc", "docx"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.success(f"Selected: {uploaded_file.name}")
        st.caption(f"Size: {uploaded_file.size / 1024:.2f} KB")

        if st.button("Upload Resume", type="primary", use_container_width=True):
            with st.spinner("Uploading..."):
                success = upload_resume(uploaded_file)
            if success:
                st.success("Resume uploaded successfully.")
                st.rerun()
            else:
                st.error("Upload failed.")

    st.divider()
    st.markdown("**Supported formats:**")
    st.caption("PDF • DOC • DOCX")

# ------------------------------------------------------------
# CENTER PANEL — JOB DESCRIPTION & CHAT INTERFACE
# ------------------------------------------------------------
with center:
    st.subheader("🎯 Job Description")
    job_description = st.text_area(
        "Job Description Input",
        placeholder=(
            "Paste the job description here...\n\n"
            "Example:\n"
            "We are looking for an AI Engineer with experience in Python, "
            "LangChain, AWS, and machine learning."
        ),
        height=170,
        label_visibility="collapsed",
    )

    if job_description:
        st.caption(f"{len(job_description)} characters")

    st.divider()

    st.subheader("💬 Chat Interface")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container(height=240)

    with chat_container:
        if not st.session_state.messages:
            st.info("Ask something about the uploaded resumes or job description.")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    prompt = st.chat_input("Ask Resume Dangal...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Workspace Assistant Response Placeholder
        response = "Your AI agent will process this query."
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ------------------------------------------------------------
# RIGHT PANEL — ALL RESUMES & MANAGEMENT
# ------------------------------------------------------------
with right:
    st.subheader("📋 All Resumes")
    
    st.markdown(f'<div class="resume-count">{len(resumes)}</div>', unsafe_allow_html=True)
    st.caption("Total uploaded resumes")

    st.divider()

    if not resumes:
        st.info("No resumes uploaded yet.")
    else:
        for index, resume in enumerate(resumes, start=1):
            filename = resume["Key"].replace(S3_PREFIX, "")
            size_kb = resume["Size"] / 1024
            st.markdown(
                f"""
                <div class="resume-item">
                    <b>{index}. {filename}</b><br>
                    <small>{size_kb:.2f} KB</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    if resumes:
        st.markdown("**Delete Resume**")
        resume_options = {
            obj["Key"].replace(S3_PREFIX, ""): obj["Key"]
            for obj in resumes
        }

        selected_resume = st.selectbox(
            "Select resume to delete",
            options=list(resume_options.keys()),
            label_visibility="collapsed",
        )

        if st.button("🗑️ Delete Selected", use_container_width=True):
            success = delete_resume(resume_options[selected_resume])
            if success:
                st.success("Resume deleted.")
                st.rerun()
            else:
                st.error("Delete failed.")