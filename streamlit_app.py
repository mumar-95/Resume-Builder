"""ATS-friendly resume builder."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.exporters import export_docx, export_pdf
from utils.professions import PROFESSIONAL_TITLES, profession_image
from utils.responsibility_enhancer import (
    enhance_responsibilities,
    responsibilities_to_text as enhanced_to_text,
)
from utils.resume_builder import (
    build_resume,
    regenerate_skills_order,
    regenerate_summary,
    render_preview_html,
    render_preview_markdown,
    re_split,
)
from utils.state import (
    REGENERABLE_SECTIONS,
    ROLE_FOCUS_OPTIONS,
    ROLE_TITLE_HINTS,
    STEPS,
    _empty_company,
    _empty_education,
    _empty_project,
    get_approved_responsibilities,
    go_back,
    go_next,
    init_session_state,
    reset_wizard,
    store_approved_responsibilities,
)
from utils.backgrounds import atmosphere_meta, page_atmosphere_css
from utils.templates import (
    TEMPLATE_CATEGORIES,
    TEMPLATE_OPTIONS,
    TEMPLATES,
    example_resume_for_template,
    recommend_templates_for_title,
)

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_IMAGE = ASSETS / "careerforge_logo.jpg"

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


def render_page_atmosphere() -> None:
    """Background image behind the app; opaque content panels in the foreground."""
    template_name = st.session_state.get("resume_template") or "Harmonized"
    meta = TEMPLATES.get(template_name) or {}
    accent = str(meta.get("accent_color") or "#0E7C86")
    # Welcome uses a strong hero backdrop; other steps stay softer for readability.
    intensity = "hero" if int(st.session_state.get("step") or 0) == 0 else "balanced"
    css = page_atmosphere_css(
        template_name,
        accent_color=accent,
        intensity=intensity,
    )
    if css:
        st.html(css)


def render_step_banner(step_index: int | None = None) -> None:
    """
    Light decorative strip only — no opaque full-bleed image that covers content.

    Page atmosphere (transparent background) is handled separately so sections
    stay readable on solid panels above the artwork.
    """
    index = st.session_state.step if step_index is None else step_index
    template_name = st.session_state.get("resume_template") or "Harmonized"
    template_meta = TEMPLATES.get(template_name) or {}
    accent = str(template_meta.get("accent_color") or "#0E7C86")
    atmosphere = atmosphere_meta(template_name)

    st.html(
        f"""
        <div class="cf-atmosphere-strip" style="background: linear-gradient(90deg, {accent}, transparent 85%);"></div>
        """
    )

    # Personal step: compact profession cue (not a full opaque banner).
    if index == 1:
        title = st.session_state.personal.get("professional_title") or "Software Engineer"
        image_path, alt = profession_image(title)
        if image_path and Path(image_path).exists():
            cue = st.container(horizontal=True, gap="small", vertical_alignment="center", wrap=True)
            with cue:
                st.image(str(image_path), width=112, alt=alt)
                st.caption(
                    f"{title} · backdrop: {atmosphere.get('label')} "
                    f"({template_name})"
                )
            st.space("small")
            return

    step_label = STEPS[index] if 0 <= index < len(STEPS) else "CareerForge"
    st.caption(
        f"{step_label} · template backdrop: **{atmosphere.get('label')}** "
        f"for **{template_name}** (transparent behind content)"
    )


def responsive_columns(n: int = 2):
    """Use side-by-side columns on desktop; stack as one column on mobile."""
    if is_mobile() or n <= 1:
        return [st.container()]
    return st.columns(n)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## CareerForge")
        title = st.session_state.personal.get("target_title") or (
            st.session_state.personal.get("professional_title") or ""
        )
        if title == "Other":
            title = st.session_state.personal.get("target_title") or "Custom title"
        st.caption(title if title else "ATS-ready resume builder")
        st.progress(
            (st.session_state.step + 1) / len(STEPS),
            text=f"Step {st.session_state.step + 1} of {len(STEPS)} · {STEPS[st.session_state.step]}",
        )
        st.space("small")
        st.caption("Jump to any section")
        for index, label in enumerate(STEPS):
            is_current = index == st.session_state.step
            is_done = index < st.session_state.step
            if is_current:
                button_label = f"→ {label}"
                icon = ":material/play_arrow:"
            elif is_done:
                button_label = f"✓ {label}"
                icon = ":material/check_circle:"
            else:
                button_label = label
                icon = ":material/radio_button_unchecked:"
            if st.button(
                button_label,
                key=f"nav_step_{index}",
                width="stretch",
                type="primary" if is_current else "secondary",
                icon=icon,
                disabled=is_current,
                help=f"Go to {label}",
            ):
                st.session_state.step = index
                st.rerun()
        st.space("medium")
        if st.button(
            "Start over",
            icon=":material/restart_alt:",
            width="stretch",
            key="reset_wizard",
        ):
            reset_wizard()
            st.rerun()


def resume_payload() -> dict:
    personal = dict(st.session_state.personal)
    if st.session_state.get("section_summary"):
        personal["summary"] = st.session_state.section_summary
    return {
        "personal": personal,
        "role_focus": st.session_state.role_focus,
        "priority_technologies": st.session_state.priority_technologies,
        "all_technologies": st.session_state.all_technologies,
        "companies": st.session_state.companies,
        "education": st.session_state.education,
        "certifications": st.session_state.certifications,
        "achievements": st.session_state.achievements,
        "use_reference_format": False,
        "reference_file_type": None,
        "format_profile": None,
        "section_summary": st.session_state.get("section_summary", ""),
        "approved_key_responsibilities": st.session_state.get(
            "approved_key_responsibilities", {}
        ),
        "resume_template": st.session_state.get("resume_template", "Harmonized"),
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

    # Image lives in the hero banner; gallery sits on a solid white panel for clarity.
    template_name = st.session_state.get("resume_template") or "Harmonized"
    st.html(
        """
        <section class="cf-welcome-hero" aria-label="CareerForge welcome">
          <div class="cf-welcome-hero-inner">
            <h1>CareerForge</h1>
            <h2>Professional ATS resume builder</h2>
            <p>
              Choose a resume template below, then build a recruiter-ready resume
              as Word or PDF — with your experience, skills, and story.
            </p>
          </div>
        </section>
        """
    )

    st.html(
        f"""
        <div class="cf-welcome-selected">
          Currently selected template: <span>{template_name}</span>
        </div>
        """
    )

    with st.container(border=True):
        _render_template_gallery(location="welcome")

        st.space("small")
        cta = st.container(horizontal=True, horizontal_alignment="center", wrap=True)
        with cta:
            if st.button(
                f"Begin with {template_name}",
                icon=":material/arrow_forward:",
                type="primary",
                key="next_0",
                width="stretch" if is_mobile() else "content",
            ):
                go_next()
                st.rerun()


def _render_template_card(
    name: str, *, location: str, current: str, category: str = "all"
) -> None:
    meta = TEMPLATES.get(name) or {}
    template_id = str(meta.get("template_id") or name).replace(" ", "_").lower()
    category_slug = "".join(ch if ch.isalnum() else "_" for ch in category.lower())
    widget_key = f"tmpl_{location}_{category_slug}_{template_id}"
    selected = name == current
    with st.container(border=True):
        if selected:
            st.html('<div class="cf-template-selected-badge">SELECTED</div>')
        st.markdown(f"**{name}**")
        if selected:
            st.success(f"**{name}** is your active template", icon=":material/check_circle:")
        best_for = meta.get("best_for") or []
        if best_for:
            st.caption("Best for: " + " · ".join(best_for[:3]))
        st.caption(meta.get("description") or "")
        st.caption(f"Format: {meta.get('structure_hint') or 'Professional layout'}")
        st.caption(f"Backdrop: {atmosphere_meta(name).get('label')}")
        example = example_resume_for_template(name)
        person = example.get("personal") or {}
        job = (example.get("experience") or [{}])[0]
        st.markdown(
            f"**Example:** {person.get('full_name', '')} — "
            f"{person.get('target_title', '')}"
        )
        st.caption(
            f"{job.get('job_title', '')} at {job.get('company_name', '')} · "
            f"{(job.get('projects') or [{}])[0].get('domain', '')}"
        )
        with st.expander("View full resume example", expanded=False):
            st.html(render_preview_html(example))
        if st.button(
            "✓ Selected" if selected else "Use this template",
            key=widget_key,
            type="primary" if selected else "secondary",
            width="stretch",
            disabled=selected,
            icon=":material/check_circle:" if selected else ":material/style:",
        ):
            st.session_state.resume_template = name
            st.toast(f"Template set to {name}", icon=":material/check:")
            st.rerun()


def _render_template_gallery(*, location: str) -> None:
    """Template picker with mini resume examples. Selection never clears user data."""
    current = st.session_state.get("resume_template") or "Harmonized"
    if current not in TEMPLATE_OPTIONS:
        current = "Harmonized"
        st.session_state.resume_template = current

    st.subheader("Resume Templates", icon=":material/dashboard:")
    st.markdown(f"**Selected template: {current}**")
    st.caption(
        f"{len(TEMPLATE_OPTIONS)} layouts available. "
        "Switching templates only changes layout — your details stay intact."
    )

    title_hint = (
        st.session_state.personal.get("target_title")
        or st.session_state.personal.get("professional_title")
        or ""
    )
    recommended = recommend_templates_for_title(title_hint)
    if recommended:
        st.info(
            "Suggested for your role: " + ", ".join(f"**{n}**" for n in recommended[:4]),
            icon=":material/recommend:",
        )

    filter_cols = responsive_columns(2)
    with filter_cols[0]:
        search = st.text_input(
            "Search templates",
            value="",
            placeholder="e.g. ATS, corporate, modern, sidebar…",
            key=f"tmpl_search_{location}",
        ).strip().lower()
    with filter_cols[-1]:
        sort_mode = st.selectbox(
            "Sort by",
            ["Recommended first", "A–Z", "ATS first", "Modern first"],
            key=f"tmpl_sort_{location}",
        )

    def _matches(name: str) -> bool:
        if not search:
            return True
        meta = TEMPLATES.get(name) or {}
        blob = " ".join(
            [
                name,
                str(meta.get("description") or ""),
                str(meta.get("structure_hint") or ""),
                " ".join(meta.get("best_for") or []),
            ]
        ).lower()
        return search in blob

    def _sort_key(name: str) -> tuple:
        meta = TEMPLATES.get(name) or {}
        layout = str(meta.get("layout_id") or "")
        if sort_mode == "A–Z":
            return (0, name.lower())
        if sort_mode == "ATS first":
            return (0 if "ats" in name.lower() or "ats" in layout else 1, name.lower())
        if sort_mode == "Modern first":
            return (0 if layout in {"clean", "harmonized", "modern_professional", "nordic", "impact"} else 1, name.lower())
        # Recommended first
        rank = recommended.index(name) if name in recommended else 99
        return (rank, name.lower())

    category_tabs = st.tabs(["All"] + list(TEMPLATE_CATEGORIES.keys()))
    tab_groups = [("All", list(TEMPLATE_OPTIONS))] + list(TEMPLATE_CATEGORIES.items())
    for tab, (category, names) in zip(category_tabs, tab_groups):
        with tab:
            filtered = sorted([n for n in names if _matches(n)], key=_sort_key)
            if not filtered:
                st.caption("No templates match your search.")
                continue
            cols_per_row = 1 if is_mobile() else 3
            for start in range(0, len(filtered), cols_per_row):
                chunk = filtered[start : start + cols_per_row]
                columns = st.columns(len(chunk))
                for col, name in zip(columns, chunk):
                    with col:
                        _render_template_card(
                            name,
                            location=location,
                            current=current,
                            category=category,
                        )


def step_personal() -> None:
    personal = st.session_state.personal
    stored_title = personal.get("professional_title") or "Software Engineer"
    if stored_title in PROFESSIONAL_TITLES:
        current_title = stored_title
    elif stored_title and stored_title != "Other":
        current_title = "Other"
    else:
        current_title = "Other" if personal.get("target_title") else "Software Engineer"

    # Title selection outside the form so profession artwork updates immediately.
    st.header("Personal details", icon=":material/badge:")
    st.caption("Contact details and professional title appear at the top of your ATS resume.")
    selected_title = st.selectbox(
        "Professional name / job title",
        options=PROFESSIONAL_TITLES,
        index=PROFESSIONAL_TITLES.index(current_title),
        key="professional_title_select",
        help="Choose your closest title, or Other if it is not listed.",
    )
    st.session_state.personal["professional_title"] = selected_title

    custom_title_outside = ""
    if selected_title == "Other":
        custom_title_outside = st.text_input(
            "Enter your job title",
            value=personal.get("target_title", "")
            if personal.get("professional_title") == "Other" or personal.get("target_title") not in PROFESSIONAL_TITLES
            else "",
            placeholder="e.g. Salesforce Developer, Cloud Architect, Product Analyst",
            key="custom_job_title_input",
            help="Required when your title is not in the dropdown. Used on the resume headline and Professional Summary.",
        )
        if not custom_title_outside.strip():
            st.warning(
                "Your title is not in the list — please type the exact job title you want on the resume.",
                icon=":material/edit:",
            )
    else:
        if not personal.get("target_title") or personal.get("target_title") == "Other":
            st.session_state.personal["target_title"] = selected_title

    years_default = personal.get("years_of_experience") or ""
    try:
        years_value = float(str(years_default).replace("+", "").strip() or 0)
    except ValueError:
        years_value = 0.0
    years_of_experience = st.number_input(
        "Total years of experience",
        min_value=0.0,
        max_value=50.0,
        value=years_value,
        step=0.5,
        help="Used in the Professional Summary (for example: “5+ years of experience”).",
        key="years_of_experience_input",
    )

    render_step_banner()

    with st.form("personal_form", border=True):
        cols = responsive_columns(2)
        with cols[0]:
            full_name = st.text_input("Full name", value=personal.get("full_name", ""))
            email = st.text_input("Email", value=personal.get("email", ""))
            phone = st.text_input("Phone", value=personal.get("phone", ""))
            location = st.text_input(
                "Location",
                value=personal.get("location", ""),
                placeholder="City, Country",
            )
        right = cols[0] if len(cols) == 1 else cols[1]
        with right:
            if selected_title != "Other":
                custom_title = st.text_input(
                    "Exact title for resume (optional)",
                    value=personal.get("target_title", "") or selected_title,
                    placeholder="e.g. Senior Informatica Developer",
                    help="Overrides the dropdown title on the resume if provided.",
                )
            else:
                custom_title = custom_title_outside
                st.caption(f"Resume title: **{custom_title_outside.strip() or 'Not set yet'}**")
            linkedin = st.text_input("LinkedIn", value=personal.get("linkedin", ""))
            github = st.text_input("GitHub", value=personal.get("github", ""))
            portfolio = st.text_input("Portfolio / website", value=personal.get("portfolio", ""))

        summary = st.text_area(
            "Professional summary (optional)",
            value=personal.get("summary", "") or st.session_state.get("section_summary", ""),
            height=120,
            help="Leave blank to auto-generate a role-aware summary that includes your years of experience.",
        )
        submitted = st.form_submit_button("Save and continue", type="primary", width="stretch")

    if submitted:
        if not full_name.strip() or not email.strip():
            st.error("Full name and email are required.", icon=":material/error:")
            return
        if selected_title == "Other" and not str(custom_title or "").strip():
            st.error(
                "Please enter your job title — it is not in the dropdown list.",
                icon=":material/error:",
            )
            return
        resolved_title = str(custom_title or "").strip() or selected_title
        years_str = (
            str(int(years_of_experience))
            if float(years_of_experience).is_integer()
            else str(years_of_experience)
        )
        st.session_state.personal = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "linkedin": linkedin.strip(),
            "github": github.strip(),
            "portfolio": portfolio.strip(),
            "professional_title": selected_title,
            "target_title": resolved_title,
            "years_of_experience": years_str,
            "summary": summary.strip(),
        }
        st.session_state.section_summary = summary.strip()
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


def step_experience() -> None:
    render_step_banner()
    st.header("Work experience", icon=":material/work:")
    st.caption(
        "Enter company/employment details first, then add one or more projects under that company. "
        "Approved Key Responsibilities stay locked during regeneration."
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
    draft = st.session_state.company_draft
    project = st.session_state.project_draft
    phase = st.session_state.get("experience_phase", "company")

    if st.session_state.reviewing_responsibilities or phase == "responsibilities":
        _render_responsibility_review(draft, project, saved)
        return

    if current_index > expected and saved and phase == "company" and not draft.get("company_name"):
        _render_experience_complete(saved, expected)
        return

    st.subheader(f"Company {min(max(current_index, 1), expected)} of {expected}")
    _render_saved_companies(saved)

    if phase == "company":
        _render_company_details_form(draft, saved)
        return

    if phase == "project":
        _render_project_details_form(draft, project)
        return


def _render_experience_complete(saved: list, expected: int) -> None:
    st.success(
        f"All {expected} compan{'y' if expected == 1 else 'ies'} captured.",
        icon=":material/done_all:",
        title="Experience complete",
    )
    _render_saved_companies(saved, editable=True)
    cols = st.container(horizontal=True, gap="small", wrap=True)
    with cols:
        if st.button("Back", icon=":material/arrow_back:", key="exp_done_back"):
            go_back()
            st.rerun()
        if st.button(
            "Add another company",
            icon=":material/add_business:",
            key="add_extra_company",
        ):
            st.session_state.expected_company_count = max(expected, len(saved)) + 1
            st.session_state.company_draft = _empty_company()
            st.session_state.project_draft = _empty_project()
            st.session_state.experience_phase = "company"
            st.rerun()
        if st.button(
            "Continue",
            icon=":material/arrow_forward:",
            type="primary",
            key="exp_done_next",
        ):
            go_next()
            st.rerun()


def _render_saved_companies(saved: list, *, editable: bool = True) -> None:
    if not saved:
        return
    st.markdown("#### Saved companies")
    for index, company in enumerate(saved):
        end = "Present" if company.get("currently_working") else company.get("end_date", "")
        with st.expander(
            f"{index + 1}. {company.get('company_name')} — {company.get('job_title')} "
            f"({company.get('start_date')} – {end})",
            expanded=False,
        ):
            st.caption(
                f"{company.get('location') or 'Location n/a'} · "
                f"{len(company.get('projects') or [])} project(s)"
            )
            for p_index, project in enumerate(company.get("projects") or []):
                st.markdown(
                    f"- **{project.get('name')}**"
                    + (f" · {project.get('domain')}" if project.get("domain") else "")
                    + (f" · {project.get('tenure')}" if project.get("tenure") else "")
                )
                if editable:
                    pcols = st.container(horizontal=True, gap="small", wrap=True)
                    with pcols:
                        if st.button(
                            "Edit project",
                            key=f"edit_proj_{index}_{p_index}",
                            icon=":material/edit:",
                        ):
                            st.session_state.editing_company_index = index
                            st.session_state.editing_project_index = p_index
                            st.session_state.company_draft = {
                                **company,
                                "projects": [
                                    p
                                    for i, p in enumerate(company.get("projects") or [])
                                    if i != p_index
                                ],
                            }
                            st.session_state.project_draft = dict(project)
                            st.session_state.experience_phase = "project"
                            st.session_state.reviewing_responsibilities = False
                            st.rerun()
                        if st.button(
                            "Delete project",
                            key=f"del_proj_{index}_{p_index}",
                            icon=":material/delete:",
                        ):
                            updated = dict(company)
                            projects = list(updated.get("projects") or [])
                            projects.pop(p_index)
                            updated["projects"] = projects
                            companies = list(saved)
                            companies[index] = updated
                            st.session_state.companies = companies
                            st.rerun()
            if editable:
                ccols = st.container(horizontal=True, gap="small", wrap=True)
                with ccols:
                    if st.button(
                        "Edit company",
                        key=f"edit_co_{index}",
                        icon=":material/edit:",
                    ):
                        companies = list(saved)
                        st.session_state.company_draft = companies.pop(index)
                        st.session_state.companies = companies
                        st.session_state.editing_company_index = None
                        st.session_state.project_draft = _empty_project()
                        st.session_state.experience_phase = "company"
                        st.session_state.reviewing_responsibilities = False
                        st.rerun()
                    if st.button(
                        "Add project",
                        key=f"add_proj_{index}",
                        icon=":material/add:",
                    ):
                        companies = list(saved)
                        st.session_state.company_draft = companies.pop(index)
                        st.session_state.companies = companies
                        st.session_state.project_draft = _empty_project()
                        st.session_state.experience_phase = "project"
                        st.rerun()
                    if st.button(
                        "Delete company",
                        key=f"del_co_{index}",
                        icon=":material/delete:",
                    ):
                        companies = list(saved)
                        companies.pop(index)
                        st.session_state.companies = companies
                        st.rerun()


def _render_company_details_form(draft: dict, saved: list) -> None:
    st.markdown("### Company / Employment Details")
    st.caption("These details stay linked to every project you add under this company.")
    with st.form(f"company_details_form_{len(saved)}", border=True, clear_on_submit=False):
        company_cols = responsive_columns(2)
        with company_cols[0]:
            company_name = st.text_input("Company name", value=draft.get("company_name", ""))
            job_title = st.text_input(
                "Job designation / job title",
                value=draft.get("job_title", ""),
            )
            location = st.text_input("Company location", value=draft.get("location", ""))
            technologies = st.text_input(
                "Technologies used at this company",
                value=", ".join(draft.get("technologies", [])),
                placeholder="Comma-separated",
            )
        company_right = company_cols[0] if len(company_cols) == 1 else company_cols[1]
        with company_right:
            start_date = st.text_input(
                "Employment start date",
                value=draft.get("start_date", ""),
                placeholder="Jul 2022",
            )
            currently = st.checkbox(
                "Currently employed here",
                value=bool(draft.get("currently_working")),
            )
            end_date = st.text_input(
                "Employment end date",
                value=draft.get("end_date", ""),
                placeholder="Dec 2024",
                disabled=currently,
            )

        submitted = st.form_submit_button(
            "Save company details & add project",
            type="primary",
            width="stretch",
            icon=":material/arrow_forward:",
        )

    if submitted:
        if not company_name.strip() or not job_title.strip() or not start_date.strip():
            st.error(
                "Company name, job designation, and start date are required.",
                icon=":material/error:",
            )
            return
        if not currently and not end_date.strip():
            st.error(
                "Provide an end date, or mark current employment.",
                icon=":material/error:",
            )
            return
        st.session_state.company_draft = {
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
        st.session_state.project_draft = _empty_project()
        st.session_state.experience_phase = "project"
        st.rerun()

    if st.button("Back", icon=":material/arrow_back:", key="exp_company_back"):
        if draft.get("projects"):
            # Preserve in-progress company with projects already captured.
            st.session_state.companies = [*saved, draft]
            st.session_state.company_draft = _empty_company()
            st.session_state.experience_phase = "company"
        go_back()
        st.rerun()


def _render_project_details_form(draft: dict, project: dict) -> None:
    end = "Present" if draft.get("currently_working") else draft.get("end_date", "")
    with st.container(border=True):
        st.markdown("### Company context")
        st.markdown(
            f"**{draft.get('job_title')}** at **{draft.get('company_name')}**  \n"
            f"{draft.get('start_date')} – {end}"
            + (f" · {draft.get('location')}" if draft.get("location") else "")
        )
        if draft.get("projects"):
            st.caption(
                f"{len(draft['projects'])} project(s) already saved under this company."
            )

    st.markdown("### Project details")
    st.caption("Add a project under the company above. You can add more projects after approval.")
    with st.form("project_details_form", border=True, clear_on_submit=False):
        project_cols = responsive_columns(2)
        with project_cols[0]:
            project_name = st.text_input("Project name", value=project.get("name", ""))
            client_name = st.text_input(
                "Client name (optional)",
                value=project.get("client_name", ""),
            )
            domain = st.text_input(
                "Project domain / industry",
                value=project.get("domain", ""),
                placeholder="Insurance, Banking, Healthcare…",
            )
            project_tenure = st.text_input(
                "Project duration",
                value=project.get("tenure", ""),
                placeholder="Jul 2022 – Present",
            )
        project_right = project_cols[0] if len(project_cols) == 1 else project_cols[1]
        with project_right:
            project_role = st.text_input(
                "Your role on the project",
                value=project.get("role", "") or draft.get("job_title", ""),
            )
            project_tech = st.text_input(
                "Technologies and tools used",
                value=project.get("technologies", ""),
                placeholder="Snowflake, DBT, Snowpipe…",
            )
            project_desc = st.text_area(
                "Project description",
                value=project.get("description", ""),
                height=110,
                help="What the project does, business context, and scope.",
            )

        st.markdown("#### Key responsibilities")
        day_to_day = st.text_area(
            "Day-to-day responsibilities (required)",
            value=project.get("responsibilities_raw", ""),
            height=110,
            placeholder=(
                "Example:\n"
                "Develop Snowflake ELT pipelines\n"
                "Build dbt models and tests\n"
                "Support production loads"
            ),
        )
        key_contributions = st.text_area(
            "Technical contributions / modules owned",
            value=project.get("key_contributions", ""),
            height=80,
        )
        challenges_solved = st.text_area(
            "Troubleshooting / production support",
            value=project.get("challenges_solved", ""),
            height=80,
        )
        impact_outcomes = st.text_area(
            "Achievements / outcomes (only if real)",
            value=project.get("impact_outcomes", "") or project.get("achievements", ""),
            height=70,
        )
        collaboration = st.text_area(
            "Collaboration (optional)",
            value=project.get("collaboration", ""),
            height=70,
        )
        add_another_project = st.checkbox(
            "After approving, add another project for this company",
            value=bool(st.session_state.add_another_project_pending),
        )
        submitted = st.form_submit_button(
            "Continue to enhance responsibilities",
            type="primary",
            width="stretch",
            icon=":material/arrow_forward:",
        )

    nav = st.container(horizontal=True, gap="small", wrap=True)
    with nav:
        if st.button(
            "Back to company details",
            icon=":material/arrow_back:",
            key="proj_back_company",
        ):
            st.session_state.experience_phase = "company"
            st.rerun()

    if not submitted:
        return

    if not project_name.strip() or not project_desc.strip():
        st.error("Project name and project description are required.", icon=":material/error:")
        return
    if not day_to_day.strip():
        st.error(
            "Please enter day-to-day responsibilities before continuing.",
            icon=":material/error:",
        )
        return

    raw_bundle = "\n".join(
        part
        for part in [
            day_to_day.strip(),
            key_contributions.strip(),
            challenges_solved.strip(),
            impact_outcomes.strip(),
            collaboration.strip(),
        ]
        if part
    )
    existing_approved = get_approved_responsibilities(
        draft.get("company_name", ""), project_name.strip()
    )
    st.session_state.project_draft = {
        "name": project_name.strip(),
        "client_name": client_name.strip(),
        "domain": domain.strip(),
        "tenure": project_tenure.strip(),
        "role": project_role.strip() or draft.get("job_title", ""),
        "description": project_desc.strip(),
        "technologies": project_tech.strip(),
        "responsibilities": existing_approved or "",
        "responsibilities_approved": bool(existing_approved),
        "responsibilities_raw": raw_bundle,
        "achievements": impact_outcomes.strip(),
        "key_contributions": key_contributions.strip(),
        "challenges_solved": challenges_solved.strip(),
        "owned_areas": "",
        "impact_outcomes": impact_outcomes.strip(),
        "collaboration": collaboration.strip(),
    }
    st.session_state.responsibility_raw_draft = raw_bundle
    st.session_state.responsibility_enhanced_draft = existing_approved or ""
    st.session_state.responsibility_phase = "approved" if existing_approved else "input"
    st.session_state.responsibility_regen_reflection = None
    st.session_state.add_another_project_pending = bool(add_another_project)
    st.session_state.experience_phase = "responsibilities"
    st.session_state.reviewing_responsibilities = True
    st.rerun()


def _render_responsibility_review(draft: dict, project: dict, saved: list) -> None:
    st.markdown("#### Key responsibilities")
    draft = draft or st.session_state.company_draft
    st.caption(
        f"{draft.get('company_name', '')} · {draft.get('job_title', '')} · "
        f"{project.get('name', 'Project')} · {project.get('role', '')}"
    )
    st.caption(
        "Approved bullets are saved under this project and company. "
        "The resume shows company details first, then each project's responsibilities."
    )

    if project.get("responsibilities_approved"):
        st.success(
            "Approved Key Responsibilities are locked and will not be changed by "
            "summary/skills regeneration.",
            icon=":material/lock:",
            title="Protected section",
        )

    with st.expander("Your original input", expanded=st.session_state.responsibility_phase == "input"):
        st.text(project.get("responsibilities_raw") or st.session_state.responsibility_raw_draft)

    phase = st.session_state.responsibility_phase
    editor_key = f"generated_responsibilities_editor_{st.session_state.responsibilities_editor_version}"

    reflection = st.session_state.get("responsibility_regen_reflection")
    if reflection:
        with st.container(border=True):
            st.markdown("##### Regeneration reflection")
            st.caption("What changed after the latest re-enhance:")
            for change in reflection.get("changes") or []:
                st.markdown(f"- {change}")
            with st.expander("Previous draft", expanded=False):
                st.text(reflection.get("before") or "(empty)")
            st.success(
                "Updated draft is loaded in the editor below.",
                icon=":material/check_circle:",
            )

    actions = st.container(horizontal=True, gap="small", wrap=True)
    with actions:
        enhance_clicked = st.button(
            "Enhance responsibilities",
            icon=":material/auto_awesome:",
            type="primary",
            key="enhance_resp_btn",
            width="stretch" if is_mobile() else "content",
        )
        edit_clicked = st.button(
            "Edit responsibilities",
            icon=":material/edit:",
            key="edit_resp_btn",
            width="stretch" if is_mobile() else "content",
        )

    if enhance_clicked:
        raw = project.get("responsibilities_raw") or st.session_state.responsibility_raw_draft
        result = enhance_responsibilities(
            raw,
            job_title=project.get("role") or draft.get("job_title", ""),
            technologies=project.get("technologies", ""),
            role_focus=st.session_state.role_focus,
        )
        if result["needs_clarification"] and not result["bullets"]:
            st.error(result["clarification_message"], icon=":material/error:")
        else:
            text = enhanced_to_text(result["bullets"])
            old_key = (
                f"generated_responsibilities_editor_{st.session_state.responsibilities_editor_version}"
            )
            if old_key in st.session_state:
                del st.session_state[old_key]
            st.session_state.responsibility_enhanced_draft = text
            st.session_state.project_draft["responsibilities"] = text
            st.session_state.responsibility_phase = "enhanced"
            st.session_state.responsibility_regen_reflection = {
                "before": "",
                "after": text,
                "changes": result.get("changes")
                or ["Created professional Key Responsibilities from your input."],
            }
            st.session_state.responsibilities_editor_version += 1
            for warning in result.get("warnings") or []:
                st.warning(warning, icon=":material/warning:")
            if result.get("clarification_message"):
                st.info(result["clarification_message"], icon=":material/info:")
            st.rerun()

    if edit_clicked:
        st.session_state.responsibility_phase = "enhanced"
        st.rerun()

    show_editor = phase in ("enhanced", "approved") or bool(
        st.session_state.responsibility_enhanced_draft or project.get("responsibilities")
    )
    edited = ""
    if show_editor:
        edited = st.text_area(
            "Professional Key Responsibilities (editable)",
            value=(
                st.session_state.responsibility_enhanced_draft
                or project.get("responsibilities", "")
            ),
            height=280 if is_mobile() else 320,
            key=editor_key,
            help="Review and refine before approving. One bullet per line.",
        )
    else:
        st.info(
            "Click **Enhance responsibilities** to convert your input into professional ATS bullets.",
            icon=":material/info:",
        )

    st.markdown("#### Regenerate responsibilities")
    st.caption(
        "Each click produces a new wording variant from your original facts. "
        "Keep regenerating until you are satisfied, then approve. "
        "Feedback guides style only — it is never added as a new bullet."
    )
    with st.form("regen_feedback_form", border=True, clear_on_submit=False):
        feedback = st.text_area(
            "What should change in the enhanced wording?",
            value=st.session_state.get("regen_feedback", ""),
            height=90,
            placeholder="Example:\nMore concise\nStronger action verbs\nKeep production support wording",
        )
        regen_submitted = st.form_submit_button(
            "Regenerate responsibilities",
            icon=":material/refresh:",
            width="stretch",
        )

    if regen_submitted:
        if project.get("responsibilities_approved") and phase == "approved":
            st.error(
                "These Key Responsibilities are approved/locked. Unlock by editing "
                "before regenerating, or keep them as-is.",
                icon=":material/lock:",
            )
        else:
            raw = project.get("responsibilities_raw") or st.session_state.responsibility_raw_draft
            current_draft = (
                (edited or "").strip()
                or st.session_state.responsibility_enhanced_draft
                or project.get("responsibilities", "")
            )
            st.session_state.responsibility_regen_count = (
                int(st.session_state.get("responsibility_regen_count") or 0) + 1
            )
            result = enhance_responsibilities(
                raw,
                job_title=project.get("role") or draft.get("job_title", ""),
                technologies=project.get("technologies", ""),
                role_focus=st.session_state.role_focus,
                feedback=feedback.strip(),
                existing_bullets=current_draft,
                variant_index=st.session_state.responsibility_regen_count,
            )
            if not result["bullets"]:
                st.error(
                    result.get("clarification_message")
                    or "Could not enhance responsibilities. Add clearer input and try again.",
                    icon=":material/error:",
                )
            else:
                text = enhanced_to_text(result["bullets"])
                # Guard: if somehow identical, force another variant pass.
                if text.strip() == current_draft.strip():
                    st.session_state.responsibility_regen_count += 1
                    result = enhance_responsibilities(
                        raw,
                        job_title=project.get("role") or draft.get("job_title", ""),
                        technologies=project.get("technologies", ""),
                        role_focus=st.session_state.role_focus,
                        feedback=feedback.strip() or "Stronger action verbs",
                        existing_bullets=current_draft,
                        variant_index=st.session_state.responsibility_regen_count,
                    )
                    text = enhanced_to_text(result["bullets"])
                old_key = (
                    f"generated_responsibilities_editor_{st.session_state.responsibilities_editor_version}"
                )
                if old_key in st.session_state:
                    del st.session_state[old_key]
                st.session_state.regen_feedback = feedback.strip()
                st.session_state.responsibility_regen_reflection = {
                    "before": current_draft,
                    "after": text,
                    "changes": result.get("changes")
                    or [
                        f"Variant {st.session_state.responsibility_regen_count}: "
                        "wording refreshed — keep regenerating until satisfied."
                    ],
                }
                st.session_state.responsibility_enhanced_draft = text
                st.session_state.project_draft["responsibilities"] = text
                st.session_state.project_draft["responsibilities_approved"] = False
                st.session_state.responsibility_phase = "enhanced"
                st.session_state.responsibilities_editor_version += 1
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
            st.session_state.experience_phase = "project"
            st.rerun()
        save_label = (
            "Approve & add another project"
            if st.session_state.add_another_project_pending
            else "Approve & save company"
        )
        if st.button(
            save_label,
            icon=":material/verified:",
            type="primary",
            key="resp_save",
            width="stretch" if is_mobile() else "content",
            disabled=not bool((edited or "").strip()),
        ):
            approved_text = edited.strip()
            store_approved_responsibilities(
                draft.get("company_name", ""),
                project.get("name", ""),
                approved_text,
            )
            project_payload = {
                **project,
                "responsibilities": approved_text,
                "responsibilities_approved": True,
                "responsibilities_raw": project.get("responsibilities_raw")
                or st.session_state.responsibility_raw_draft,
                "achievements": project.get("achievements")
                or project.get("impact_outcomes", ""),
            }
            company_payload = {
                **draft,
                "projects": [*list(draft.get("projects", [])), project_payload],
            }
            st.session_state.regen_feedback = ""
            st.session_state.responsibility_phase = "input"
            st.session_state.responsibility_enhanced_draft = ""
            st.session_state.responsibility_regen_reflection = None
            st.session_state.responsibilities_editor_version += 1
            if st.session_state.add_another_project_pending:
                st.session_state.company_draft = company_payload
                st.session_state.project_draft = _empty_project()
                st.session_state.add_another_project_pending = False
                st.session_state.reviewing_responsibilities = False
                st.session_state.experience_phase = "project"
                st.success(
                    "Project saved under this company. Add the next project below.",
                    icon=":material/task_alt:",
                )
                st.rerun()

            st.session_state.companies = [*saved, company_payload]
            st.session_state.company_draft = _empty_company()
            st.session_state.project_draft = _empty_project()
            st.session_state.reviewing_responsibilities = False
            st.session_state.add_another_project_pending = False
            st.session_state.experience_phase = "company"
            st.session_state.editing_company_index = None
            st.session_state.editing_project_index = None
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

    with st.expander("Change resume template", expanded=False):
        _render_template_gallery(location="preview")

    template_meta = TEMPLATES.get(st.session_state.get("resume_template") or "") or {}
    st.caption(
        f"Layout: **{st.session_state.get('resume_template', 'Harmonized')}** — "
        f"{template_meta.get('description') or 'Professional ATS-friendly layout.'}"
    )

    # Snapshot protected data so regeneration cannot silently alter it.
    companies_before = list(st.session_state.companies)
    approved_before = dict(st.session_state.get("approved_key_responsibilities") or {})

    resume = build_resume(resume_payload())
    st.session_state.generated_resume = resume

    approved_count = len(approved_before)
    if approved_count:
        st.caption(
            f"Protected: {approved_count} approved Key Responsibilities set(s) will not change during section regeneration."
        )

    if not st.session_state.personal.get("full_name") or not st.session_state.companies:
        st.warning(
            "Add personal details and at least one company before downloading.",
            icon=":material/warning:",
            title="Almost there",
        )

    skill_count = sum(len(v) for v in (resume.get("skills") or {}).values())

    with st.container(border=True):
        st.subheader("Regenerate one section", icon=":material/refresh:")
        st.caption(
            "Updates only the selected section. Company details and Key Responsibilities never change."
        )
        default_section = st.session_state.get("selected_regen_section") or REGENERABLE_SECTIONS[0]
        if default_section not in REGENERABLE_SECTIONS:
            default_section = REGENERABLE_SECTIONS[0]
        section = st.radio(
            "Section to regenerate",
            REGENERABLE_SECTIONS,
            index=REGENERABLE_SECTIONS.index(default_section),
            horizontal=not is_mobile(),
            key="regen_section_radio",
        )
        st.session_state.selected_regen_section = section

        if st.session_state.get("last_regen_message"):
            st.success(st.session_state.last_regen_message, icon=":material/check_circle:")

        if st.button(
            "Regenerate selected section",
            icon=":material/auto_awesome:",
            key="regen_section_btn",
            type="primary",
            width="stretch" if is_mobile() else "content",
        ):
            _regenerate_selected_section(section, companies_before, approved_before)

    # Rebuild after possible regeneration so preview matches latest section state.
    resume = build_resume(resume_payload())
    st.session_state.generated_resume = resume
    skill_count = sum(len(v) for v in (resume.get("skills") or {}).values())
    preview_html = render_preview_html(resume)
    if is_mobile():
        metrics = st.container(horizontal=True, gap="small", wrap=True)
        with metrics:
            st.metric("Companies", len(resume["experience"]))
            st.metric("Skills", skill_count)
            st.metric("Template", st.session_state.resume_template.split()[0])
        st.markdown("#### ATS checklist")
        for note in resume["ats_notes"]:
            st.markdown(f"- {note}")
        with st.container(border=True):
            st.html(preview_html)
    else:
        left, right = st.columns((2, 1), gap="large")
        with left:
            with st.container(border=True):
                st.html(preview_html)
        with right:
            st.markdown("#### ATS checklist")
            for note in resume["ats_notes"]:
                st.markdown(f"- {note}")
            st.markdown("#### Snapshot")
            st.metric("Companies", len(resume["experience"]))
            st.metric("Skills", skill_count)
            st.metric(
                "Title",
                resume["personal"].get("target_title") or "—",
            )
            st.metric("Template", st.session_state.resume_template)

    nav_buttons(next_label="Choose download format")


def _regenerate_selected_section(
    section: str,
    companies_before: list,
    approved_before: dict,
) -> None:
    """Regenerate one section only; restore protected experience data if anything drifts."""
    section = section or st.session_state.get("selected_regen_section") or REGENERABLE_SECTIONS[0]

    if section == "Professional Summary":
        st.session_state.summary_regen_count = int(st.session_state.get("summary_regen_count") or 0) + 1
        previous = (
            st.session_state.get("section_summary")
            or st.session_state.personal.get("summary")
            or ""
        )
        new_summary = regenerate_summary(
            professional_title=st.session_state.personal.get("target_title")
            or st.session_state.personal.get("professional_title")
            or "Software Engineer",
            role_focus=st.session_state.role_focus,
            priority_technologies=list(st.session_state.priority_technologies or []),
            all_technologies=list(st.session_state.all_technologies or []),
            company_count=len(st.session_state.companies or []),
            variant_index=st.session_state.summary_regen_count,
            previous_summary=previous,
            years_of_experience=st.session_state.personal.get("years_of_experience") or "",
        )
        st.session_state.section_summary = new_summary
        st.session_state.personal["summary"] = new_summary
        st.session_state.section_summary_locked = True
        st.session_state.last_regen_message = (
            f"Professional Summary updated to variant {st.session_state.summary_regen_count}. "
            "Keep regenerating until satisfied. Experience and Key Responsibilities unchanged."
        )
    elif section == "Technical Skills":
        st.session_state.skills_regen_count = int(st.session_state.get("skills_regen_count") or 0) + 1
        priority, merged, grouped = regenerate_skills_order(
            list(st.session_state.priority_technologies or []),
            list(st.session_state.all_technologies or []),
            rotate=st.session_state.skills_regen_count,
        )
        st.session_state.priority_technologies = priority
        st.session_state.all_technologies = merged
        category_names = ", ".join(grouped.keys()) or "Technical Skills"
        st.session_state.section_skills_note = (
            f"Technical skills refreshed into: {category_names}."
        )
        st.session_state.last_regen_message = (
            f"Technical Skills regenerated ({len(merged)} skills across "
            f"{len(grouped)} categories). Experience and Key Responsibilities unchanged."
        )
    else:
        st.session_state.last_regen_message = ""
        st.error("Select Professional Summary or Technical Skills to regenerate.", icon=":material/error:")
        return

    # Hard guarantee: regeneration never mutates company / approved KR state.
    st.session_state.companies = companies_before
    st.session_state.approved_key_responsibilities = approved_before
    st.rerun()


def step_download() -> None:
    render_step_banner()
    st.header("Download your resume", icon=":material/download:")
    st.caption(
        f"Template: **{st.session_state.get('resume_template', 'Modern Professional')}**. "
        "PDF and Word use the same layout as the preview."
    )
    if LOGO_IMAGE.exists():
        brand = st.container(horizontal=True, horizontal_alignment="center", wrap=True)
        with brand:
            st.image(str(LOGO_IMAGE), width=96, alt="CareerForge logo")

    resume = build_resume(resume_payload())
    st.session_state.generated_resume = resume
    preferred = "PDF (.pdf)"

    safe_name = (st.session_state.personal.get("full_name") or "resume").replace(" ", "_")
    format_choice = st.segmented_control(
        "Download format",
        ["Word (.docx)", "PDF (.pdf)", "Both"],
        default=preferred,
        key="download_format",
    )

    if format_choice in ("Word (.docx)", "Both"):
        try:
            docx_bytes = export_docx(resume)
        except Exception as exc:
            st.error(f"Could not build Word file: {exc}", icon=":material/error:")
        else:
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
        try:
            pdf_bytes = export_pdf(resume)
        except ModuleNotFoundError as exc:
            missing = str(exc).replace("No module named ", "").strip("'\"")
            st.error(
                f"PDF export needs the **{missing}** package. "
                "Install it with: `pip install reportlab` "
                "(or run the app from the project `.venv`).",
                icon=":material/error:",
            )
        except Exception as exc:
            st.error(f"Could not build PDF: {exc}", icon=":material/error:")
        else:
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


render_page_atmosphere()
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
    step_experience()
elif step == 5:
    step_education()
elif step == 6:
    step_preview()
elif step == 7:
    step_download()
else:
    st.session_state.step = 0
    st.rerun()
