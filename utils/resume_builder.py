"""Build ATS-friendly resume content tailored to role focus."""

from __future__ import annotations

from typing import Any

from utils.resume_parser import DEFAULT_LABELS, DEFAULT_SECTION_ORDER
from utils.state import ROLE_TITLE_HINTS

ROLE_BULLET_LENSES = {
    "Only Development": [
        "Designed and implemented {focus} features for {project}, improving delivery quality and maintainability.",
        "Built scalable modules using {tech} and collaborated with stakeholders to ship production-ready functionality.",
        "Refactored critical components in {project} to reduce complexity and accelerate feature delivery.",
    ],
    "Development + Testing": [
        "Developed and validated {focus} capabilities for {project}, pairing feature work with thorough test coverage.",
        "Created automated test scenarios around {tech} workflows to catch regressions before release.",
        "Partnered with QA to harden {project}, reducing defect leakage and improving release confidence.",
    ],
    "Development + Production": [
        "Delivered {focus} services for {project} and supported production readiness, monitoring, and incident response.",
        "Implemented deployment-friendly {tech} components with logging, health checks, and operational runbooks.",
        "Optimized {project} for reliability and performance in production environments.",
    ],
    "Development + Testing + Production": [
        "Owned end-to-end delivery for {project}: development, validation, and production support using {tech}.",
        "Built, tested, and released {focus} features with measurable quality and operational guardrails.",
        "Improved release cadence for {project} by combining automation, code quality, and production observability.",
    ],
}

SUMMARY_TEMPLATES = {
    "Only Development": (
        "{name} is a {title} with hands-on experience across {tech_list}. "
        "Skilled at translating requirements into clean, maintainable software and delivering "
        "high-impact features across {company_count} organization(s)."
    ),
    "Development + Testing": (
        "{name} is a {title} specializing in building and validating software with {tech_list}. "
        "Combines strong development practice with testing discipline to ship reliable releases "
        "across {company_count} organization(s)."
    ),
    "Development + Production": (
        "{name} is a {title} experienced in developing and operating software with {tech_list}. "
        "Focused on production-ready delivery, reliability, and continuous improvement across "
        "{company_count} organization(s)."
    ),
    "Development + Testing + Production": (
        "{name} is a {title} with end-to-end ownership across development, testing, and production "
        "using {tech_list}. Delivers resilient systems and measurable outcomes across "
        "{company_count} organization(s)."
    ),
}


def generate_project_responsibilities(
    *,
    role_focus: str,
    project_name: str,
    project_role: str = "",
    project_overview: str = "",
    technologies: str = "",
    tenure: str = "",
    company_name: str = "",
    job_title: str = "",
    priority_technologies: list[str] | None = None,
    change_requests: str = "",
) -> list[str]:
    """Create elaborate, editable responsibility bullets from role + project overview."""
    project = (project_name or "the project").strip()
    role = (project_role or job_title or "team member").strip()
    overview = (project_overview or "").strip()
    overview_short = _shorten(overview, 140) if overview else (
        f"delivery of {project} with a focus on quality and maintainable design"
    )
    tech_list = _normalize_list(technologies) or _normalize_list(priority_technologies or [])
    tech = ", ".join(tech_list[:5]) if tech_list else "the project technology stack"
    primary_tech = tech_list[0] if tech_list else "core application components"
    company = (company_name or "the organization").strip()
    tenure_note = f" during a {tenure.strip()} engagement" if tenure.strip() else ""
    feedback = (change_requests or "").strip()
    feedback_lower = feedback.lower()

    shared = [
        (
            f"Worked as {role} on {project}{tenure_note}, contributing to "
            f"{overview_short}."
        ),
        (
            f"Translated business and functional requirements for {project} into detailed "
            f"technical tasks, implementation plans, and clear acceptance criteria."
        ),
        (
            f"Designed and developed application modules using {tech}, ensuring readability, "
            f"reusability, and alignment with {company} coding standards."
        ),
        (
            f"Built and enhanced {primary_tech}-based features for {project}, integrating "
            f"with dependent services and handling edge cases in real business workflows."
        ),
        (
            f"Collaborated with product owners, designers, and peer engineers to refine "
            f"scope for {project} and deliver incremental value across sprint cycles."
        ),
        (
            f"Performed code reviews, resolved defects, and refactored critical paths in "
            f"{project} to improve maintainability and reduce future change cost."
        ),
        (
            f"Documented technical design decisions, API contracts, and hand-off notes so "
            f"new team members could ramp up quickly on {project}."
        ),
    ]

    development_extra = [
        (
            f"Implemented end-to-end feature flows for {project}, covering UI/service "
            f"interactions, data validation, error handling, and backward-compatible changes."
        ),
        (
            f"Optimized application logic and data access patterns in {project} to improve "
            f"response time, reliability, and overall user experience."
        ),
        (
            f"Owned technical spikes and proof-of-concepts when introducing new {primary_tech} "
            f"capabilities, then productionized the approved approach for {project}."
        ),
    ]

    testing_extra = [
        (
            f"Created unit, integration, and regression test coverage for {project} changes, "
            f"validating happy-path and negative scenarios before each release candidate."
        ),
        (
            f"Designed and executed test cases mapped to {project} requirements, logged "
            f"defects with reproducible steps, and verified fixes through re-test cycles."
        ),
        (
            f"Automated repetitive validation for {tech} workflows to shorten feedback loops "
            f"and reduce manual testing effort on {project}."
        ),
        (
            f"Partnered with QA stakeholders to strengthen quality gates for {project}, "
            f"improving release confidence and lowering production defect leakage."
        ),
    ]

    production_extra = [
        (
            f"Prepared {project} releases for production by adding logging, health checks, "
            f"configuration management, and rollback-friendly deployment steps."
        ),
        (
            f"Monitored {project} in live environments, triaged incidents, and applied "
            f"hotfixes or configuration changes to restore service quickly."
        ),
        (
            f"Improved operational readiness of {project} with runbooks, alert tuning, and "
            f"post-incident reviews that reduced repeat production issues."
        ),
        (
            f"Supported CI/CD and environment promotion for {project}, coordinating "
            f"deployments across lower and production landscapes with {tech}."
        ),
    ]

    leadership_extra = [
        (
            f"Mentored junior engineers on {project}, unblocked delivery risks, and helped "
            f"the team align on technical approach for {_shorten(overview_short, 80)}."
        ),
        (
            f"Led design discussions and stakeholder demos for {project}, translating complex "
            f"{primary_tech} decisions into clear business outcomes."
        ),
    ]

    metrics_extra = [
        (
            f"Improved key delivery metrics for {project} by tightening release readiness, "
            f"reducing rework, and tracking outcomes against agreed success criteria."
        ),
        (
            f"Drove measurable quality gains on {project} through targeted fixes, stronger "
            f"validation, and continuous feedback from users and stakeholders."
        ),
    ]

    # Lead with overview + role-specific work so focus bullets are never truncated away.
    bullets: list[str] = [shared[0]]
    if overview:
        bullets.append(
            (
                f"Analyzed the project overview for {project} and broke the solution into "
                f"implementable components covering: {_shorten(overview, 160)}."
            )
        )

    if role_focus == "Only Development":
        bullets.extend(development_extra)
        bullets.extend(shared[1:])
    elif role_focus == "Development + Testing":
        bullets.extend(development_extra[:2])
        bullets.extend(testing_extra)
        bullets.extend(shared[1:])
    elif role_focus == "Development + Production":
        bullets.extend(development_extra[:2])
        bullets.extend(production_extra)
        bullets.extend(shared[1:])
    else:
        bullets.extend(development_extra[:2])
        bullets.extend(testing_extra[:2])
        bullets.extend(production_extra[:2])
        bullets.extend(shared[1:])

    if feedback:
        bullets = _apply_change_requests(
            bullets,
            feedback=feedback,
            feedback_lower=feedback_lower,
            project=project,
            role=role,
            tech=tech,
            primary_tech=primary_tech,
            development_extra=development_extra,
            testing_extra=testing_extra,
            production_extra=production_extra,
            leadership_extra=leadership_extra,
            metrics_extra=metrics_extra,
        )

    # Keep unique, elaborate set for user editing
    unique: list[str] = []
    for bullet in bullets:
        cleaned = " ".join(bullet.split())
        if cleaned and cleaned not in unique:
            unique.append(cleaned)

    limit = 10 if "short" in feedback_lower or "concise" in feedback_lower else 14
    return unique[:limit]


def _apply_change_requests(
    bullets: list[str],
    *,
    feedback: str,
    feedback_lower: str,
    project: str,
    role: str,
    tech: str,
    primary_tech: str,
    development_extra: list[str],
    testing_extra: list[str],
    production_extra: list[str],
    leadership_extra: list[str],
    metrics_extra: list[str],
) -> list[str]:
    """Rebuild bullets so regeneration clearly reflects the user's requested changes."""
    updated = list(bullets)
    requested_lines = _split_lines(feedback)

    # Explicit requested additions first so the user sees their changes immediately.
    custom_bullets: list[str] = []
    for line in requested_lines:
        lower = line.lower()
        if lower.startswith(("add ", "include ", "mention ", "emphasize ", "focus on ")):
            detail = line.split(" ", 1)[1].strip(" .")
            custom_bullets.append(
                f"As {role} on {project}, {_ensure_sentence(detail)} using {tech}."
            )
        elif lower.startswith(("remove ", "drop ", "delete ", "less ")):
            continue
        elif len(line.split()) >= 4 and not any(
            token in lower
            for token in ("make it", "more ", "less ", "shorter", "concise", "rewrite")
        ):
            custom_bullets.append(
                f"Delivered {_ensure_sentence(line)} within {project}, applying {primary_tech} "
                f"and related {tech} capabilities."
            )

    if any(token in feedback_lower for token in ("test", "qa", "quality", "selenium", "automation")):
        updated = testing_extra + updated
    if any(token in feedback_lower for token in ("production", "devops", "deploy", "monitor", "support")):
        updated = production_extra + updated
    if any(token in feedback_lower for token in ("develop", "coding", "feature", "backend", "frontend", "api")):
        updated = development_extra + updated
    if any(token in feedback_lower for token in ("lead", "mentor", "ownership", "senior", "architect")):
        updated = leadership_extra + updated
    if any(token in feedback_lower for token in ("metric", "impact", "quantif", "kpi", "result", "achievement")):
        updated = metrics_extra + updated

    drop_tokens: list[str] = []
    if any(token in feedback_lower for token in ("remove collab", "less collab", "no collab", "drop collab")):
        drop_tokens.extend(["collaborated", "partnered", "stakeholders"])
    if any(token in feedback_lower for token in ("remove document", "less document", "no document")):
        drop_tokens.extend(["documented", "hand-off", "runbooks"])
    if drop_tokens:
        updated = [
            bullet
            for bullet in updated
            if not any(token in bullet.lower() for token in drop_tokens)
        ]

    if any(token in feedback_lower for token in ("short", "concise", "brief", "less verbose")):
        updated = [_shorten(bullet, 150) for bullet in updated]

    if any(token in feedback_lower for token in ("more technical", "technical depth", "deeper technical")):
        updated.insert(
            0,
            (
                f"Deepened the technical design of {project} by refining {primary_tech} "
                f"architecture choices, data contracts, and integration patterns across {tech}."
            ),
        )

    updated.insert(
        0,
        (
            f"Regenerated responsibilities for {project} to reflect requested changes: "
            f"{_shorten(feedback, 160)}."
        ),
    )
    return custom_bullets + updated


def _ensure_sentence(text: str) -> str:
    cleaned = " ".join((text or "").split()).strip(" .")
    if not cleaned:
        return "additional project outcomes"
    if cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def responsibilities_to_text(bullets: list[str]) -> str:
    return "\n".join(f"• {bullet}" for bullet in bullets)


def build_resume(data: dict[str, Any]) -> dict[str, Any]:
    personal = data.get("personal", {})
    role_focus = data.get("role_focus", "Only Development")
    priority_techs = _normalize_list(data.get("priority_technologies", []))
    all_techs = _normalize_list(data.get("all_technologies", []))
    companies = data.get("companies", [])
    education = data.get("education", [])

    target_title = personal.get("target_title") or ROLE_TITLE_HINTS.get(
        role_focus, "Software Professional"
    )
    tech_for_summary = priority_techs or all_techs
    tech_list = ", ".join(tech_for_summary[:6]) if tech_for_summary else "modern software stacks"

    summary = (personal.get("summary") or "").strip()
    if not summary:
        summary = SUMMARY_TEMPLATES[role_focus].format(
            name=personal.get("full_name") or "Candidate",
            title=target_title,
            tech_list=tech_list,
            company_count=max(len(companies), 1),
        )

    experience_sections = []
    for company in companies:
        projects = company.get("projects") or []
        bullets = _company_bullets(company, role_focus, priority_techs)
        experience_sections.append(
            {
                "company_name": company.get("company_name", ""),
                "job_title": company.get("job_title") or target_title,
                "location": company.get("location", ""),
                "date_range": _date_range(company),
                "technologies": _normalize_list(company.get("technologies", [])),
                "projects": [
                    {
                        "name": project.get("name", "Project"),
                        "tenure": project.get("tenure", ""),
                        "role": project.get("role", ""),
                        "description": project.get("description", ""),
                        "technologies": project.get("technologies", ""),
                        "bullets": _project_bullets(project, role_focus, priority_techs),
                    }
                    for project in projects
                ],
                "bullets": bullets,
            }
        )

    skills = {
        "Priority technologies": priority_techs,
        "Additional technologies": [
            tech for tech in all_techs if tech not in set(priority_techs)
        ],
    }

    use_reference = bool(data.get("use_reference_format"))
    format_profile = data.get("format_profile") if use_reference else None

    return {
        "personal": {
            **personal,
            "target_title": target_title,
            "summary": summary,
        },
        "role_focus": role_focus,
        "skills": skills,
        "experience": experience_sections,
        "education": education,
        "certifications": _split_lines(data.get("certifications", "")),
        "achievements": _split_lines(data.get("achievements", "")),
        "use_reference_format": use_reference,
        "reference_file_type": data.get("reference_file_type"),
        "format_profile": format_profile,
        "ats_notes": _ats_notes(role_focus, priority_techs, format_profile),
    }


def render_preview_markdown(resume: dict[str, Any]) -> str:
    from utils.exporters import _contact_line, _job_heading, _section_label

    personal = resume["personal"]
    profile = resume.get("format_profile") or {
        "section_order": list(DEFAULT_SECTION_ORDER),
        "section_labels": dict(DEFAULT_LABELS),
        "contact_separator": " | ",
        "job_line_style": "title_emdash_company",
        "include_projects_under_experience": True,
        "heading_all_caps": True,
    }
    lines = [
        f"# {personal.get('full_name') or 'Your Name'}",
        f"**{personal.get('target_title', '')}**",
        "",
        _contact_line(personal, profile),
        "",
    ]

    include_projects = profile.get("include_projects_under_experience", True)
    for section_key in profile.get("section_order") or DEFAULT_SECTION_ORDER:
        label = _section_label(profile, section_key)
        if section_key == "summary":
            lines.extend([f"## {label}", personal.get("summary", ""), ""])
        elif section_key == "skills":
            if any((resume.get("skills") or {}).values()):
                lines.append(f"## {label}")
                for skill_label, values in resume["skills"].items():
                    if values:
                        lines.append(f"**{skill_label}:** {', '.join(values)}")
                lines.append("")
        elif section_key == "experience":
            if resume.get("experience"):
                lines.append(f"## {label}")
                for job in resume["experience"]:
                    lines.append(f"### {_job_heading(job, profile)}")
                    meta = " | ".join(
                        part for part in [job["date_range"], job["location"]] if part
                    )
                    if meta:
                        lines.append(f"*{meta}*")
                    if job["technologies"]:
                        lines.append(f"**Technologies:** {', '.join(job['technologies'])}")
                    for bullet in job["bullets"]:
                        lines.append(f"- {bullet}")
                    if include_projects:
                        for project in job["projects"]:
                            tenure = f" ({project['tenure']})" if project.get("tenure") else ""
                            lines.append(f"#### {project['name']}{tenure}")
                            if project.get("description"):
                                lines.append(project["description"])
                            for bullet in project["bullets"]:
                                lines.append(f"- {bullet}")
                    lines.append("")
        elif section_key == "projects":
            projects = [
                project
                for job in resume.get("experience", [])
                for project in job.get("projects", [])
            ]
            if projects and not include_projects:
                lines.append(f"## {label}")
                for project in projects:
                    tenure = f" ({project['tenure']})" if project.get("tenure") else ""
                    lines.append(f"### {project['name']}{tenure}")
                    if project.get("description"):
                        lines.append(project["description"])
                    for bullet in project["bullets"]:
                        lines.append(f"- {bullet}")
                lines.append("")
        elif section_key == "education" and resume.get("education"):
            lines.append(f"## {label}")
            for edu in resume["education"]:
                years = " – ".join(
                    part for part in [edu.get("start_year"), edu.get("end_year")] if part
                )
                headline = f"**{edu.get('degree', '')}** — {edu.get('institution', '')}"
                if years:
                    headline += f" ({years})"
                lines.append(headline)
                if edu.get("details"):
                    lines.append(edu["details"])
            lines.append("")
        elif section_key == "certifications" and resume.get("certifications"):
            lines.append(f"## {label}")
            lines.extend(f"- {item}" for item in resume["certifications"])
            lines.append("")
        elif section_key == "achievements" and resume.get("achievements"):
            lines.append(f"## {label}")
            lines.extend(f"- {item}" for item in resume["achievements"])
            lines.append("")

    return "\n".join(lines).strip()


def _company_bullets(
    company: dict[str, Any], role_focus: str, priority_techs: list[str]
) -> list[str]:
    bullets: list[str] = []
    responsibilities = _split_lines(company.get("responsibilities", ""))
    bullets.extend(responsibilities)

    if not bullets and company.get("projects"):
        first = company["projects"][0]
        bullets.extend(_project_bullets(first, role_focus, priority_techs)[:2])

    if not bullets:
        focus = priority_techs[0] if priority_techs else "core"
        tech = ", ".join(priority_techs[:3]) if priority_techs else "relevant technologies"
        templates = ROLE_BULLET_LENSES[role_focus]
        bullets.append(
            templates[0].format(
                focus=focus,
                project=company.get("company_name") or "key initiatives",
                tech=tech,
            )
        )
    return bullets[:6]


def _project_bullets(
    project: dict[str, Any], role_focus: str, priority_techs: list[str]
) -> list[str]:
    bullets = _split_lines(project.get("responsibilities", ""))
    bullets.extend(_split_lines(project.get("achievements", "")))
    if bullets:
        return bullets[:10]

    return generate_project_responsibilities(
        role_focus=role_focus,
        project_name=project.get("name", "Project"),
        project_role=project.get("role", ""),
        project_overview=project.get("description", ""),
        technologies=project.get("technologies", ""),
        tenure=project.get("tenure", ""),
        priority_technologies=priority_techs,
    )[:8]


def _shorten(text: str, limit: int) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    trimmed = compact[: limit - 1].rsplit(" ", 1)[0]
    return f"{trimmed}…"


def _date_range(company: dict[str, Any]) -> str:
    start = company.get("start_date") or ""
    end = "Present" if company.get("currently_working") else (company.get("end_date") or "")
    if start and end:
        return f"{start} – {end}"
    return start or end


def _normalize_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        parts = re_split(values)
        return parts
    result = []
    for value in values:
        text = str(value).strip()
        if text and text not in result:
            result.append(text)
    return result


def re_split(value: str) -> list[str]:
    parts = []
    for chunk in value.replace(";", ",").split(","):
        item = chunk.strip()
        if item and item not in parts:
            parts.append(item)
    return parts


def _split_lines(value: str) -> list[str]:
    if not value:
        return []
    lines = []
    for raw in value.replace("\r", "").split("\n"):
        line = raw.strip(" •-\t")
        if line:
            lines.append(line)
    return lines


def _ats_notes(
    role_focus: str,
    priority_techs: list[str],
    format_profile: dict[str, Any] | None = None,
) -> list[str]:
    notes = [
        "Single-column layout with standard section headings for ATS parsers.",
        "Keywords placed in summary, skills, and experience bullets.",
        f"Content emphasis tuned for: {role_focus}.",
    ]
    if format_profile:
        order = format_profile.get("section_order") or []
        labels = format_profile.get("section_labels") or {}
        shown = [labels.get(key, key) for key in order[:6]]
        notes.append(
            "Matched reference section order/labels: " + " → ".join(shown)
        )
        notes.append(
            f"Matched reference alignment ({format_profile.get('name_alignment', 'center')}) "
            f"and contact separator style."
        )
    if priority_techs:
        notes.append(
            "Priority technologies highlighted first: " + ", ".join(priority_techs[:8])
        )
    return notes
