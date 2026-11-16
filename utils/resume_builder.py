"""Build ATS-friendly resume content tailored to role focus."""

from __future__ import annotations

from typing import Any

from utils.resume_parser import (
    DEFAULT_LABELS,
    DEFAULT_SECTION_ORDER,
    PROFESSIONAL_SECTION_ORDER,
)
from utils.skill_categories import categorize_skills
from utils.state import ROLE_TITLE_HINTS
from utils.templates import apply_template_to_profile

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
        "Results-driven {title} with {years_text} across {tech_list}. "
        "Skilled at translating requirements into maintainable software and delivering "
        "high-impact features across {company_count} organization(s)."
    ),
    "Development + Testing": (
        "Results-driven {title} with {years_text}, specializing in building and validating software "
        "with {tech_list}. Combines strong development practice with testing discipline to ship "
        "reliable releases across {company_count} organization(s)."
    ),
    "Development + Production": (
        "Results-driven {title} with {years_text} developing and operating software with {tech_list}. "
        "Focused on production-ready delivery, reliability, and continuous improvement across "
        "{company_count} organization(s)."
    ),
    "Development + Testing + Production": (
        "Results-driven {title} with {years_text} and end-to-end ownership across development, testing, "
        "and production using {tech_list}. Delivers resilient systems and measurable outcomes across "
        "{company_count} organization(s)."
    ),
}

# Many alternate phrasings so repeated "Regenerate" keeps changing until the user is satisfied.
SUMMARY_VARIANTS: dict[str, list[str]] = {
    "Only Development": [
        SUMMARY_TEMPLATES["Only Development"],
        (
            "Accomplished {title} proficient in {tech_list}, with a track record of designing "
            "scalable features and clean, maintainable code across {company_count} organization(s)."
        ),
        (
            "Detail-oriented {title} specializing in {tech_list}. Delivers well-structured "
            "software solutions and collaborates effectively across {company_count} organization(s)."
        ),
        (
            "Passionate {title} with practical expertise in {tech_list}. Focused on building "
            "reliable features, clean architecture, and measurable delivery across {company_count} organization(s)."
        ),
        (
            "{title} with strong engineering foundations in {tech_list}. Known for converting "
            "requirements into maintainable solutions for {company_count} organization(s)."
        ),
        (
            "Software-focused {title} delivering high-quality work with {tech_list}. Emphasizes "
            "code quality, collaboration, and consistent feature delivery across {company_count} organization(s)."
        ),
        (
            "Innovative {title} experienced with {tech_list}. Builds scalable modules and "
            "improves application design across {company_count} organization(s)."
        ),
        (
            "Professional {title} skilled in {tech_list}, contributing to product development "
            "and technical excellence across {company_count} organization(s)."
        ),
    ],
    "Development + Testing": [
        SUMMARY_TEMPLATES["Development + Testing"],
        (
            "Quality-focused {title} experienced with {tech_list}. Builds features with solid "
            "test coverage and reduces defect risk across {company_count} organization(s)."
        ),
        (
            "Versatile {title} combining development and validation using {tech_list}. "
            "Partners with stakeholders to release dependable software across {company_count} organization(s)."
        ),
        (
            "{title} specializing in feature delivery and test readiness with {tech_list}. "
            "Strengthens release confidence across {company_count} organization(s)."
        ),
        (
            "Engineering {title} who pairs development with disciplined testing using {tech_list}. "
            "Supports reliable releases across {company_count} organization(s)."
        ),
        (
            "Results-oriented {title} with hands-on experience in {tech_list}. Delivers validated "
            "functionality and improves quality gates across {company_count} organization(s)."
        ),
        (
            "Diligent {title} proficient in {tech_list}, focused on building and verifying "
            "software that meets business and quality standards across {company_count} organization(s)."
        ),
        (
            "{title} with dual strengths in coding and QA practices using {tech_list}. "
            "Helps teams ship stable features across {company_count} organization(s)."
        ),
    ],
    "Development + Production": [
        SUMMARY_TEMPLATES["Development + Production"],
        (
            "Production-minded {title} skilled in {tech_list}. Builds reliable services and "
            "supports operational excellence across {company_count} organization(s)."
        ),
        (
            "Hands-on {title} delivering and operating solutions with {tech_list}. "
            "Strengthens stability, monitoring, and delivery across {company_count} organization(s)."
        ),
        (
            "{title} experienced in development and production support using {tech_list}. "
            "Focused on dependable releases and operational readiness across {company_count} organization(s)."
        ),
        (
            "Reliable {title} with expertise in {tech_list}. Combines implementation skills with "
            "production troubleshooting across {company_count} organization(s)."
        ),
        (
            "Operations-aware {title} proficient in {tech_list}. Delivers production-ready "
            "features and improves runtime stability across {company_count} organization(s)."
        ),
        (
            "{title} specializing in build-and-run delivery with {tech_list}. Supports "
            "continuous improvement and resilient systems across {company_count} organization(s)."
        ),
        (
            "Pragmatic {title} using {tech_list} to develop solutions and maintain production "
            "health across {company_count} organization(s)."
        ),
    ],
    "Development + Testing + Production": [
        SUMMARY_TEMPLATES["Development + Testing + Production"],
        (
            "Full-lifecycle {title} covering build, test, and run with {tech_list}. "
            "Owns delivery quality and production readiness across {company_count} organization(s)."
        ),
        (
            "End-to-end {title} experienced in {tech_list}. Ships validated features and "
            "supports resilient operations across {company_count} organization(s)."
        ),
        (
            "{title} with complete SDLC ownership using {tech_list}. Delivers, validates, and "
            "supports software across {company_count} organization(s)."
        ),
        (
            "Versatile {title} skilled in development, testing, and production work with {tech_list}. "
            "Drives dependable outcomes across {company_count} organization(s)."
        ),
        (
            "Cross-functional {title} proficient in {tech_list}. Combines coding, quality checks, "
            "and operational support across {company_count} organization(s)."
        ),
        (
            "{title} delivering end-to-end value with {tech_list}: implement, verify, and stabilize "
            "releases across {company_count} organization(s)."
        ),
        (
            "Adaptive {title} experienced across build-test-run cycles using {tech_list}. "
            "Supports high-quality delivery across {company_count} organization(s)."
        ),
    ],
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
    key_contributions: str = "",
    challenges_solved: str = "",
    owned_areas: str = "",
    impact_outcomes: str = "",
    collaboration: str = "",
) -> list[str]:
    """Elaborate user-provided project points into deep professional responsibility bullets."""
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

    user_point_groups = {
        "contribution": _split_lines(key_contributions),
        "challenge": _split_lines(challenges_solved),
        "ownership": _split_lines(owned_areas),
        "impact": _split_lines(impact_outcomes),
        "collaboration": _split_lines(collaboration),
    }
    has_user_points = any(user_point_groups.values())

    bullets: list[str] = [
        (
            f"Worked as {role} on {project}{tenure_note}, contributing to "
            f"{overview_short}."
        )
    ]

    if has_user_points:
        for point in user_point_groups["contribution"]:
            bullets.extend(
                _elaborate_contribution_point(
                    point, role=role, project=project, tech=tech, primary_tech=primary_tech,
                    company=company, role_focus=role_focus,
                )
            )
        for point in user_point_groups["challenge"]:
            bullets.extend(
                _elaborate_challenge_point(
                    point, role=role, project=project, tech=tech, primary_tech=primary_tech,
                    role_focus=role_focus,
                )
            )
        for point in user_point_groups["ownership"]:
            bullets.extend(
                _elaborate_ownership_point(
                    point, role=role, project=project, tech=tech, company=company,
                    role_focus=role_focus,
                )
            )
        for point in user_point_groups["impact"]:
            bullets.extend(
                _elaborate_impact_point(
                    point, role=role, project=project, tech=tech, role_focus=role_focus,
                )
            )
        for point in user_point_groups["collaboration"]:
            bullets.extend(
                _elaborate_collaboration_point(
                    point, role=role, project=project, tech=tech, role_focus=role_focus,
                )
            )
        bullets.extend(
            _role_depth_bullets(
                role_focus=role_focus,
                project=project,
                tech=tech,
                primary_tech=primary_tech,
                company=company,
            )
        )
    else:
        # Fallback when user skipped key points
        bullets.extend(
            _role_depth_bullets(
                role_focus=role_focus,
                project=project,
                tech=tech,
                primary_tech=primary_tech,
                company=company,
                full=True,
            )
        )
        if overview:
            bullets.insert(
                1,
                (
                    f"Analyzed requirements for {project} and translated them into "
                    f"implementable components covering: {_shorten(overview, 160)}."
                ),
            )

    development_extra = _role_depth_bullets(
        role_focus="Only Development",
        project=project,
        tech=tech,
        primary_tech=primary_tech,
        company=company,
        full=True,
    )
    testing_extra = _role_depth_bullets(
        role_focus="Development + Testing",
        project=project,
        tech=tech,
        primary_tech=primary_tech,
        company=company,
        full=True,
    )[2:]
    production_extra = _role_depth_bullets(
        role_focus="Development + Production",
        project=project,
        tech=tech,
        primary_tech=primary_tech,
        company=company,
        full=True,
    )[2:]
    leadership_extra = [
        (
            f"Mentored team members on {project}, clarified technical approach for "
            f"{primary_tech} deliverables, and kept implementation aligned with business goals."
        )
    ]
    metrics_extra = [
        (
            f"Tracked delivery and quality outcomes for {project}, using measurable indicators "
            f"to validate improvements across {tech} workflows."
        )
    ]

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

    unique: list[str] = []
    for bullet in bullets:
        cleaned = " ".join(bullet.split())
        if cleaned and cleaned not in unique:
            unique.append(cleaned)

    limit = 10 if "short" in feedback_lower or "concise" in feedback_lower else 16
    return unique[:limit]


def _elaborate_contribution_point(
    point: str,
    *,
    role: str,
    project: str,
    tech: str,
    primary_tech: str,
    company: str,
    role_focus: str,
) -> list[str]:
    detail = _ensure_sentence(point)
    bullets = [
        (
            f"As {role} on {project}, {_ensure_sentence(detail.lower() if detail[:1].isupper() else detail)} "
            f"using {tech}, with attention to code quality, edge cases, and maintainable design."
        ),
        (
            f"Broke down the contribution around “{_shorten(point, 90)}” into detailed implementation tasks, "
            f"validated technical approach with peers, and delivered production-ready changes for {company}."
        ),
    ]
    if "Testing" in role_focus:
        bullets.append(
            (
                f"Validated the implemented work for “{_shorten(point, 80)}” through targeted test scenarios "
                f"covering happy-path, negative, and regression cases before release."
            )
        )
    if "Production" in role_focus:
        bullets.append(
            (
                f"Prepared the “{_shorten(point, 80)}” changes for production readiness with logging, "
                f"configuration checks, and safe rollout considerations on {project}."
            )
        )
    return bullets


def _elaborate_challenge_point(
    point: str,
    *,
    role: str,
    project: str,
    tech: str,
    primary_tech: str,
    role_focus: str,
) -> list[str]:
    challenge = _shorten(point, 110)
    bullets = [
        (
            f"Diagnosed and resolved a critical challenge on {project}: {challenge}. "
            f"Identified root cause, evaluated alternatives in {primary_tech}/{tech}, and implemented a durable fix."
        ),
        (
            f"Hardened {project} against recurrence of “{_shorten(point, 80)}” by improving error handling, "
            f"validation logic, and defensive checks across dependent workflows."
        ),
    ]
    if "Testing" in role_focus:
        bullets.append(
            (
                f"Added focused verification for the “{_shorten(point, 70)}” scenario so similar defects "
                f"are caught earlier in the release cycle."
            )
        )
    if "Production" in role_focus:
        bullets.append(
            (
                f"Monitored post-fix behavior related to “{_shorten(point, 70)}” and tuned alerts/"
                f"operational checks to reduce production risk."
            )
        )
    return bullets


def _elaborate_ownership_point(
    point: str,
    *,
    role: str,
    project: str,
    tech: str,
    company: str,
    role_focus: str,
) -> list[str]:
    owned = _shorten(point, 100)
    bullets = [
        (
            f"Owned end-to-end delivery for {owned} within {project}, covering design alignment, "
            f"implementation with {tech}, peer review, and hand-off documentation."
        ),
        (
            f"Drove technical decisions for {owned} as {role}, ensuring scalability, readability, "
            f"and consistency with {company} engineering standards."
        ),
    ]
    if "Testing" in role_focus:
        bullets.append(
            (
                f"Defined acceptance criteria and verification coverage for {owned}, coordinating "
                f"with QA to keep quality gates clear and measurable."
            )
        )
    if "Production" in role_focus:
        bullets.append(
            (
                f"Supported operational readiness for {owned}, including deployment notes, "
                f"rollback considerations, and first-line production triage guidance."
            )
        )
    return bullets


def _elaborate_impact_point(
    point: str,
    *,
    role: str,
    project: str,
    tech: str,
    role_focus: str,
) -> list[str]:
    impact = _ensure_sentence(point)
    bullets = [
        (
            f"Delivered measurable impact on {project}: {impact} "
            f"This outcome was achieved through focused {tech}-based improvements and disciplined delivery."
        ),
        (
            f"Quantified and communicated the result of “{_shorten(point, 90)}” to stakeholders, "
            f"linking technical work as {role} to business/user value."
        ),
    ]
    if "Testing" in role_focus:
        bullets.append(
            (
                f"Protected the impact of “{_shorten(point, 70)}” with regression coverage so quality "
                f"gains remained stable across subsequent releases."
            )
        )
    if "Production" in role_focus:
        bullets.append(
            (
                f"Sustained the impact of “{_shorten(point, 70)}” in production through monitoring, "
                f"fast feedback loops, and continuous operational improvements."
            )
        )
    return bullets


def _elaborate_collaboration_point(
    point: str,
    *,
    role: str,
    project: str,
    tech: str,
    role_focus: str,
) -> list[str]:
    collab = _shorten(point, 110)
    return [
        (
            f"Collaborated across teams on {project} around {collab}, aligning requirements, "
            f"technical constraints, and delivery timelines as {role}."
        ),
        (
            f"Facilitated clear communication on {collab} by translating {tech} implementation details "
            f"into actionable updates for product, QA, and engineering partners."
        ),
    ]


def _role_depth_bullets(
    *,
    role_focus: str,
    project: str,
    tech: str,
    primary_tech: str,
    company: str,
    full: bool = False,
) -> list[str]:
    development = [
        (
            f"Designed and developed application modules using {tech}, ensuring readability, "
            f"reusability, and alignment with {company} coding standards."
        ),
        (
            f"Implemented end-to-end feature flows for {project}, covering service interactions, "
            f"data validation, error handling, and backward-compatible changes."
        ),
        (
            f"Optimized {primary_tech} logic and data access patterns in {project} to improve "
            f"response time, reliability, and overall user experience."
        ),
    ]
    testing = [
        (
            f"Created unit, integration, and regression coverage for {project} changes, validating "
            f"happy-path and negative scenarios before each release candidate."
        ),
        (
            f"Designed and executed requirement-mapped test cases, logged defects with reproducible "
            f"steps, and verified fixes through structured re-test cycles."
        ),
        (
            f"Automated repetitive validation for {tech} workflows to shorten feedback loops and "
            f"reduce manual testing effort on {project}."
        ),
    ]
    production = [
        (
            f"Prepared {project} releases for production with logging, health checks, configuration "
            f"management, and rollback-friendly deployment steps."
        ),
        (
            f"Monitored {project} in live environments, triaged incidents, and applied hotfixes or "
            f"configuration changes to restore service quickly."
        ),
        (
            f"Improved operational readiness with runbooks, alert tuning, and post-incident reviews "
            f"that reduced repeat production issues."
        ),
    ]

    if role_focus == "Only Development":
        return development if full else development[:2]
    if role_focus == "Development + Testing":
        return (development[:2] + testing) if full else (development[:1] + testing[:2])
    if role_focus == "Development + Production":
        return (development[:2] + production) if full else (development[:1] + production[:2])
    return (
        (development[:2] + testing[:2] + production[:2])
        if full
        else (development[:1] + testing[:1] + production[:1])
    )


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
    personal = dict(data.get("personal", {}))
    role_focus = data.get("role_focus", "Only Development")
    priority_techs = _normalize_list(data.get("priority_technologies", []))
    all_techs = _normalize_list(data.get("all_technologies", []))
    companies = data.get("companies", [])
    education = data.get("education", [])
    approved_map = data.get("approved_key_responsibilities") or {}

    target_title = (
        personal.get("target_title")
        or personal.get("professional_title")
        or ROLE_TITLE_HINTS.get(role_focus, "Software Professional")
    )
    personal["target_title"] = target_title
    tech_for_summary = priority_techs or all_techs
    tech_list = ", ".join(tech_for_summary[:6]) if tech_for_summary else "modern software stacks"

    # Independent summary section state takes precedence when set.
    summary = (data.get("section_summary") or personal.get("summary") or "").strip()
    if not summary:
        summary = SUMMARY_TEMPLATES[role_focus].format(
            title=target_title,
            tech_list=tech_list,
            company_count=max(len(companies), 1),
            years_text=years_experience_text(personal.get("years_of_experience")),
        )

    experience_sections = []
    for company in companies:
        projects = company.get("projects") or []
        # Company-level bullets only when explicitly provided — project KR live under projects.
        bullets = _split_lines(company.get("responsibilities", ""))
        company_techs = _normalize_list(company.get("technologies", []))
        project_payloads = []
        for project in projects:
            project_name = project.get("name", "Project")
            approved_key = (
                f"{(company.get('company_name') or '').strip().lower()}"
                f"::{(project_name or '').strip().lower()}"
            )
            # Approved Key Responsibilities are never overwritten by generation.
            if project.get("responsibilities_approved") or approved_map.get(approved_key):
                locked = approved_map.get(approved_key) or project.get("responsibilities", "")
                project_for_bullets = {
                    **project,
                    "responsibilities": locked,
                    "responsibilities_approved": True,
                }
            else:
                project_for_bullets = project
            project_bullets = _project_bullets(
                project_for_bullets, role_focus, priority_techs
            )
            for tech in _normalize_list(project.get("technologies", [])):
                if tech not in company_techs:
                    company_techs.append(tech)
            project_payloads.append(
                {
                    "name": project_name,
                    "client_name": project.get("client_name", ""),
                    "domain": project.get("domain", ""),
                    "tenure": project.get("tenure", ""),
                    "role": project.get("role", ""),
                    "description": project.get("description", ""),
                    "technologies": project.get("technologies", ""),
                    "achievements": _split_lines(project.get("achievements", "")),
                    "responsibilities_approved": bool(
                        project.get("responsibilities_approved")
                        or approved_map.get(approved_key)
                    ),
                    "bullets": project_bullets,
                }
            )
        experience_sections.append(
            {
                "company_name": company.get("company_name", ""),
                "job_title": company.get("job_title") or target_title,
                "location": company.get("location", ""),
                "date_range": _date_range(company),
                "technologies": company_techs,
                "projects": project_payloads,
                "bullets": bullets,
            }
        )

    ordered_techs = priority_techs + [
        tech for tech in all_techs if tech not in set(priority_techs)
    ]
    skills = categorize_skills(ordered_techs)

    template_name = data.get("resume_template") or "Modern Professional"
    use_reference = bool(data.get("use_reference_format"))
    format_profile = apply_template_to_profile(
        template_name,
        base_profile=data.get("format_profile") if use_reference else None,
        use_reference_labels=use_reference,
    )

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
        "resume_template": template_name,
        "format_profile": format_profile,
        "ats_notes": _ats_notes(role_focus, priority_techs, format_profile),
    }


def years_experience_text(years_value: Any) -> str:
    """Human-readable experience phrase for professional summaries."""
    raw = str(years_value or "").strip()
    if not raw:
        return "hands-on professional experience"
    try:
        years = float(raw.replace("+", "").strip())
    except ValueError:
        if "year" in raw.lower():
            return f"{raw} of professional experience" if "of" not in raw.lower() else raw
        return f"{raw}+ years of experience"
    if years <= 0:
        return "hands-on professional experience"
    years_label = str(int(years)) if years == int(years) else str(years).rstrip("0").rstrip(".")
    unit = "year" if years == 1 else "years"
    return f"{years_label}+ {unit} of experience"


def regenerate_summary(
    *,
    professional_title: str,
    role_focus: str,
    priority_technologies: list[str],
    all_technologies: list[str],
    company_count: int,
    variant_index: int = 0,
    previous_summary: str = "",
    years_of_experience: str | int | float = "",
) -> str:
    """Regenerate only the Professional Summary; keep changing until wording differs."""
    tech_for_summary = list(priority_technologies or []) or list(all_technologies or [])
    variants = SUMMARY_VARIANTS.get(role_focus) or SUMMARY_VARIANTS["Only Development"]
    previous = " ".join((previous_summary or "").split()).strip().lower()
    title = professional_title or "Software Professional"
    count = max(company_count, 1)
    years_text = years_experience_text(years_of_experience)

    # Try several variants so regenerate never feels stuck on the same sentence.
    for offset in range(max(len(variants) * 2, 8)):
        index = (int(variant_index) + offset) % len(variants)
        rotated = _rotate_list(tech_for_summary, index)
        tech_list = _format_tech_list(rotated, style=index % 3)
        candidate = variants[index].format(
            title=title,
            tech_list=tech_list,
            company_count=count,
            years_text=years_text,
        ).strip()
        if " ".join(candidate.split()).lower() != previous:
            return candidate
    # Fallback: force a visible change by adjusting tech emphasis.
    rotated = _rotate_list(tech_for_summary, int(variant_index) + 1)
    return variants[int(variant_index) % len(variants)].format(
        title=title,
        tech_list=_format_tech_list(rotated, style=(int(variant_index) + 1) % 3),
        company_count=count,
        years_text=years_text,
    ).strip()


def _rotate_list(values: list[str], shift: int) -> list[str]:
    if not values:
        return []
    amount = int(shift) % len(values)
    return values[amount:] + values[:amount]


def _format_tech_list(techs: list[str], *, style: int = 0) -> str:
    if not techs:
        return "modern software stacks"
    top = techs[:6]
    if style % 3 == 1 and len(top) >= 3:
        return f"{', '.join(top[:3])} (including {', '.join(top[3:6])})" if len(top) > 3 else ", ".join(top)
    if style % 3 == 2 and len(top) >= 2:
        return f"{top[0]} and {', '.join(top[1:])}"
    return ", ".join(top)


def regenerate_skills_order(
    priority_technologies: list[str],
    all_technologies: list[str],
    *,
    rotate: int = 0,
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """
    Refresh Technical Skills ordering/categories only.
    Never mutates experience, companies, or Key Responsibilities.
    """
    priority = [t for t in (priority_technologies or []) if t]
    others = [t for t in (all_technologies or []) if t and t not in set(priority)]
    # Rotate non-priority techs so regeneration is visibly different.
    if others and rotate:
        shift = int(rotate) % len(others)
        others = others[shift:] + others[:shift]
    merged = priority + [t for t in others if t not in set(priority)]
    return priority, merged, categorize_skills(merged)


def render_preview_markdown(resume: dict[str, Any]) -> str:
    """Markdown preview kept for lightweight checks; HTML preview is preferred in UI."""
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
                    if job.get("technologies") and not include_projects:
                        lines.append(f"**Technologies:** {', '.join(job['technologies'])}")
                    for bullet in job.get("bullets") or []:
                        lines.append(f"- {bullet}")
                    if include_projects:
                        for project in job.get("projects") or []:
                            lines.extend(_preview_project_lines(project))
                    lines.append("")
        elif section_key == "projects":
            if include_projects or not profile.get("show_standalone_projects"):
                continue
            projects = [
                project
                for job in resume.get("experience", [])
                for project in job.get("projects", [])
            ]
            if projects:
                lines.append(f"## {label}")
                for project in projects:
                    lines.extend(_preview_project_lines(project))
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


def _preview_project_lines(project: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    tenure = f" ({project['tenure']})" if project.get("tenure") else ""
    lines.append(f"#### {project.get('name', 'Project')}{tenure}")
    meta_bits = [
        part
        for part in [
            f"Client: {project['client_name']}" if project.get("client_name") else "",
            f"Domain: {project['domain']}" if project.get("domain") else "",
            f"Role: {project['role']}" if project.get("role") else "",
        ]
        if part
    ]
    if meta_bits:
        lines.append(" · ".join(meta_bits))
    if project.get("description"):
        lines.append(project["description"])
    if project.get("technologies"):
        tech = project["technologies"]
        if isinstance(tech, list):
            tech = ", ".join(tech)
        lines.append(f"**Technologies:** {tech}")
    for bullet in project.get("bullets") or []:
        lines.append(f"- {bullet}")
    achievements = project.get("achievements") or []
    if isinstance(achievements, str):
        achievements = _split_lines(achievements)
    for item in achievements:
        lines.append(f"- {item}")
    return lines


def render_preview_html(resume: dict[str, Any]) -> str:
    """HTML preview using the template's distinct structural layout."""
    from utils.layout_renderers import render_layout_html

    return render_layout_html(resume)


def _project_bullets(
    project: dict[str, Any], role_focus: str, priority_techs: list[str]
) -> list[str]:
    bullets = _split_lines(project.get("responsibilities", ""))
    bullets.extend(_split_lines(project.get("achievements", "")))
    if bullets:
        return bullets[:10]

    # Never invent bullets when the user already approved Key Responsibilities.
    if project.get("responsibilities_approved"):
        return []

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
