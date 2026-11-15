"""ATS-friendly resume builder."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.exporters import export_docx, export_pdf
from utils.resume_builder import (
    build_resume,
    generate_project_responsibilities,
    render_preview_markdown,
    re_split,
    responsibilities_to_text,
)
from utils.resume_parser import parse_reference_resume
from utils.state import (
    ROLE_FOCUS_OPTIONS,
    ROLE_TITLE_HINTS,
    STEPS,
    _empty_company,
    _empty_education,
    _empty_project,
    go_back,
    go_next,
    init_session_state,
    reset_wizard,
)

ASSETS = Path(__file__).resolve().parent / "assets"
HERO_IMAGE = ASSETS / "careerforge_hero.jpg"
LOGO_IMAGE = ASSETS / "careerforge_logo.jpg"

STEP_IMAGES = {
    0: (HERO_IMAGE, "CareerForge welcome hero with polished resume atmosphere"),
    1: (ASSETS / "step_personal.jpg", "Personal details — professional profile setup"),
    2: (ASSETS / "step_role.jpg", "Role focus — development, testing, and production paths"),
    3: (ASSETS / "step_technologies.jpg", "Technologies — skills and stack prioritization"),
    4: (ASSETS / "step_reference.jpg", "Reference resume upload inspiration"),
    5: (ASSETS / "step_experience.jpg", "Work experience timeline and projects"),
    6: (ASSETS / "step_education.jpg", "Education and certifications"),
    7: (ASSETS / "step_preview.jpg", "Resume preview and ATS polish"),
    8: (ASSETS / "step_download.jpg", "Download finished Word or PDF resume"),
}

st.set_page_config(
    page_title="CareerForge Resume Builder",
    page_icon=":material/auto_awesome:",
    layout="wide",
    initial_sidebar_state="auto",
)

init_session_state()

if LOGO_IMAGE.exists():
    st.logo(str(LOGO_IMAGE), size="large")


def is_mobile() -> bool:
    """Best-effort mobile detection for responsive stacking."""
    try:
        headers = st.context.headers
        ua = str(headers.get("User-Agent") or headers.get("user-agent") or "").lower()
    except Exception:
        ua = ""
    return any(token in ua for token in ("mobile", "android", "iphone", "ipod", "ipad"))


def render_step_banner(step_index: int | None = None) -> None:
    index = st.session_state.step if step_index is None else step_index
    image_path, alt = STEP_IMAGES.get(index, (None, ""))
    if image_path and Path(image_path).exists():
        st.image(str(image_path), width="stretch", alt=alt)
        st.space("small")


def responsive_columns(n: int = 2):
    """Use side-by-side columns on desktop; stack as one column on mobile."""
    if is_mobile() or n <= 1:
        return [st.container()]
    return st.columns(n)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## CareerForge")
        st.caption("Forge trust. Signal growth. Ship an ATS-ready resume.")
        st.progress(
            (st.session_state.step + 1) / len(STEPS),
            text=f"Step {st.session_state.step + 1} of {len(STEPS)} · {STEPS[st.session_state.step]}",
        )
        st.space("small")
        for index, label in enumerate(STEPS):
            if index == st.session_state.step:
                st.markdown(f":blue-badge[Now] **{label}**")
            elif index < st.session_state.step:
                st.markdown(f":green-badge[Done] {label}")
            else:
                st.markdown(f":gray-badge[Next] {label}")
        st.space("medium")
        st.markdown(":yellow-badge[Trust] :green-badge[Growth] :orange-badge[Achievement]")
        st.caption("Navy for competence · Teal for progress · Gold for confidence")
        st.space("small")
        if st.button(
            "Start over",
            icon=":material/restart_alt:",
            width="stretch",
            key="reset_wizard",
        ):
            reset_wizard()
            st.rerun()


def resume_payload() -> dict:
    return {
        "personal": st.session_state.personal,
        "role_focus": st.session_state.role_focus,
        "priority_technologies": st.session_state.priority_technologies,
        "all_technologies": st.session_state.all_technologies,
        "companies": st.session_state.companies,
        "education": st.session_state.education,
        "certifications": st.session_state.certifications,
        "achievements": st.session_state.achievements,
        "use_reference_format": st.session_state.use_reference_format,
        "reference_file_type": st.session_state.reference_file_type,
        "format_profile": st.session_state.reference_format_profile,
    }


def nav_buttons(*, show_back: bool = True, next_label: str = "Continue") -> None:
    cols = st.container(
        horizontal=True,
        gap="small",
        vertical_alignment="center",
        wrap=True,
        horizontal_alignment="left" if not is_mobile() else "center",
    )
    with cols:
        if show_back and st.session_state.step > 0:
            if st.button(
                "Back",
                icon=":material/arrow_back:",
                key=f"back_{st.session_state.step}",
                width="stretch" if is_mobile() else "content",
            ):
                go_back()
                st.rerun()
        if st.button(
            next_label,
            icon=":material/arrow_forward:",
            type="primary",
            key=f"next_{st.session_state.step}",
            width="stretch" if is_mobile() else "content",
        ):
            go_next()
            st.rerun()


def step_welcome() -> None:
    render_step_banner(0)

    st.title("CareerForge", text_alignment="center")
    st.header(
        "Build an ATS-friendly resume that sounds like you",
        text_alignment="center",
        icon=":material/auto_awesome:",
    )
    st.markdown(
        "Walk through your role, stack, and projects — then download a recruiter-ready Word or PDF resume.",
        text_alignment="center",
    )

    cta = st.container(horizontal=True, horizontal_alignment="center", wrap=True)
    with cta:
        if st.button(
            "Start building",
            icon=":material/rocket_launch:",
            type="primary",
            key="next_0",
            width="stretch" if is_mobile() else "content",
        ):
            go_next()
            st.rerun()

    st.space("large")
    st.subheader("Why it feels right", icon=":material/palette:")
    st.caption(
        "Color psychology is baked into the experience: navy for trust, teal for growth, "
        "and gold for achievement — cues associated with competence and career confidence."
    )

    features = st.container(horizontal=True, gap="large", wrap=True)
    with features:
        st.markdown(
            "**Role-aware writing**  \n"
            ":material/person_search: Development, testing, and production focus reshape every bullet."
        )
        st.markdown(
            "**Company by company**  \n"
            ":material/apartment: Capture tenure, stack, and project overview one employer at a time."
        )
        st.markdown(
            "**Reference-ready polish**  \n"
            ":material/upload_file: Upload Word/PDF guidance, then export a clean ATS layout."
        )


def step_personal() -> None:
    render_step_banner()
    st.header("Personal details", icon=":material/badge:")
    st.caption("These fields appear at the top of your ATS resume.")
    personal = st.session_state.personal

    with st.form("personal_form", border=True):
        cols = responsive_columns(2)
        with cols[0]:
            full_name = st.text_input("Full name", value=personal.get("full_name", ""))
            email = st.text_input("Email", value=personal.get("email", ""))
            phone = st.text_input("Phone", value=personal.get("phone", ""))
            location = st.text_input("Location", value=personal.get("location", ""), placeholder="City, Country")
        right = cols[0] if len(cols) == 1 else cols[1]
        with right:
            target_title = st.text_input(
                "Target job title",
                value=personal.get("target_title", ""),
                placeholder="e.g. Senior Java Developer",
            )
            linkedin = st.text_input("LinkedIn", value=personal.get("linkedin", ""))
            github = st.text_input("GitHub", value=personal.get("github", ""))
            portfolio = st.text_input("Portfolio / website", value=personal.get("portfolio", ""))

        summary = st.text_area(
            "Professional summary (optional)",
            value=personal.get("summary", ""),
            height=120,
            help="Leave blank to auto-generate a role-aware summary later.",
        )
        submitted = st.form_submit_button("Save and continue", type="primary", width="stretch")

    if submitted:
        if not full_name.strip() or not email.strip():
            st.error("Full name and email are required.", icon=":material/error:")
            return
        st.session_state.personal = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "linkedin": linkedin.strip(),
            "github": github.strip(),
            "portfolio": portfolio.strip(),
            "target_title": target_title.strip(),
            "summary": summary.strip(),
        }
        go_next()
        st.rerun()

    if st.session_state.step > 0:
        if st.button("Back", icon=":material/arrow_back:", key="personal_back"):
            go_back()
            st.rerun()


def step_role_focus() -> None:
    render_step_banner()
    st.header("Role focus", icon=":material/tune:")
    st.caption("This shapes summary language, bullet emphasis, and keyword placement.")

    role = st.segmented_control(
        "What best describes your work?",
        ROLE_FOCUS_OPTIONS,
        default=st.session_state.role_focus,
        key="role_focus_widget",
        width="stretch",
        wrap=True,
    )
    if role:
        st.session_state.role_focus = role

    hints = {
        "Only Development": "Emphasizes coding, architecture, feature delivery, and technical ownership.",
        "Development + Testing": "Balances feature work with test design, automation, and quality gates.",
        "Development + Production": "Highlights builds plus deployment, reliability, monitoring, and ops support.",
        "Development + Testing + Production": "End-to-end ownership across build, validate, and operate.",
    }
    current = st.session_state.role_focus
    st.success(hints[current], icon=":material/check_circle:", title=current)

    suggested = ROLE_TITLE_HINTS[current]
    if not st.session_state.personal.get("target_title"):
        st.session_state.personal["target_title"] = suggested
        st.caption(f"Suggested title set to **{suggested}** (you can edit it on the personal step later).")

    nav_buttons()


def step_technologies() -> None:
    render_step_banner()
    st.header("Technologies", icon=":material/memory:")
    st.caption("List everything you have used, then choose what should lead the resume.")

    all_techs_raw = st.text_area(
        "All technologies you have worked with",
        value=", ".join(st.session_state.all_technologies),
        height=100,
        placeholder="Java, Spring Boot, React, AWS, Selenium, Docker, Kubernetes...",
        help="Comma-separated list.",
    )
    all_techs = re_split(all_techs_raw)

    if all_techs:
        priority = st.pills(
            "Prioritize technologies for this resume",
            options=all_techs,
            selection_mode="multi",
            default=[t for t in st.session_state.priority_technologies if t in all_techs],
            key="priority_pills",
            help="These appear first in skills and get stronger keyword weight.",
        )
    else:
        priority = []
        st.warning("Add at least a few technologies to continue.", icon=":material/warning:")

    cols = st.container(horizontal=True, gap="small", wrap=True)
    with cols:
        if st.button(
            "Back",
            icon=":material/arrow_back:",
            key="tech_back",
            width="stretch" if is_mobile() else "content",
        ):
            go_back()
            st.rerun()
        if st.button(
            "Continue",
            icon=":material/arrow_forward:",
            type="primary",
            key="tech_next",
            width="stretch" if is_mobile() else "content",
        ):
            if not all_techs:
                st.error("Please enter your technologies.", icon=":material/error:")
            else:
                st.session_state.all_technologies = all_techs
                st.session_state.priority_technologies = list(priority or all_techs[:5])
                go_next()
                st.rerun()


def step_reference() -> None:
    render_step_banner()
    st.header("Reference resume (optional)", icon=":material/upload_file:")
    st.caption(
        "Upload a Word or PDF resume to prefill contact details and match section order, "
        "heading labels, fonts, margins, and alignment in the final resume."
    )

    uploaded = st.file_uploader(
        "Upload reference resume",
        type=["pdf", "docx"],
        accept_multiple_files=False,
        key="reference_uploader",
        help="PDF or DOCX only. DOCX gives the closest format match.",
    )

    if uploaded is not None:
        try:
            parsed = parse_reference_resume(uploaded.getvalue(), uploaded.name)
        except ValueError as exc:
            st.error(str(exc), icon=":material/error:")
        else:
            st.session_state.reference_file_name = uploaded.name
            st.session_state.reference_file_bytes = uploaded.getvalue()
            st.session_state.reference_file_type = parsed["file_type"]
            st.session_state.reference_text = parsed["text"]
            st.session_state.reference_format_profile = parsed.get("format_profile")
            st.session_state.use_reference_format = True
            hints = parsed["hints"]
            for key, value in hints.items():
                if value and not st.session_state.personal.get(key):
                    st.session_state.personal[key] = value
            profile = parsed.get("format_profile") or {}
            order = profile.get("section_order") or []
            labels = profile.get("section_labels") or {}
            st.success(
                f"Parsed **{uploaded.name}** and locked onto its format profile.",
                icon=":material/check_circle:",
                title="Reference format detected",
            )
            if order:
                st.caption(
                    "Detected section order: "
                    + " → ".join(labels.get(key, key) for key in order)
                )
            with st.expander("View extracted text"):
                st.text(parsed["text"][:4000] or "No extractable text found.")

    elif st.session_state.reference_file_name:
        st.info(
            f"Using previously uploaded file: **{st.session_state.reference_file_name}**",
            icon=":material/attach_file:",
        )

    has_reference = bool(st.session_state.reference_file_name)
    use_format = st.toggle(
        "Match uploaded reference format",
        value=st.session_state.use_reference_format if has_reference else False,
        key="use_reference_toggle",
        disabled=not has_reference,
        help=(
            "Uses detected section headings, order, alignment, fonts, and margins from the upload. "
            "DOCX references match more closely than PDF."
        ),
    )
    st.session_state.use_reference_format = bool(use_format and has_reference)
    if has_reference and st.session_state.use_reference_format:
        st.caption(
            ":green-badge[Format matching on] Exports will follow your reference structure."
        )
    elif has_reference:
        st.caption(":orange-badge[Format matching off] Using CareerForge ATS default layout.")

    nav_buttons(next_label="Continue to experience")


def step_experience() -> None:
    render_step_banner()
    st.header("Work experience", icon=":material/work:")
    st.caption(
        "Tell us how many companies you worked at — then fill them one by one. "
        "Project responsibilities are auto-generated from your role focus and project overview for you to edit."
    )

    expected = st.number_input(
        "How many companies have you worked at?",
        min_value=1,
        max_value=15,
        value=int(st.session_state.expected_company_count),
        step=1,
        key="expected_companies",
    )
    st.session_state.expected_company_count = int(expected)

    saved = st.session_state.companies
    current_index = len(saved) + 1
    if current_index > expected and saved:
        st.success(
            f"All {expected} compan{'y' if expected == 1 else 'ies'} captured.",
            icon=":material/done_all:",
            title="Experience complete",
        )
        for index, company in enumerate(saved, start=1):
            with st.expander(f"{index}. {company['company_name']} · {company['job_title']}"):
                st.write(
                    {
                        "Dates": f"{company.get('start_date')} – "
                        f"{'Present' if company.get('currently_working') else company.get('end_date')}",
                        "Projects": len(company.get("projects", [])),
                        "Technologies": ", ".join(company.get("technologies", [])),
                    }
                )
        cols = st.container(horizontal=True, gap="small")
        with cols:
            if st.button("Back", icon=":material/arrow_back:", key="exp_done_back"):
                go_back()
                st.rerun()
            if st.button(
                "Edit last company",
                icon=":material/edit:",
                key="edit_last_company",
            ):
                st.session_state.company_draft = saved.pop()
                st.session_state.companies = saved
                st.session_state.reviewing_responsibilities = False
                st.rerun()
            if st.button(
                "Continue",
                icon=":material/arrow_forward:",
                type="primary",
                key="exp_done_next",
            ):
                go_next()
                st.rerun()
        return

    st.subheader(f"Company {min(current_index, expected)} of {expected}")
    draft = st.session_state.company_draft
    project = st.session_state.project_draft

    if st.session_state.reviewing_responsibilities:
        _render_responsibility_review(draft, project, saved)
        return

    with st.form(f"company_form_{len(saved)}", border=True, clear_on_submit=False):
        company_cols = responsive_columns(2)
        with company_cols[0]:
            company_name = st.text_input("Company name", value=draft.get("company_name", ""))
            job_title = st.text_input("Job title", value=draft.get("job_title", ""))
            location = st.text_input("Company location", value=draft.get("location", ""))
            technologies = st.text_input(
                "Technologies used here",
                value=", ".join(draft.get("technologies", [])),
                placeholder="Comma-separated",
            )
        company_right = company_cols[0] if len(company_cols) == 1 else company_cols[1]
        with company_right:
            start_date = st.text_input(
                "Start date",
                value=draft.get("start_date", ""),
                placeholder="Jan 2022",
            )
            currently = st.checkbox(
                "I currently work here",
                value=bool(draft.get("currently_working")),
            )
            end_date = st.text_input(
                "End date",
                value=draft.get("end_date", ""),
                placeholder="Dec 2024 or Present",
                disabled=currently,
            )

        st.markdown("#### Project overview")
        st.caption(
            "Describe the project clearly — CareerForge will draft elaborate responsibilities "
            f"for your **{st.session_state.role_focus}** focus, then let you edit them."
        )
        project_cols = responsive_columns(2)
        with project_cols[0]:
            project_name = st.text_input("Project name", value=project.get("name", ""))
            project_tenure = st.text_input(
                "Project tenure",
                value=project.get("tenure", ""),
                placeholder="6 months / Jan 2023 – Jun 2023",
            )
            project_role = st.text_input(
                "Your role on the project",
                value=project.get("role", "") or draft.get("job_title", ""),
            )
        project_right = project_cols[0] if len(project_cols) == 1 else project_cols[1]
        with project_right:
            project_tech = st.text_input(
                "Project technologies",
                value=project.get("technologies", ""),
                placeholder="Comma-separated",
            )
            project_desc = st.text_area(
                "Project information / overview",
                value=project.get("description", ""),
                height=120,
                help="Required. What the project does, domain, key modules, users, and outcomes.",
            )

        add_another_project = st.checkbox(
            "After saving, add another project for the same company"
        )
        submitted = st.form_submit_button(
            "Generate project responsibilities",
            type="primary",
            width="stretch",
            icon=":material/auto_awesome:",
        )

    if submitted:
        if not company_name.strip() or not job_title.strip() or not start_date.strip():
            st.error("Company name, job title, and start date are required.", icon=":material/error:")
            return
        if not project_name.strip() or not project_desc.strip():
            st.error(
                "Project name and project overview are required to generate responsibilities.",
                icon=":material/error:",
            )
            return

        company_payload = {
            "company_name": company_name.strip(),
            "job_title": job_title.strip(),
            "location": location.strip(),
            "start_date": start_date.strip(),
            "end_date": "" if currently else end_date.strip(),
            "currently_working": currently,
            "technologies": re_split(technologies),
            "responsibilities": draft.get("responsibilities", ""),
            "projects": list(draft.get("projects", [])),
        }
        generated = generate_project_responsibilities(
            role_focus=st.session_state.role_focus,
            project_name=project_name.strip(),
            project_role=project_role.strip() or job_title.strip(),
            project_overview=project_desc.strip(),
            technologies=project_tech.strip() or ", ".join(re_split(technologies)),
            tenure=project_tenure.strip(),
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            priority_technologies=st.session_state.priority_technologies,
        )
        st.session_state.company_draft = company_payload
        st.session_state.project_draft = {
            "name": project_name.strip(),
            "tenure": project_tenure.strip(),
            "role": project_role.strip() or job_title.strip(),
            "description": project_desc.strip(),
            "technologies": project_tech.strip(),
            "responsibilities": responsibilities_to_text(generated),
            "achievements": "",
        }
        st.session_state.add_another_project_pending = bool(add_another_project)
        st.session_state.reviewing_responsibilities = True
        st.rerun()

    if st.button("Back", icon=":material/arrow_back:", key="exp_back"):
        go_back()
        st.rerun()

    if saved:
        st.divider()
        st.markdown("#### Saved companies")
        for index, company in enumerate(saved, start=1):
            st.markdown(
                f"{index}. **{company['company_name']}** — {company['job_title']} "
                f"(:blue-badge[{len(company.get('projects', []))} projects])"
            )


def _render_responsibility_review(draft: dict, project: dict, saved: list) -> None:
    st.markdown("#### Review generated project responsibilities")
    st.info(
        "These bullets were drafted from your role focus and project overview. "
        "Delete lines you do not need, rewrite any bullet, or add missing points — one per line.",
        icon=":material/edit_note:",
        title="Edit before saving",
    )

    st.markdown(
        f"**{project.get('name', 'Project')}** · {project.get('role', '')} · "
        f":blue-badge[{st.session_state.role_focus}]"
    )
    if project.get("description"):
        with st.expander("Project overview used for generation"):
            st.write(project["description"])

    editor_key = f"generated_responsibilities_editor_{st.session_state.responsibilities_editor_version}"
    edited = st.text_area(
        "Project responsibilities",
        value=project.get("responsibilities", ""),
        height=280 if is_mobile() else 320,
        key=editor_key,
        help="Keep each responsibility on its own line. Start a line with • or - if you like.",
    )

    st.markdown("#### Regenerate with your changes")
    st.caption(
        "Tell CareerForge what to change — for example: more testing, add leadership, "
        "make shorter, include Kafka, remove collaboration bullets."
    )
    with st.form("regen_feedback_form", border=True, clear_on_submit=False):
        feedback = st.text_area(
            "What changes do you want in the responsibilities?",
            value=st.session_state.get("regen_feedback", ""),
            height=110,
            placeholder=(
                "Examples:\n"
                "• Make them more concise\n"
                "• Add more testing and Selenium automation\n"
                "• Include production support and monitoring\n"
                "• Emphasize API design and mentorship"
            ),
            help="Required for regeneration so the new draft matches your intent.",
        )
        quick = st.pills(
            "Quick change themes",
            options=[
                "More concise",
                "More technical",
                "More testing",
                "More production",
                "Add leadership",
                "Add measurable impact",
            ],
            selection_mode="multi",
            key="regen_quick_themes",
        )
        regen_submitted = st.form_submit_button(
            "Apply regeneration",
            icon=":material/refresh:",
            type="secondary",
            width="stretch",
        )

    if regen_submitted:
        theme_text = ", ".join(quick or [])
        combined_feedback = "\n".join(
            part for part in [feedback.strip(), theme_text] if part
        ).strip()
        if not combined_feedback:
            st.error(
                "Please describe what should change before regenerating.",
                icon=":material/error:",
            )
        else:
            regenerated = generate_project_responsibilities(
                role_focus=st.session_state.role_focus,
                project_name=project.get("name", ""),
                project_role=project.get("role", ""),
                project_overview=project.get("description", ""),
                technologies=project.get("technologies", ""),
                tenure=project.get("tenure", ""),
                company_name=draft.get("company_name", ""),
                job_title=draft.get("job_title", ""),
                priority_technologies=st.session_state.priority_technologies,
                change_requests=combined_feedback,
            )
            st.session_state.regen_feedback = combined_feedback
            st.session_state.project_draft["responsibilities"] = responsibilities_to_text(
                regenerated
            )
            st.session_state.responsibilities_editor_version += 1
            st.success(
                "Responsibilities regenerated from your change requests. Review and edit below.",
                icon=":material/auto_awesome:",
                title="Updated draft ready",
            )
            st.rerun()

    action_cols = st.container(horizontal=True, gap="small", wrap=True)
    with action_cols:
        if st.button(
            "Back to project details",
            icon=":material/arrow_back:",
            key="resp_back",
            width="stretch" if is_mobile() else "content",
        ):
            st.session_state.reviewing_responsibilities = False
            st.rerun()
        save_label = (
            "Save project & add another"
            if st.session_state.add_another_project_pending
            else "Save company"
        )
        if st.button(
            save_label,
            icon=":material/save:",
            type="primary",
            key="resp_save",
            width="stretch" if is_mobile() else "content",
        ):
            project_payload = {
                **project,
                "responsibilities": edited.strip(),
            }
            company_payload = {
                **draft,
                "projects": [*list(draft.get("projects", [])), project_payload],
            }
            if st.session_state.add_another_project_pending:
                st.session_state.company_draft = company_payload
                st.session_state.project_draft = _empty_project()
                st.session_state.add_another_project_pending = False
                st.session_state.reviewing_responsibilities = False
                st.session_state.regen_feedback = ""
                st.session_state.responsibilities_editor_version += 1
                st.success(
                    "Project saved with your edited responsibilities. Add the next project.",
                    icon=":material/task_alt:",
                )
                st.rerun()

            st.session_state.companies = [*saved, company_payload]
            st.session_state.company_draft = _empty_company()
            st.session_state.project_draft = _empty_project()
            st.session_state.reviewing_responsibilities = False
            st.session_state.add_another_project_pending = False
            st.session_state.regen_feedback = ""
            st.session_state.responsibilities_editor_version += 1
            st.rerun()


def step_education() -> None:
    render_step_banner()
    st.header("Education & extras", icon=":material/school:")
    st.caption("Add degrees, certifications, and standout achievements.")

    draft = st.session_state.education_draft
    with st.form("education_form", border=True):
        edu_cols = responsive_columns(2)
        with edu_cols[0]:
            degree = st.text_input("Degree / program", value=draft.get("degree", ""))
            institution = st.text_input("Institution", value=draft.get("institution", ""))
            location = st.text_input("Location", value=draft.get("location", ""))
        edu_right = edu_cols[0] if len(edu_cols) == 1 else edu_cols[1]
        with edu_right:
            start_year = st.text_input("Start year", value=draft.get("start_year", ""))
            end_year = st.text_input("End year", value=draft.get("end_year", ""))
            details = st.text_input("Details (GPA, honors, etc.)", value=draft.get("details", ""))
        add_edu = st.form_submit_button("Add education entry", width="stretch")

    if add_edu:
        if degree.strip() and institution.strip():
            st.session_state.education = [
                *st.session_state.education,
                {
                    "degree": degree.strip(),
                    "institution": institution.strip(),
                    "location": location.strip(),
                    "start_year": start_year.strip(),
                    "end_year": end_year.strip(),
                    "details": details.strip(),
                },
            ]
            st.session_state.education_draft = _empty_education()
            st.rerun()
        else:
            st.error("Degree and institution are required to add an entry.", icon=":material/error:")

    if st.session_state.education:
        for index, edu in enumerate(st.session_state.education):
            cols = st.container(horizontal=True, gap="small", vertical_alignment="center")
            with cols:
                st.markdown(f"**{edu['degree']}** — {edu['institution']}")
                if st.button("Remove", key=f"remove_edu_{index}", icon=":material/delete:"):
                    st.session_state.education.pop(index)
                    st.rerun()

    st.session_state.certifications = st.text_area(
        "Certifications (one per line)",
        value=st.session_state.certifications,
        height=90,
        key="certs_area",
    )
    st.session_state.achievements = st.text_area(
        "Key achievements (one per line)",
        value=st.session_state.achievements,
        height=90,
        key="achievements_area",
    )

    nav_buttons(next_label="Generate preview")


def step_preview() -> None:
    render_step_banner()
    st.header("Resume preview", icon=":material/preview:")
    resume = build_resume(resume_payload())
    st.session_state.generated_resume = resume

    if st.session_state.use_reference_format and st.session_state.reference_format_profile:
        st.caption(
            ":green-badge[Reference format] Preview uses your uploaded resume's section order and labels."
        )

    if not st.session_state.personal.get("full_name") or not st.session_state.companies:
        st.warning(
            "Add personal details and at least one company before downloading.",
            icon=":material/warning:",
            title="Almost there",
        )

    if is_mobile():
        metrics = st.container(horizontal=True, gap="small", wrap=True)
        with metrics:
            st.metric("Companies", len(resume["experience"]))
            st.metric(
                "Priority technologies",
                len(resume["skills"]["Priority technologies"]),
            )
        st.markdown("#### ATS checklist")
        for note in resume["ats_notes"]:
            st.markdown(f"- {note}")
        with st.container(border=True):
            st.markdown(render_preview_markdown(resume))
    else:
        left, right = st.columns((2, 1), gap="large")
        with left:
            with st.container(border=True):
                st.markdown(render_preview_markdown(resume))
        with right:
            st.markdown("#### ATS checklist")
            for note in resume["ats_notes"]:
                st.markdown(f"- {note}")
            st.markdown("#### Snapshot")
            st.metric("Companies", len(resume["experience"]))
            st.metric(
                "Priority technologies",
                len(resume["skills"]["Priority technologies"]),
            )
            st.metric("Role focus", resume["role_focus"])

    nav_buttons(next_label="Choose download format")


def step_download() -> None:
    render_step_banner()
    st.header("Download your resume", icon=":material/download:")
    st.caption("Choose Word for easy editing, or PDF for polished sharing.")
    if LOGO_IMAGE.exists():
        brand = st.container(horizontal=True, horizontal_alignment="center", wrap=True)
        with brand:
            st.image(str(LOGO_IMAGE), width=96, alt="CareerForge logo")

    resume = build_resume(resume_payload())
    st.session_state.generated_resume = resume

    if st.session_state.use_reference_format and st.session_state.reference_format_profile:
        preferred = (
            "Word (.docx)"
            if st.session_state.reference_file_type == "docx"
            else "PDF (.pdf)"
        )
        st.info(
            f"Format matching is on. For the closest match to your uploaded "
            f"**{st.session_state.reference_file_name}**, download **{preferred}**.",
            icon=":material/content_copy:",
            title="Reference format active",
        )
    else:
        preferred = "PDF (.pdf)"

    safe_name = (st.session_state.personal.get("full_name") or "resume").replace(" ", "_")
    format_choice = st.segmented_control(
        "Download format",
        ["Word (.docx)", "PDF (.pdf)", "Both"],
        default=preferred,
        key="download_format",
    )

    if format_choice in ("Word (.docx)", "Both"):
        docx_bytes = export_docx(resume)
        st.download_button(
            "Download Word resume",
            data=docx_bytes,
            file_name=f"{safe_name}_ATS_Resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            icon=":material/description:",
            type="primary",
            width="stretch",
            key="download_docx",
        )

    if format_choice in ("PDF (.pdf)", "Both"):
        pdf_bytes = export_pdf(resume)
        st.download_button(
            "Download PDF resume",
            data=pdf_bytes,
            file_name=f"{safe_name}_ATS_Resume.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            type="primary",
            width="stretch",
            key="download_pdf",
        )

    st.success(
        "Your ATS-friendly resume is ready. Update details anytime by going back through the steps.",
        icon=":material/celebration:",
        title="All set",
    )

    cols = st.container(horizontal=True, gap="small")
    with cols:
        if st.button("Back to preview", icon=":material/arrow_back:", key="dl_back"):
            go_back()
            st.rerun()
        if st.button("Build another resume", icon=":material/add:", key="dl_reset"):
            reset_wizard()
            st.rerun()


render_sidebar()

step = st.session_state.step
if step == 0:
    step_welcome()
elif step == 1:
    step_personal()
elif step == 2:
    step_role_focus()
elif step == 3:
    step_technologies()
elif step == 4:
    step_reference()
elif step == 5:
    step_experience()
elif step == 6:
    step_education()
elif step == 7:
    step_preview()
elif step == 8:
    step_download()
else:
    st.session_state.step = 0
    st.rerun()
