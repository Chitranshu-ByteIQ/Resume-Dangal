import requests
import streamlit as st


# ==========================================================
# Configuration
# ==========================================================

API_URL = "http://127.0.0.1:8000"


# ==========================================================
# Page Config
# ==========================================================

st.set_page_config(
    page_title="Resume Dangal",
    page_icon="📄",
    layout="wide",
)


# ==========================================================
# Custom CSS
# ==========================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 2rem;
    }

    .resume-header {
        padding: 1rem 0 2rem 0;
    }

    .resume-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .resume-subtitle {
        color: #777;
        font-size: 1.1rem;
    }

    .resume-card {
        padding: 1.2rem;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin-bottom: 1rem;
        background-color: white;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# Header
# ==========================================================

st.markdown(
    """
    <div class="resume-header">
        <div class="resume-title">
            Resume Dangal
        </div>

        <div class="resume-subtitle">
            AI-powered resume ranking and candidate intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# Sidebar
# ==========================================================

with st.sidebar:

    st.header("Resume Manager")

    st.caption(
        "Upload candidate resumes to Resume Dangal."
    )

    st.divider()

    if st.button(
        "🔄 Refresh Resumes",
        use_container_width=True,
    ):
        st.rerun()


# ==========================================================
# Upload Section
# ==========================================================

st.subheader("Upload Resume")

uploaded_file = st.file_uploader(
    "Choose a PDF resume",
    type=["pdf"],
    accept_multiple_files=False,
)


if uploaded_file:

    st.write(
        f"Selected: **{uploaded_file.name}**"
    )

    if st.button(
        "Upload Resume",
        type="primary",
        use_container_width=True,
    ):

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf",
            )
        }

        try:

            response = requests.post(
                f"{API_URL}/api/resumes/upload",
                files=files,
                timeout=60,
            )

            if response.status_code == 201:

                data = response.json()

                st.success(
                    "Resume uploaded successfully."
                )

                st.json(data)

                st.rerun()

            else:

                try:
                    error = response.json()
                except Exception:
                    error = response.text

                st.error(
                    f"Upload failed: {error}"
                )

        except requests.RequestException as error:

            st.error(
                f"Backend connection failed: {error}"
            )


# ==========================================================
# Resume List
# ==========================================================

st.divider()

st.subheader("Stored Resumes")


try:

    response = requests.get(
        f"{API_URL}/api/resumes",
        timeout=30,
    )

    if response.status_code == 200:

        data = response.json()

        resumes = data.get(
            "resumes",
            [],
        )

        if not resumes:

            st.info(
                "No resumes stored yet."
            )

        else:

            st.caption(
                f"{len(resumes)} resume(s) stored"
            )

            for resume in resumes:

                with st.container(
                    border=True
                ):

                    col1, col2, col3 = st.columns(
                        [5, 2, 1]
                    )

                    with col1:

                        st.markdown(
                            f"### 📄 {resume['filename']}"
                        )

                        st.caption(
                            f"S3 Key: `{resume['s3_key']}`"
                        )

                    with col2:

                        size_kb = (
                            resume["size"]
                            / 1024
                        )

                        st.metric(
                            "Size",
                            f"{size_kb:.1f} KB",
                        )

                    with col3:

                        delete_clicked = st.button(
                            "🗑️",
                            key=f"delete_{resume['s3_key']}",
                            help="Delete resume",
                        )

                        if delete_clicked:

                            delete_response = requests.delete(
                                f"{API_URL}/api/resumes",
                                params={
                                    "s3_key": resume[
                                        "s3_key"
                                    ]
                                },
                                timeout=30,
                            )

                            if (
                                delete_response.status_code
                                == 200
                            ):

                                st.success(
                                    "Resume deleted."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Failed to delete resume."
                                )

    else:

        st.error(
            "Unable to retrieve resumes."
        )

except requests.RequestException:

    st.warning(
        "FastAPI backend is not running."
    )