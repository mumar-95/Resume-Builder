"""Session state helpers for the resume wizard."""

from __future__ import annotations

import streamlit as st

STEPS = [
    "Welcome",
    "Personal",
    "Role & focus",
    "Technologies",
    "Reference resume",
    "Experience",
    "Education",
    "Preview",
    "Download",
]

ROLE_FOCUS_OPTIONS = [
    "Only Development",
    "Development + Testing",
    "Development + Production",
    "Development + Testing + Production",
]

ROLE_TITLE_HINTS = {
    "Only Development": "Software Developer",
    "Development + Testing": "Software Developer / QA Engineer",
    "Development + Production": "Software Developer / DevOps Engineer",
    "Development + Testing + Production": "Full-Stack Software Engineer",
}


def init_session_state() -> None:
    defaults = {
        "step": 0,
        "personal": {
            "full_name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "portfolio": "",
            "target_title": "",
            "summary": "",
        },
        "role_focus": "Only Development",
        "priority_technologies": [],
        "all_technologies": [],
        "companies": [],
        "company_draft": _empty_company(),
        "project_draft": _empty_project(),
        "education": [],
        "education_draft": _empty_education(),
        "certifications": "",
        "achievements": "",
        "reference_file_name": None,
        "reference_file_bytes": None,
        "reference_file_type": None,
        "reference_text": "",
        "reference_format_profile": None,
        "use_reference_format": False,
        "generated_resume": None,
        "company_index": 0,
        "expected_company_count": 1,
        "reviewing_responsibilities": False,
        "add_another_project_pending": False,
        "regen_feedback": "",
        "responsibilities_editor_version": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _empty_company() -> dict:
    return {
        "company_name": "",
        "job_title": "",
        "location": "",
        "start_date": "",
        "end_date": "",
        "currently_working": False,
        "technologies": [],
        "projects": [],
        "responsibilities": "",
    }


def _empty_project() -> dict:
    return {
        "name": "",
        "tenure": "",
        "role": "",
        "description": "",
        "technologies": "",
        "responsibilities": "",
        "achievements": "",
    }


def _empty_education() -> dict:
    return {
        "degree": "",
        "institution": "",
        "location": "",
        "start_year": "",
        "end_year": "",
        "details": "",
    }


def go_next() -> None:
    st.session_state.step = min(st.session_state.step + 1, len(STEPS) - 1)


def go_back() -> None:
    st.session_state.step = max(st.session_state.step - 1, 0)


def reset_wizard() -> None:
    keep = {"step"}
    for key in list(st.session_state.keys()):
        if key not in keep:
            del st.session_state[key]
    st.session_state.step = 0
    init_session_state()
