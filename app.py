from __future__ import annotations

import os
from html import escape
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

REQUEST_TIMEOUT = 120


st.set_page_config(
    page_title="Resume Dangal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    defaults = {
        "candidates": [],
        "selected_candidate_ids": [],
        "job_description": None,
        "ranking_result": None,
        "viewed_candidate_id": None,
        "viewed_candidate": None,
        "pending_delete_id": None,
        "candidate_error": None,
        "last_status": None,
        "jd_input_mode": "Paste text",
        "candidates_loaded": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def api_request(
    method: str,
    path: str,
    **kwargs: Any,
) -> Any:
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(
            method,
            url,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not reach backend at {API_BASE_URL}: {error}"
        ) from error

    if response.status_code in {
        200,
        201,
    }:
        if not response.content:
            return {}
        return response.json()

    try:
        payload = response.json()
        detail = payload.get(
            "detail",
            payload,
        )
    except ValueError:
        detail = response.text or response.reason

    raise RuntimeError(
        f"Backend error {response.status_code}: {detail}"
    )


def get_candidates() -> list[dict[str, Any]]:
    payload = api_request(
        "GET",
        "/candidates",
    )
    return payload.get(
        "candidates",
        [],
    )


def get_candidate(
    candidate_id: str,
) -> dict[str, Any]:
    return api_request(
        "GET",
        f"/candidates/{candidate_id}",
    )


def upload_resume(
    uploaded_file: Any,
) -> dict[str, Any]:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    return api_request(
        "POST",
        "/resumes/upload",
        files=files,
    )


def delete_candidate(
    candidate_id: str,
) -> dict[str, Any]:
    return api_request(
        "DELETE",
        f"/candidates/{candidate_id}",
    )


def extract_jd_from_text(
    text: str,
) -> dict[str, Any]:
    return api_request(
        "POST",
        "/jobs/extract/text",
        data=text.encode("utf-8"),
        headers={
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


def extract_jd_from_pdf(
    uploaded_file: Any,
) -> dict[str, Any]:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    return api_request(
        "POST",
        "/jobs/extract/pdf",
        files=files,
    )


def rank_candidates(
    jd: dict[str, Any],
    candidate_ids: list[str],
) -> dict[str, Any]:
    return api_request(
        "POST",
        "/rank",
        json={
            "job_description": jd,
            "candidate_ids": candidate_ids,
        },
    )


def refresh_candidates() -> None:
    try:
        candidates = get_candidates()
        st.session_state["candidates"] = candidates
        st.session_state["candidate_error"] = None
        st.session_state["candidates_loaded"] = True

        available_ids = {
            candidate.get("candidate_id")
            for candidate in candidates
        }
        st.session_state["selected_candidate_ids"] = [
            candidate_id
            for candidate_id in st.session_state["selected_candidate_ids"]
            if candidate_id in available_ids
        ]
    except RuntimeError as error:
        st.session_state["candidate_error"] = str(error)
        st.session_state["candidates_loaded"] = True


def css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem;
        }
        .rd-header {
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 0.7rem;
            margin-bottom: 0.45rem;
            text-align: center;
        }
        .rd-header h1 {
            font-size: 1.75rem;
            line-height: 1.15;
            margin: 0;
            color: #111827;
            font-weight: 760;
        }
        .rd-header p {
            margin: 0.25rem 0 0;
            color: #64748b;
            font-size: 0.95rem;
        }
        .section-title {
            font-size: 0.9rem;
            font-weight: 760;
            color: #111827;
            margin: 0.15rem 0 0.35rem;
        }
        .metric-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.55rem;
            margin: 0.35rem 0 0.55rem;
        }
        .metric-box {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.55rem 0.65rem;
            background: #ffffff;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.74rem;
            margin-bottom: 0.15rem;
        }
        .metric-value {
            color: #111827;
            font-size: 1.1rem;
            font-weight: 760;
        }
        .candidate-card, .result-card, .status-panel, .jd-panel {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.75rem;
            background: #ffffff;
            margin-bottom: 0.65rem;
        }
        .candidate-name {
            font-weight: 720;
            color: #111827;
            line-height: 1.25;
        }
        .candidate-meta {
            color: #64748b;
            font-size: 0.78rem;
            overflow-wrap: anywhere;
        }
        .summary {
            color: #374151;
            font-size: 0.84rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }
        .badge {
            display: inline-block;
            padding: 0.12rem 0.42rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #3730a3;
            font-size: 0.76rem;
            font-weight: 650;
            margin: 0.14rem 0.18rem 0.14rem 0;
        }
        .score-big {
            font-size: 1.6rem;
            font-weight: 800;
            color: #0f766e;
            line-height: 1;
        }
        .muted {
            color: #64748b;
            font-size: 0.83rem;
        }
        .small-note {
            color: #6b7280;
            font-size: 0.78rem;
        }
        .status-panel {
            background: #f8fafc;
        }
        .scroll-panel {
            max-height: 760px;
            overflow-y: auto;
            padding-right: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="rd-header">
            <h1>Resume Dangal</h1>
            <p>AI-Powered Resume Screening & Ranking</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics() -> None:
    total = len(
        st.session_state["candidates"]
    )
    selected = len(
        st.session_state["selected_candidate_ids"]
    )
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-box">
                <div class="metric-label">Available Resumes</div>
                <div class="metric-value">{total}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Selected</div>
                <div class="metric-value">{selected}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_left_column() -> None:
    st.markdown(
        '<div class="section-title">Resume Management</div>',
        unsafe_allow_html=True,
    )

    uploaded_resume = st.file_uploader(
        "Upload Resume",
        type=[
            "pdf",
        ],
        key="resume_upload",
    )

    if st.button(
        "Upload Resume",
        use_container_width=True,
        disabled=uploaded_resume is None,
    ):
        with st.spinner(
            "Uploading and extracting resume..."
        ):
            try:
                payload = upload_resume(
                    uploaded_resume
                )
                candidate = payload.get(
                    "candidate",
                    {},
                )
                name = candidate.get(
                    "name",
                    "Candidate",
                )
                score = candidate.get(
                    "resume_score",
                    "N/A",
                )
                st.session_state["last_status"] = (
                f"Uploaded {name}. Resume score: {score}."
                )
                refresh_candidates()
                st.success(
                    st.session_state["last_status"]
                )
            except RuntimeError as error:
                st.error(
                    str(error)
                )

    render_metrics()

    refresh_col, clear_col = st.columns(
        2
    )
    with refresh_col:
        if st.button(
            "Refresh",
            use_container_width=True,
        ):
            refresh_candidates()
            st.session_state["last_status"] = (
                "Candidate list refreshed."
            )
    with clear_col:
        if st.button(
            "Clear",
            use_container_width=True,
        ):
            st.session_state["ranking_result"] = None
            st.session_state["last_status"] = (
                "Ranking result cleared."
            )

    st.caption(
        f"Backend: {API_BASE_URL}"
    )

    if st.session_state["last_status"]:
        st.info(
            st.session_state["last_status"]
        )


def render_jd_panel() -> None:
    st.markdown(
        '<div class="section-title">Job Description</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Input method",
        [
            "Paste text",
            "Upload PDF",
        ],
        horizontal=True,
        key="jd_input_mode",
        label_visibility="collapsed",
    )

    if mode == "Paste text":
        jd_text = st.text_area(
            "Paste Job Description",
            height=240,
            placeholder=(
                "Paste a complete multiline job description here..."
            ),
        )
        if st.button(
            "Extract Job Description",
            type="primary",
            use_container_width=True,
            disabled=not jd_text.strip(),
        ):
            with st.spinner(
                "Extracting job description..."
            ):
                try:
                    payload = extract_jd_from_text(
                        jd_text
                    )
                    st.session_state["job_description"] = payload.get(
                        "job_description"
                    )
                    st.session_state["ranking_result"] = None
                    st.success(
                        "Job description extracted."
                    )
                except RuntimeError as error:
                    st.error(
                        str(error)
                    )
    else:
        jd_pdf = st.file_uploader(
            "Upload JD PDF",
            type=[
                "pdf",
            ],
            key="jd_pdf_upload",
        )
        if st.button(
            "Extract from PDF",
            type="primary",
            use_container_width=True,
            disabled=jd_pdf is None,
        ):
            with st.spinner(
                "Extracting job description from PDF..."
            ):
                try:
                    payload = extract_jd_from_pdf(
                        jd_pdf
                    )
                    st.session_state["job_description"] = payload.get(
                        "job_description"
                    )
                    st.session_state["ranking_result"] = None
                    st.success(
                        "Job description extracted."
                    )
                except RuntimeError as error:
                    st.error(
                        str(error)
                    )

    jd = st.session_state["job_description"]
    if jd:
        render_jd_summary(
            jd
        )


def render_jd_summary(
    jd: dict[str, Any],
) -> None:
    st.markdown(
        '<div class="jd-panel">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**{jd.get('job_title') or 'Untitled role'}**"
    )
    st.caption(
        f"JD Score: {jd.get('jd_score', 'N/A')} / 100"
    )
    if jd.get(
        "summary"
    ):
        st.write(
            jd["summary"]
        )

    skill_cols = st.columns(
        2
    )
    with skill_cols[0]:
        st.caption(
            "Required Skills"
        )
        render_badges(
            jd.get(
                "required_skills",
                [],
            )
        )
    with skill_cols[1]:
        st.caption(
            "Preferred Skills"
        )
        render_badges(
            jd.get(
                "preferred_skills",
                [],
            )
        )

    if jd.get(
        "responsibilities"
    ):
        with st.expander(
            "Responsibilities",
            expanded=False,
        ):
            for item in jd["responsibilities"]:
                st.write(
                    f"- {item}"
                )
    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def render_badges(
    items: list[str],
) -> None:
    if not items:
        st.caption(
            "None extracted"
        )
        return

    html = "".join(
        f'<span class="badge">{escape(str(item))}</span>'
        for item in items
    )
    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_rank_action() -> None:
    jd = st.session_state["job_description"]
    selected_ids = st.session_state["selected_candidate_ids"]

    st.markdown(
        '<div class="section-title">Ranking</div>',
        unsafe_allow_html=True,
    )

    job_title = escape(
        str(
            (
                jd or {}
            ).get(
                "job_title",
                "No JD selected",
            )
        )
    )

    st.markdown(
        f"""
        <div class="status-panel">
            <div><b>Job:</b> {job_title}</div>
            <div><b>Selected Candidates:</b> {len(selected_ids)}</div>
            <div class="small-note">Ranking uses Match Score, not Resume Score or JD Score.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    disabled = not jd or not selected_ids

    if st.button(
        "Rank Selected Candidates",
        type="primary",
        use_container_width=True,
        disabled=disabled,
    ):
        with st.spinner(
            "Evaluating candidates and ranking results..."
        ):
            try:
                st.session_state["ranking_result"] = rank_candidates(
                    jd,
                    selected_ids,
                )
                st.success(
                    "Ranking completed."
                )
            except RuntimeError as error:
                st.error(
                    str(error)
                )

    if disabled:
        st.caption(
            "Extract a job description and select at least one candidate to rank."
        )


def render_status_panel() -> None:
    jd = st.session_state["job_description"]
    selected_count = len(
        st.session_state["selected_candidate_ids"]
    )
    result = st.session_state["ranking_result"]

    if result and result.get(
        "rankings"
    ):
        top = result["rankings"][0]
        message = (
            f"{top.get('candidate_name') or 'Top candidate'} ranked #1 "
            f"with a {top.get('match_score')}% match."
        )
        subtext = escape(str(top.get(
            "recommendation",
            "",
        )))
    elif jd:
        current_job = str(
            jd.get(
                "job_title"
            )
            or "current"
        )
        message = (
            f"Ready to rank {selected_count} selected candidates "
            f"against the {current_job} JD."
        )
        subtext = "Select candidates on the right, then run ranking."
    else:
        message = "Add a job description to start screening candidates."
        subtext = "Paste a JD or upload a JD PDF."

    st.markdown(
        f"""
        <div class="status-panel">
            <div class="candidate-name">Screening Assistant</div>
            <div class="summary">{escape(str(message))}</div>
            <div class="small-note">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ranking_results() -> None:
    result = st.session_state["ranking_result"]
    if not result:
        return

    rankings = result.get(
        "rankings",
        [],
    )
    evaluations = {
        item.get(
            "candidate_id"
        ): item
        for item in result.get(
            "evaluations",
            [],
        )
    }

    st.markdown(
        '<div class="section-title">Candidate Ranking</div>',
        unsafe_allow_html=True,
    )

    if not rankings:
        st.info(
            "No rankings returned."
        )
        return

    table_rows = [
        {
            "Rank": item.get(
                "rank"
            ),
            "Candidate": item.get(
                "candidate_name"
            )
            or item.get(
                "candidate_id"
            ),
            "Match Score": item.get(
                "match_score"
            ),
            "Resume Score": item.get(
                "resume_score"
            ),
            "Recommendation": item.get(
                "recommendation"
            ),
        }
        for item in rankings
    ]
    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

    for item in rankings:
        evaluation = evaluations.get(
            item.get(
                "candidate_id"
            ),
            {},
        )
        render_result_card(
            item,
            evaluation,
        )


def render_result_card(
    ranking: dict[str, Any],
    evaluation: dict[str, Any],
) -> None:
    rank = ranking.get(
        "rank"
    )
    name = ranking.get(
        "candidate_name"
    ) or ranking.get(
        "candidate_id"
    )
    match_score = ranking.get(
        "match_score",
        0,
    )
    resume_score = ranking.get(
        "resume_score",
        "N/A",
    )
    recommendation = ranking.get(
        "recommendation",
        "",
    )

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True,
    )
    top_cols = st.columns(
        [
            0.18,
            0.57,
            0.25,
        ]
    )
    with top_cols[0]:
        st.markdown(
            f"### #{rank}"
        )
    with top_cols[1]:
        st.markdown(
            f"**{name}**"
        )
        st.caption(
            recommendation
        )
    with top_cols[2]:
        st.markdown(
            f'<div class="score-big">{match_score}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Match Score"
        )

    score_cols = st.columns(
        2
    )
    with score_cols[0]:
        st.metric(
            "Match Score",
            f"{match_score} / 100",
        )
    with score_cols[1]:
        st.metric(
            "Resume Score",
            f"{resume_score} / 100",
        )

    with st.expander(
        "Detailed evaluation",
        expanded=False,
    ):
        render_component_score(
            "Required Skills",
            evaluation.get(
                "required_skill_score",
                0,
            ),
        )
        render_component_score(
            "Experience",
            evaluation.get(
                "experience_score",
                0,
            ),
        )
        render_component_score(
            "Projects",
            evaluation.get(
                "project_score",
                0,
            ),
        )
        render_component_score(
            "Preferred Skills",
            evaluation.get(
                "preferred_skill_score",
                0,
            ),
        )
        render_component_score(
            "Responsibilities",
            evaluation.get(
                "responsibility_score",
                0,
            ),
        )
        render_component_score(
            "Education",
            evaluation.get(
                "education_score",
                0,
            ),
        )

        st.markdown(
            "**Strengths**"
        )
        render_text_list(
            evaluation.get(
                "strengths",
                [],
            ),
            empty_text="No strengths returned.",
        )

        st.markdown(
            "**Gaps**"
        )
        render_text_list(
            evaluation.get(
                "gaps",
                [],
            ),
            empty_text="No gaps returned.",
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def render_component_score(
    label: str,
    value: Any,
) -> None:
    try:
        score = float(
            value or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        score = 0

    st.caption(
        f"{label}: {score:g} / 100"
    )
    st.progress(
        min(
            1.0,
            max(
                0.0,
                score / 100,
            ),
        )
    )


def render_text_list(
    items: list[str],
    empty_text: str,
) -> None:
    if not items:
        st.caption(
            empty_text
        )
        return

    for item in items:
        st.write(
            f"- {item}"
        )


def render_right_column() -> None:
    st.markdown(
        '<div class="section-title">Available Resumes</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state["candidates_loaded"]:
        refresh_candidates()

    if st.session_state["candidate_error"]:
        st.error(
            st.session_state["candidate_error"]
        )

    candidates = st.session_state["candidates"]

    action_cols = st.columns(
        2
    )
    with action_cols[0]:
        if st.button(
            "Select All",
            use_container_width=True,
            disabled=not candidates,
        ):
            st.session_state["selected_candidate_ids"] = [
                candidate.get(
                    "candidate_id"
                )
                for candidate in candidates
                if candidate.get(
                    "candidate_id"
                )
            ]
            for candidate_id in st.session_state["selected_candidate_ids"]:
                st.session_state[f"select_{candidate_id}"] = True
            st.rerun()
    with action_cols[1]:
        if st.button(
            "Clear Selection",
            use_container_width=True,
            disabled=not st.session_state["selected_candidate_ids"],
        ):
            for candidate_id in st.session_state["selected_candidate_ids"]:
                st.session_state[f"select_{candidate_id}"] = False
            st.session_state["selected_candidate_ids"] = []
            st.rerun()

    st.caption(
        f"Selected: {len(st.session_state['selected_candidate_ids'])} candidates"
    )

    st.markdown(
        '<div class="scroll-panel">',
        unsafe_allow_html=True,
    )

    for candidate in candidates:
        render_candidate_card(
            candidate
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    render_candidate_detail()


def render_candidate_card(
    candidate: dict[str, Any],
) -> None:
    candidate_id = candidate.get(
        "candidate_id"
    )
    if not candidate_id:
        return

    selected_ids = st.session_state["selected_candidate_ids"]
    name = candidate.get(
        "name"
    ) or "Unnamed candidate"
    score = candidate.get(
        "resume_score",
        "N/A",
    )
    summary = candidate.get(
        "summary"
    ) or "No summary available."

    st.markdown(
        '<div class="candidate-card">',
        unsafe_allow_html=True,
    )
    checked = st.checkbox(
        name,
        value=candidate_id in selected_ids,
        key=f"select_{candidate_id}",
    )

    if checked and candidate_id not in selected_ids:
        selected_ids.append(
            candidate_id
        )
    if not checked and candidate_id in selected_ids:
        selected_ids.remove(
            candidate_id
        )

    st.caption(
        f"Resume Score: {score} / 100"
    )
    st.markdown(
        f'<div class="summary">{escape(str(summary[:180]))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="candidate-meta">ID: {escape(str(candidate_id))}</div>',
        unsafe_allow_html=True,
    )

    view_col, delete_col = st.columns(
        2
    )
    with view_col:
        if st.button(
            "View",
            key=f"view_{candidate_id}",
            use_container_width=True,
        ):
            with st.spinner(
                "Loading candidate details..."
            ):
                try:
                    st.session_state["viewed_candidate"] = get_candidate(
                        candidate_id
                    )
                    st.session_state["viewed_candidate_id"] = candidate_id
                except RuntimeError as error:
                    st.error(
                        str(error)
                    )
    with delete_col:
        if st.button(
            "Delete",
            key=f"delete_{candidate_id}",
            use_container_width=True,
        ):
            st.session_state["pending_delete_id"] = candidate_id

    if st.session_state["pending_delete_id"] == candidate_id:
        st.warning(
            f"Delete {name}?"
        )
        confirm_col, cancel_col = st.columns(
            2
        )
        with confirm_col:
            if st.button(
                "Confirm",
                key=f"confirm_delete_{candidate_id}",
                use_container_width=True,
            ):
                try:
                    delete_candidate(
                        candidate_id
                    )
                    st.session_state["pending_delete_id"] = None
                    st.session_state["viewed_candidate_id"] = None
                    st.session_state["viewed_candidate"] = None
                    refresh_candidates()
                    st.success(
                        "Candidate deleted."
                    )
                    st.rerun()
                except RuntimeError as error:
                    st.error(
                        str(error)
                    )
        with cancel_col:
            if st.button(
                "Cancel",
                key=f"cancel_delete_{candidate_id}",
                use_container_width=True,
            ):
                st.session_state["pending_delete_id"] = None
                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def render_candidate_detail() -> None:
    candidate = st.session_state["viewed_candidate"]
    if not candidate:
        return

    candidate_id = st.session_state["viewed_candidate_id"]
    name = candidate.get(
        "name"
    ) or "Candidate"

    with st.expander(
        f"Candidate Detail: {name}",
        expanded=True,
    ):
        st.caption(
            f"ID: {candidate_id}"
        )
        st.metric(
            "Resume Score",
            f"{candidate.get('resume_score', 'N/A')} / 100",
        )
        if candidate.get(
            "summary"
        ):
            st.write(
                candidate["summary"]
            )

        if candidate.get(
            "resume_url"
        ):
            st.link_button(
                "Open Resume",
                candidate["resume_url"],
                use_container_width=True,
            )

        st.markdown(
            "**Skills**"
        )
        render_badges(
            candidate.get(
                "skills",
                [],
            )
        )

        render_profile_section(
            "Experience",
            candidate.get(
                "experience",
                [],
            ),
        )
        render_profile_section(
            "Projects",
            candidate.get(
                "projects",
                [],
            ),
        )
        render_profile_section(
            "Education",
            candidate.get(
                "education",
                [],
            ),
        )


def render_profile_section(
    title: str,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        return

    st.markdown(
        f"**{title}**"
    )
    for row in rows:
        if isinstance(
            row,
            dict,
        ):
            primary = (
                row.get(
                    "role"
                )
                or row.get(
                    "name"
                )
                or row.get(
                    "degree"
                )
                or "Item"
            )
            secondary = (
                row.get(
                    "company"
                )
                or row.get(
                    "institution"
                )
                or row.get(
                    "description"
                )
                or ""
            )
            st.write(
                f"- **{primary}** {secondary}"
            )


def main() -> None:
    init_state()
    css()

    left_col, center_col, right_col = st.columns(
        [
            1.0,
            2.5,
            1.3,
        ],
        gap="large",
    )

    with left_col:
        render_left_column()

    with center_col:
        render_header()
        render_jd_panel()
        render_status_panel()
        render_rank_action()
        render_ranking_results()

    with right_col:
        render_right_column()


if __name__ == "__main__":
    main()
