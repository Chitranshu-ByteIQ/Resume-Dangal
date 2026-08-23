import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Page Setup
st.set_page_config(
    page_title="Resume Dangal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "Light"


# ============================================================
# Dynamic CSS Injection
# ============================================================
def apply_theme_css():
    if st.session_state.theme == "Dark":
        bg_color, card_bg, border_color, text_color, text_muted, input_bg = (
            "#0E1117",
            "#161B22",
            "#30363D",
            "#C9D1D9",
            "#8B949E",
            "#0D1117",
        )
    else:
        bg_color, card_bg, border_color, text_color, text_muted, input_bg = (
            "#FFFFFF",
            "#F8F9FA",
            "#E9ECEF",
            "#212529",
            "#6C757D",
            "#FFFFFF",
        )

    css = f"""
    <style>
    [data-testid="stHeader"] {{ display: none; }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1400px; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .app-title {{ font-size: 38px; font-weight: 800; margin-bottom: 2px; color: {text_color}; }}
    .app-subtitle {{ font-size: 15px; color: {text_muted}; margin-bottom: 15px; }}
    .content-card {{ background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
    .resume-count {{ font-size: 36px; font-weight: 800; text-align: center; color: {text_color}; margin: 5px 0; }}
    .resume-item {{ padding: 8px 0; border-bottom: 1px solid {border_color}; font-size: 13px; color: {text_color}; }}
    .stTextArea textarea, .stTextInput input {{ background-color: {input_bg} !important; color: {text_color} !important; border: 1px solid {border_color} !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


apply_theme_css()


# ============================================================
# API Service Helpers
# ============================================================
def fetch_resumes():
    try:
        res = requests.get(f"{BACKEND_URL}/resumes", timeout=5)
        return res.json() if res.status_code == 200 else []
    except requests.exceptions.RequestException:
        st.error("Failed to connect to backend service.")
        return []


def upload_resume_file(file):
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        res = requests.post(f"{BACKEND_URL}/resumes/upload", files=files, timeout=10)
        return res.status_code == 201
    except requests.exceptions.RequestException:
        return False


def delete_resume_key(key):
    try:
        res = requests.delete(
            f"{BACKEND_URL}/resumes", params={"s3_key": key}, timeout=5
        )
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False


def send_chat_prompt(prompt, job_desc):
    try:
        res = requests.post(
            f"{BACKEND_URL}/chat",
            json={"prompt": prompt, "job_description": job_desc},
            timeout=10,
        )
        if res.status_code == 200:
            return res.json().get("response")
    except requests.exceptions.RequestException:
        pass
    return "Error generating response."


# ============================================================
# Layout & Render
# ============================================================
header_left, header_right = st.columns([0.82, 0.18])

with header_left:
    st.markdown('<div class="app-title">Resume Dangal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">AI-powered resume screening workspace</div>',
        unsafe_allow_html=True,
    )

with header_right:
    selected_theme = st.selectbox(
        "Theme Mode",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1,
        key="theme_selector_dropdown",
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

st.divider()

resumes = fetch_resumes()
S3_PREFIX = "resumes/"

left, center, right = st.columns([1.2, 3.2, 1.5], gap="medium")

# LEFT PANEL — UPLOAD
with left:
    st.subheader("📤 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose resume", type=["pdf", "doc", "docx"], label_visibility="collapsed"
    )

    if uploaded_file:
        st.success(f"Selected: {uploaded_file.name}")
        st.caption(f"Size: {uploaded_file.size / 1024:.2f} KB")

        if st.button("Upload Resume", type="primary", use_container_width=True):
            with st.spinner("Uploading..."):
                if upload_resume_file(uploaded_file):
                    st.success("Uploaded successfully.")
                    st.rerun()
                else:
                    st.error("Upload failed.")

    st.divider()
    st.markdown("**Supported formats:**\n\nPDF • DOC • DOCX")

# CENTER PANEL — CHAT & JOB DESC
with center:
    st.subheader("🎯 Job Description")
    job_description = st.text_area(
        "Job Description Input",
        placeholder="Paste job description here...",
        height=170,
        label_visibility="collapsed",
    )

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
        bot_response = send_chat_prompt(prompt, job_description)
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_response}
        )
        st.rerun()

# RIGHT PANEL — MANAGEMENT
with right:
    st.subheader("📋 All Resumes")
    st.markdown(
        f'<div class="resume-count">{len(resumes)}</div>', unsafe_allow_html=True
    )
    st.caption("Total uploaded resumes")
    st.divider()

    if not resumes:
        st.info("No resumes uploaded yet.")
    else:
        for idx, item in enumerate(resumes, start=1):
            filename = item["Key"].replace(S3_PREFIX, "")
            st.markdown(
                f'<div class="resume-item"><b>{idx}. {filename}</b><br><small>{item["Size"] / 1024:.2f} KB</small></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    if resumes:
        st.markdown("**Delete Resume**")
        resume_options = {
            obj["Key"].replace(S3_PREFIX, ""): obj["Key"] for obj in resumes
        }
        selected_resume = st.selectbox(
            "Select resume to delete",
            options=list(resume_options.keys()),
            label_visibility="collapsed",
        )

        if st.button("🗑️ Delete Selected", use_container_width=True):
            if delete_resume_key(resume_options[selected_resume]):
                st.success("Deleted successfully.")
                st.rerun()
            else:
                st.error("Delete failed.")