import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

API_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)

REQUEST_TIMEOUT = 120


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Resume Dangal",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .app-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .app-subtitle {
        font-size: 16px;
        opacity: 0.65;
        margin-bottom: 25px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,0.25);
        text-align: center;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 800;
    }

    .metric-label {
        font-size: 13px;
        opacity: 0.65;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API HELPERS
# ============================================================

def api_get(
    endpoint: str,
    timeout: int = 20,
):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=timeout,
        )

        return response

    except requests.RequestException as error:

        st.error(
            f"Backend connection failed: {error}"
        )

        return None


def api_post(
    endpoint: str,
    **kwargs,
):

    try:

        return requests.post(
            f"{API_URL}{endpoint}",
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )

    except requests.RequestException as error:

        st.error(
            f"Backend connection failed: {error}"
        )

        return None


def api_delete(
    endpoint: str,
):

    try:

        return requests.delete(
            f"{API_URL}{endpoint}",
            timeout=30,
        )

    except requests.RequestException as error:

        st.error(
            f"Backend connection failed: {error}"
        )

        return None


# ============================================================
# LOAD RESUMES
# ============================================================

@st.cache_data(
    ttl=10,
    show_spinner=False,
)
def get_resumes():

    response = api_get(
        "/api/resumes"
    )

    if response is None:
        return []

    if response.status_code != 200:

        return []

    try:

        data = response.json()

        return data.get(
            "resumes",
            [],
        )

    except Exception:

        return []


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.markdown(
        '<div class="app-title">🏆 Resume Dangal</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "AI-powered resume ranking and candidate intelligence"
        "</div>",
        unsafe_allow_html=True,
    )


with header_right:

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        get_resumes.clear()

        st.rerun()


# ============================================================
# BACKEND STATUS
# ============================================================

health_response = api_get(
    "/health",
    timeout=5,
)

if health_response is not None:

    if health_response.status_code == 200:

        st.success(
            "● Backend connected",
            icon="✅",
        )

    else:

        st.warning(
            "Backend is degraded."
        )

else:

    st.error(
        "Backend unavailable."
    )


# ============================================================
# LOAD RESUMES
# ============================================================

resumes = get_resumes()


# ============================================================
# TOP METRICS
# ============================================================

m1, m2, m3 = st.columns(3)


with m1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">
                {len(resumes)}
            </div>
            <div class="metric-label">
                Stored Resumes
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with m2:

    selected_count = len(
        st.session_state.get(
            "selected_resume_ids",
            [],
        )
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">
                {selected_count}
            </div>
            <div class="metric-label">
                Selected Candidates
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with m3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">
                {API_URL}
            </div>
            <div class="metric-label">
                API Endpoint
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()


# ============================================================
# MAIN LAYOUT
# ============================================================

left, center, right = st.columns(
    [1.3, 3.4, 1.8],
    gap="large",
)


# ============================================================
# LEFT - UPLOAD
# ============================================================

with left:

    st.markdown(
        '<div class="section-title">📤 Upload Resume</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        accept_multiple_files=False,
    )

    if uploaded_file:

        st.info(
            f"📄 {uploaded_file.name}"
        )

        st.caption(
            f"{uploaded_file.size / 1024:.1f} KB"
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

            with st.spinner(
                "Uploading resume..."
            ):

                response = api_post(
                    "/api/resumes/upload",
                    files=files,
                )

            if response is not None:

                if response.status_code == 201:

                    st.success(
                        "Resume uploaded."
                    )

                    get_resumes.clear()

                    st.rerun()

                else:

                    try:
                        detail = response.json().get(
                            "detail",
                            response.text,
                        )
                    except Exception:
                        detail = response.text

                    st.error(
                        f"Upload failed: {detail}"
                    )


# ============================================================
# CENTER - JOB DESCRIPTION
# ============================================================

with center:

    st.markdown(
        '<div class="section-title">🎯 Job Description</div>',
        unsafe_allow_html=True,
    )

    job_description = st.text_area(
        "Job Description",
        height=260,
        placeholder=(
            "Paste the complete job description here...\n\n"
            "Example:\n"
            "We are looking for an AI Engineer..."
        ),
        label_visibility="collapsed",
    )

    st.caption(
        "The JD is used by the LangGraph ranking engine."
    )


# ============================================================
# RIGHT - RESUME SELECTION
# ============================================================

with right:

    st.markdown(
        '<div class="section-title">📋 Resume Library</div>',
        unsafe_allow_html=True,
    )

    if not resumes:

        st.info(
            "No resumes uploaded yet."
        )

    else:

        # ----------------------------------------------------
        # Create lookup
        # ----------------------------------------------------

        resume_lookup = {
            resume["resume_id"]: resume
            for resume in resumes
        }

        resume_options = {
            resume["resume_id"]: (
                f"{resume['filename']} "
                f"({resume['size'] / 1024:.1f} KB)"
            )
            for resume in resumes
        }

        existing_selection = [
            resume_id
            for resume_id in st.session_state.get(
                "selected_resume_ids",
                [],
            )
            if resume_id in resume_lookup
        ]

        selected_resume_ids = st.multiselect(
            "Select candidates",
            options=list(
                resume_options.keys()
            ),
            default=existing_selection,
            format_func=lambda resume_id:
                resume_options[resume_id],
        )

        st.session_state[
            "selected_resume_ids"
        ] = selected_resume_ids

        st.caption(
            f"{len(selected_resume_ids)} resume(s) selected"
        )

        st.divider()

        # ----------------------------------------------------
        # Selected resumes
        # ----------------------------------------------------

        for resume_id in selected_resume_ids:

            resume = resume_lookup[
                resume_id
            ]

            st.markdown(
                f"**📄 {resume['filename']}**"
            )

        st.divider()

        # ----------------------------------------------------
        # Delete
        # ----------------------------------------------------

        st.markdown(
            "**Delete Resume**"
        )

        delete_options = {
            resume["resume_id"]: resume["filename"]
            for resume in resumes
        }

        delete_id = st.selectbox(
            "Resume",
            options=list(
                delete_options.keys()
            ),
            format_func=lambda resume_id:
                delete_options[resume_id],
            label_visibility="collapsed",
        )

        if st.button(
            "🗑️ Delete",
            use_container_width=True,
        ):

            response = api_delete(
                f"/api/resumes/{delete_id}"
            )

            if response is not None:

                if response.status_code == 200:

                    st.success(
                        "Resume deleted."
                    )

                    st.session_state[
                        "selected_resume_ids"
                    ] = [
                        x
                        for x in selected_resume_ids
                        if x != delete_id
                    ]

                    get_resumes.clear()

                    st.rerun()

                else:

                    st.error(
                        "Failed to delete resume."
                    )


# ============================================================
# RANKING
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">🏆 Resume Ranking</div>',
    unsafe_allow_html=True,
)


selected_resume_ids = st.session_state.get(
    "selected_resume_ids",
    [],
)


rank_disabled = (
    not job_description.strip()
    or not selected_resume_ids
)


if rank_disabled:

    if not job_description.strip():

        st.info(
            "Enter a job description first."
        )

    elif not selected_resume_ids:

        st.info(
            "Select at least one resume from the Resume Library."
        )


if st.button(
    "🚀 Rank Selected Resumes",
    type="primary",
    use_container_width=True,
    disabled=rank_disabled,
):

    payload = {
        "job_description": job_description,
        "resume_ids": selected_resume_ids,
    }

    with st.spinner(
        "Analyzing resumes and ranking candidates..."
    ):

        response = api_post(
            "/api/ranking",
            json=payload,
        )

    if response is not None:

        if response.status_code == 200:

            data = response.json()

            st.session_state[
                "ranking_results"
            ] = data.get(
                "results",
                [],
            )

            st.success(
                f"Ranked {data.get('total_resumes', 0)} resumes."
            )

        else:

            try:

                detail = response.json().get(
                    "detail",
                    response.text,
                )

            except Exception:

                detail = response.text

            st.error(
                f"Ranking failed: {detail}"
            )


# ============================================================
# RESULTS
# ============================================================

results = st.session_state.get(
    "ranking_results",
    [],
)


if results:

    st.divider()

    st.markdown(
        '<div class="section-title">📊 Ranking Results</div>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Main ranking table
    # --------------------------------------------------------

    preferred_columns = [
        "Rank",
        "Candidate Name",
        "Final Score",
        "Recommendation",
        "Skill Score",
        "Project Score",
        "Experience Score",
        "Education Score",
    ]

    visible_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    if visible_columns:

        st.dataframe(
            df[visible_columns],
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # Candidate details
    # --------------------------------------------------------

    st.subheader(
        "Candidate Details"
    )

    for _, row in df.iterrows():

        candidate_name = row.get(
            "Candidate Name",
            "Unknown",
        )

        score = row.get(
            "Final Score",
            0,
        )

        recommendation = row.get(
            "Recommendation",
            "Unknown",
        )

        with st.expander(
            f"#{row.get('Rank', '')} "
            f"{candidate_name} — "
            f"{score}% — "
            f"{recommendation}"
        ):

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Skills",
                    row.get(
                        "Skill Score",
                        0,
                    ),
                )

            with c2:
                st.metric(
                    "Projects",
                    row.get(
                        "Project Score",
                        0,
                    ),
                )

            with c3:
                st.metric(
                    "Experience",
                    row.get(
                        "Experience Score",
                        0,
                    ),
                )

            with c4:
                st.metric(
                    "Education",
                    row.get(
                        "Education Score",
                        0,
                    ),
                )

            matched = row.get(
                "Matched Skills",
                [],
            )

            if isinstance(
                matched,
                list,
            ):

                st.write(
                    "**Matched Skills:**",
                    ", ".join(matched)
                    if matched
                    else "None",
                )

            else:

                st.write(
                    f"**Matched Skills:** {matched}"
                )

            reason = row.get(
                "Reason",
                "",
            )

            if reason:

                st.write(
                    "**Reason:**"
                )

                st.write(
                    reason
                )