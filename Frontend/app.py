import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

API_URL = "http://localhost:8000"


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Resume Dangal",
    page_icon="🎯",
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
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .score {
        font-size: 32px;
        font-weight: 800;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session state
# ============================================================

if "candidates" not in st.session_state:
    st.session_state.candidates = []

if "job" not in st.session_state:
    st.session_state.job = None

if "rankings" not in st.session_state:
    st.session_state.rankings = None


# ============================================================
# Helper
# ============================================================


def api_error(response):
    try:
        data = response.json()

        if isinstance(data, dict):
            return data.get(
                "detail",
                "Unknown API error.",
            )

        return str(data)

    except Exception:
        return response.text or "Unknown API error."


def refresh_candidates():
    try:

        response = requests.get(
            f"{API_URL}/resumes",
            timeout=30,
        )

        if response.ok:
            st.session_state.candidates = (
                response.json()
            )

        else:
            st.error(
                f"Failed to load resumes: "
                f"{api_error(response)}"
            )

    except requests.RequestException as error:

        st.error(
            f"Backend connection failed: {error}"
        )


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="main-title">🎯 Resume Dangal</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "AI-Powered Hybrid Resume Screening & Ranking"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# Backend status
# ============================================================

try:

    health = requests.get(
        f"{API_URL}/health",
        timeout=5,
    )

    if health.ok:
        st.success("Backend connected")

    else:
        st.warning("Backend is running but unhealthy.")

except requests.RequestException:
    st.error(
        "Backend is not reachable. "
        "Start FastAPI before using the application."
    )


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.header("⚙️ System")

    st.caption(
        "Resume Dangal uses a hybrid ranking pipeline."
    )

    st.markdown(
        """
        **Ranking**

        - 40% Deterministic
        - 40% Semantic AI
        - 20% LLM Evaluation
        """
    )

    if st.button(
        "🔄 Refresh Resumes",
        use_container_width=True,
    ):
        refresh_candidates()
        st.rerun()


# ============================================================
# STEP 1 — Resume Upload
# ============================================================

st.markdown(
    '<div class="section-title">'
    "1️⃣ Upload Resumes"
    "</div>",
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Upload candidate resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    help="Only PDF and DOCX resumes are supported.",
)


if uploaded_files:

    for uploaded_file in uploaded_files:

        with st.spinner(
            f"Analyzing {uploaded_file.name}..."
        ):

            try:

                response = requests.post(
                    f"{API_URL}/resumes/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    },
                    timeout=180,
                )

                if response.ok:

                    data = response.json()

                    candidate = data["candidate"]

                    st.success(
                        f"✓ {uploaded_file.name} "
                        "processed successfully."
                    )

                    # ----------------------------------------
                    # Automatically show extracted fields
                    # ----------------------------------------

                    with st.expander(
                        f"📄 {candidate['name']} — "
                        f"{candidate.get('suitable_title') or 'Candidate'}",
                        expanded=True,
                    ):

                        col1, col2 = st.columns(2)

                        with col1:

                            st.text_input(
                                "Name",
                                value=candidate["name"],
                                key=f"name_{candidate['candidate_id']}",
                                disabled=True,
                            )

                            st.text_input(
                                "Email",
                                value=candidate.get("email") or "",
                                key=f"email_{candidate['candidate_id']}",
                                disabled=True,
                            )

                            st.text_input(
                                "Phone",
                                value=candidate.get("phone") or "",
                                key=f"phone_{candidate['candidate_id']}",
                                disabled=True,
                            )

                            st.text_input(
                                "Location",
                                value=candidate.get("location") or "",
                                key=f"location_{candidate['candidate_id']}",
                                disabled=True,
                            )

                        with col2:

                            st.text_input(
                                "Suitable Title",
                                value=candidate.get(
                                    "suitable_title"
                                ) or "",
                                key=f"title_{candidate['candidate_id']}",
                                disabled=True,
                            )

                            st.number_input(
                                "Experience (years)",
                                value=float(
                                    candidate.get(
                                        "experience_years"
                                    ) or 0
                                ),
                                key=f"exp_{candidate['candidate_id']}",
                                disabled=True,
                            )

                            st.text_area(
                                "Technical Skills",
                                value=", ".join(
                                    candidate.get(
                                        "tech_stack",
                                        [],
                                    )
                                ),
                                key=f"skills_{candidate['candidate_id']}",
                                disabled=True,
                            )

                        st.text_area(
                            "Profile Summary",
                            value=candidate.get(
                                "profile_summary"
                            ) or "",
                            key=f"summary_{candidate['candidate_id']}",
                            disabled=True,
                        )

                        st.text_area(
                            "Projects",
                            value="\n".join(
                                candidate.get(
                                    "projects",
                                    [],
                                )
                            ),
                            key=f"projects_{candidate['candidate_id']}",
                            disabled=True,
                        )

                else:

                    # ----------------------------------------
                    # IMPORTANT:
                    # Show actual rejection reason
                    # ----------------------------------------

                    st.error(
                        f"❌ {uploaded_file.name}: "
                        f"{api_error(response)}"
                    )

            except requests.RequestException as error:

                st.error(
                    f"❌ Failed to process "
                    f"{uploaded_file.name}: {error}"
                )


# ============================================================
# Load existing candidates
# ============================================================

refresh_candidates()


# ============================================================
# Candidate summary
# ============================================================

if st.session_state.candidates:

    st.markdown(
        '<div class="section-title">'
        "📋 Stored Candidates"
        "</div>",
        unsafe_allow_html=True,
    )

    st.dataframe(
        [
            {
                "Name": candidate["name"],
                "Title": candidate.get(
                    "suitable_title"
                ),
                "Experience": candidate.get(
                    "experience_years"
                ),
                "Skills": ", ".join(
                    candidate.get(
                        "tech_stack",
                        [],
                    )
                ),
            }
            for candidate in st.session_state.candidates
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# STEP 2 — Job Description
# ============================================================

st.markdown(
    '<div class="section-title">'
    "2️⃣ Job Description"
    "</div>",
    unsafe_allow_html=True,
)

jd_text = st.text_area(
    "Paste the Job Description",
    height=250,
    placeholder=(
        "Paste the complete job description here..."
    ),
)


if st.button(
    "🔍 Analyze Job Description",
    type="primary",
    use_container_width=True,
):

    if not jd_text.strip():

        st.error(
            "Please enter a Job Description first."
        )

    else:

        with st.spinner(
            "Analyzing Job Description..."
        ):

            try:

                response = requests.post(
                    f"{API_URL}/jobs/analyze",
                    json={
                        "description": jd_text,
                    },
                    timeout=120,
                )

                if response.ok:

                    data = response.json()

                    st.session_state.job = data["job"]

                    st.success(
                        "Job Description analyzed successfully."
                    )

                else:

                    st.error(
                        api_error(response)
                    )

            except requests.RequestException as error:

                st.error(
                    f"Backend connection failed: {error}"
                )


# ============================================================
# Display extracted JD
# ============================================================

if st.session_state.job:

    job = st.session_state.job

    st.markdown(
        '<div class="section-title">'
        "📋 Extracted Job Profile"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:

        st.text_input(
            "Job Title",
            value=job["title"],
            disabled=True,
        )

        st.text_area(
            "Required Skills",
            value=", ".join(
                job.get(
                    "required_skills",
                    [],
                )
            ),
            disabled=True,
        )

        st.text_area(
            "Preferred Skills",
            value=", ".join(
                job.get(
                    "preferred_skills",
                    [],
                )
            ),
            disabled=True,
        )

    with col2:

        st.number_input(
            "Required Experience",
            value=float(
                job.get(
                    "experience_required"
                ) or 0
            ),
            disabled=True,
        )

        st.text_area(
            "Responsibilities",
            value="\n".join(
                job.get(
                    "responsibilities",
                    [],
                )
            ),
            disabled=True,
        )

        st.text_area(
            "Education",
            value="\n".join(
                job.get(
                    "education",
                    [],
                )
            ),
            disabled=True,
        )


# ============================================================
# STEP 3 — Ranking
# ============================================================

st.markdown(
    '<div class="section-title">'
    "3️⃣ Rank Candidates"
    "</div>",
    unsafe_allow_html=True,
)


if not st.session_state.job:

    st.info(
        "Analyze a Job Description before ranking candidates."
    )

elif not st.session_state.candidates:

    st.info(
        "Upload at least one valid resume before ranking."
    )

else:

    if st.button(
        "🚀 Rank All Candidates",
        type="primary",
        use_container_width=True,
    ):

        job_id = st.session_state.job["job_id"]

        with st.spinner(
            "Running hybrid AI ranking..."
        ):

            try:

                response = requests.post(
                    f"{API_URL}/jobs/{job_id}/rank",
                    timeout=600,
                )

                if response.ok:

                    st.session_state.rankings = (
                        response.json()
                    )

                    st.success(
                        "Ranking completed successfully."
                    )

                else:

                    st.error(
                        api_error(response)
                    )

            except requests.RequestException as error:

                st.error(
                    f"Ranking failed: {error}"
                )


# ============================================================
# Results
# ============================================================

if st.session_state.rankings:

    result = st.session_state.rankings

    st.markdown(
        '<div class="section-title">'
        "🏆 Ranking Results"
        "</div>",
        unsafe_allow_html=True,
    )

    rankings = result.get(
        "rankings",
        [],
    )

    # --------------------------------------------------------
    # Summary table
    # --------------------------------------------------------

    table = []

    for candidate in rankings:

        scores = candidate["scores"]

        table.append(
            {
                "Rank": candidate["rank"],
                "Candidate": candidate[
                    "candidate_name"
                ],
                "Final Score": scores[
                    "final_score"
                ],
                "Deterministic": scores[
                    "deterministic_score"
                ],
                "Semantic AI": scores[
                    "semantic_score"
                ],
                "LLM": scores[
                    "llm_score"
                ],
                "Recommendation": candidate[
                    "recommendation"
                ],
            }
        )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Detailed results
    # --------------------------------------------------------

    st.markdown(
        "### Candidate Analysis"
    )

    for candidate in rankings:

        scores = candidate["scores"]

        with st.expander(
            f"#{candidate['rank']} "
            f"{candidate['candidate_name']} "
            f"— {scores['final_score']}/100"
        ):

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Final",
                    f"{scores['final_score']:.1f}",
                )

            with col2:
                st.metric(
                    "Deterministic",
                    f"{scores['deterministic_score']:.1f}",
                )

            with col3:
                st.metric(
                    "Semantic AI",
                    f"{scores['semantic_score']:.1f}",
                )

            with col4:
                st.metric(
                    "LLM",
                    f"{scores['llm_score']:.1f}",
                )

            st.markdown(
                f"**Recommendation:** "
                f"{candidate['recommendation']}"
            )

            st.markdown(
                "#### Matched Required Skills"
            )

            if candidate[
                "matched_required_skills"
            ]:

                st.success(
                    ", ".join(
                        candidate[
                            "matched_required_skills"
                        ]
                    )
                )

            else:

                st.warning(
                    "No required skills matched."
                )

            st.markdown(
                "#### Missing Required Skills"
            )

            if candidate[
                "missing_required_skills"
            ]:

                st.error(
                    ", ".join(
                        candidate[
                            "missing_required_skills"
                        ]
                    )
                )

            else:

                st.success(
                    "No required skill gaps."
                )

            llm = candidate.get(
                "llm_evaluation"
            )

            if llm:

                st.markdown(
                    "#### 🤖 LLM Evaluation"
                )

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.metric(
                        "Skill Fit",
                        f"{llm['skill_fit']:.1f}",
                    )

                with c2:
                    st.metric(
                        "Experience Fit",
                        f"{llm['experience_fit']:.1f}",
                    )

                with c3:
                    st.metric(
                        "Responsibility Fit",
                        f"{llm['responsibility_fit']:.1f}",
                    )

                with c4:
                    st.metric(
                        "Project Fit",
                        f"{llm['project_fit']:.1f}",
                    )

                st.markdown(
                    "**Strengths**"
                )

                for strength in llm.get(
                    "strengths",
                    [],
                ):
                    st.write(
                        f"✓ {strength}"
                    )

                st.markdown(
                    "**Gaps**"
                )

                for gap in llm.get(
                    "gaps",
                    [],
                ):
                    st.write(
                        f"• {gap}"
                    )

                st.markdown(
                    "**Reasoning**"
                )

                st.write(
                    llm.get(
                        "reasoning",
                        "",
                    )
                )