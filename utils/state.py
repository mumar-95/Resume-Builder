"""Session state helpers for the resume wizard."""

from __future__ import annotations

import streamlit as st

STEPS = [
    "Welcome",
    "Personal",
    "Role & focus",
    "Technologies",
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

REGENERABLE_SECTIONS = [
    "Professional Summary",
    "Technical Skills",
]


def migrate_step_indices() -> None:
    """Remap wizard steps after 'Reference resume' was removed from STEPS."""
    if st.session_state.get("_steps_no_reference"):
        st.session_state.step = min(int(st.session_state.get("step") or 0), len(STEPS) - 1)
        return
    old_step = int(st.session_state.get("step") or 0)
    # Previous order: 0..3 same, 4=Reference, 5=Experience ... 8=Download
    if old_step >= 5:
        st.session_state.step = old_step - 1
    # old_step == 4 (Reference) → Experience at the same index
    st.session_state.step = min(int(st.session_state.get("step") or 0), len(STEPS) - 1)
    st.session_state._steps_no_reference = True


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
            "professional_title": "Software Engineer",
            "years_of_experience": "",
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
        "reference_content_hash": None,
        "reference_uploader_version": 0,
        "use_reference_format": False,
        "generated_resume": None,
        "company_index": 0,
        "expected_company_count": 1,
        # company → project → responsibilities wizard phases
        "experience_phase": "company",  # company | project | responsibilities
        "reviewing_responsibilities": False,
        "add_another_project_pending": False,
        "editing_company_index": None,
        "editing_project_index": None,
        "regen_feedback": "",
        "responsibilities_editor_version": 0,
        # Independent section state — regeneration must not wipe approved responsibilities.
        "section_summary": "",
        "section_summary_locked": False,
        "section_skills_note": "",
        "summary_regen_count": 0,
        "skills_regen_count": 0,
        "responsibility_regen_count": 0,
        "last_regen_message": "",
        "approved_key_responsibilities": {},  # project key -> approved bullet text
        "responsibility_raw_draft": "",
        "responsibility_enhanced_draft": "",
        "responsibility_phase": "input",  # input | enhanced | approved
        "responsibility_regen_reflection": None,  # {before, after, changes}
        "resume_template": "Harmonized",
        "selected_regen_section": "Professional Summary",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    # Ensure nested personal keys exist for older sessions.
    personal = st.session_state.get("personal") or {}
    if "years_of_experience" not in personal:
        personal["years_of_experience"] = ""
        st.session_state.personal = personal
    migrate_step_indices()


def clear_reference_cache(*, bump_uploader: bool = False) -> None:
    """Drop any cached reference resume so the next upload is parsed fresh."""
    st.session_state.reference_file_name = None
    st.session_state.reference_file_bytes = None
    st.session_state.reference_file_type = None
    st.session_state.reference_text = ""
    st.session_state.reference_format_profile = None
    st.session_state.reference_content_hash = None
    st.session_state.use_reference_format = False
    st.session_state.generated_resume = None
    if bump_uploader:
        st.session_state.reference_uploader_version = (
            int(st.session_state.get("reference_uploader_version", 0)) + 1
        )
        # Force Streamlit to remount the uploader widget without stale file state.
        uploader_key = f"reference_uploader_{st.session_state.reference_uploader_version - 1}"
        if uploader_key in st.session_state:
            del st.session_state[uploader_key]
        if "use_reference_toggle" in st.session_state:
            del st.session_state["use_reference_toggle"]


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
        "client_name": "",
        "domain": "",
        "tenure": "",
        "role": "",
        "description": "",
        "technologies": "",
        "responsibilities": "",
        "responsibilities_approved": False,
        "responsibilities_raw": "",
        "achievements": "",
        "key_contributions": "",
        "challenges_solved": "",
        "owned_areas": "",
        "impact_outcomes": "",
        "collaboration": "",
    }


def project_responsibility_key(company_name: str, project_name: str) -> str:
    return f"{(company_name or '').strip().lower()}::{(project_name or '').strip().lower()}"


def store_approved_responsibilities(company_name: str, project_name: str, text: str) -> None:
    key = project_responsibility_key(company_name, project_name)
    approved = dict(st.session_state.get("approved_key_responsibilities") or {})
    approved[key] = text
    st.session_state.approved_key_responsibilities = approved


def get_approved_responsibilities(company_name: str, project_name: str) -> str | None:
    key = project_responsibility_key(company_name, project_name)
    return (st.session_state.get("approved_key_responsibilities") or {}).get(key)


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
