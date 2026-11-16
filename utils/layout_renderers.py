"""Distinct HTML layout renderers for each resume template style."""

from __future__ import annotations

import re
from html import escape
from typing import Any, Callable

from utils.resume_parser import DEFAULT_SECTION_ORDER


def render_layout_html(resume: dict[str, Any]) -> str:
    profile = resume.get("format_profile") or {}
    layout_id = str(profile.get("layout_id") or profile.get("template_id") or "classic")
    renderer = LAYOUT_RENDERERS.get(layout_id) or _render_classic
    return renderer(resume, profile)


def _scope(profile: dict[str, Any]) -> str:
    raw = str(profile.get("template_id") or profile.get("template_name") or "resume")
    return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-") or "resume"


def _colors(profile: dict[str, Any]) -> dict[str, str]:
    accent = profile.get("accent_color") or "#0E7C86"
    return {
        "accent": accent,
        "name": profile.get("name_color") or "#0A2F45",
        "title": profile.get("title_color") or accent,
        "text": profile.get("text_color") or "#102A3A",
        "muted": profile.get("muted_color") or "#5A7585",
        "heading": profile.get("heading_color") or profile.get("name_color") or "#0A2F45",
        "rule": profile.get("rule_color") or accent,
    }


def _label(profile: dict[str, Any], key: str) -> str:
    from utils.exporters import _section_label

    return _section_label(profile, key)


def _contact(personal: dict[str, Any], profile: dict[str, Any]) -> str:
    from utils.exporters import _contact_line

    return _contact_line(personal, profile)


def _job_heading(job: dict[str, Any], profile: dict[str, Any]) -> str:
    from utils.exporters import _job_heading as heading

    return heading(job, profile)


def _badge(profile: dict[str, Any], root: str) -> str:
    label = escape(str(profile.get("template_name") or profile.get("label") or "Template"))
    structure = escape(str(profile.get("structure_hint") or "Professional layout"))
    return (
        f"<div class='{root}-badge'>{label}</div>"
        f"<div class='{root}-structure'>{structure}</div>"
    )


def _summary_block(resume: dict[str, Any], profile: dict[str, Any], root: str) -> str:
    summary = (resume.get("personal") or {}).get("summary") or ""
    if not summary:
        return ""
    return (
        f"<h2 class='{root}-h'>{escape(_label(profile, 'summary'))}</h2>"
        f"<div class='{root}-desc'>{escape(summary)}</div>"
    )


def _skills_block(
    resume: dict[str, Any],
    profile: dict[str, Any],
    root: str,
    *,
    mode: str = "rows",
) -> str:
    skills = resume.get("skills") or {}
    if not any(skills.values()):
        return ""
    parts = [f"<h2 class='{root}-h'>{escape(_label(profile, 'skills'))}</h2>"]
    if mode == "chips":
        parts.append(f"<div class='{root}-chips'>")
        for values in skills.values():
            for value in values:
                parts.append(f"<span class='{root}-chip'>{escape(value)}</span>")
        parts.append("</div>")
    elif mode == "compact":
        flat = [v for values in skills.values() for v in values]
        parts.append(f"<div class='{root}-desc'>{escape(' · '.join(flat))}</div>")
    else:
        for skill_label, values in skills.items():
            if values:
                parts.append(
                    f"<div class='{root}-skill'><strong>{escape(skill_label)}:</strong> "
                    f"{escape(', '.join(values))}</div>"
                )
    return "".join(parts)


def _experience_block(
    resume: dict[str, Any],
    profile: dict[str, Any],
    root: str,
    *,
    project_style: str = "nested",
) -> str:
    jobs = resume.get("experience") or []
    if not jobs:
        return ""
    parts = [f"<h2 class='{root}-h'>{escape(_label(profile, 'experience'))}</h2>"]
    include_projects = profile.get("include_projects_under_experience", True)
    for job in jobs:
        if project_style == "split_date":
            parts.append(f"<div class='{root}-job-row'>")
            parts.append(
                f"<div class='{root}-job-main'>"
                f"<div class='{root}-job'>{escape(_job_heading(job, profile))}</div>"
            )
            loc = job.get("location") or ""
            if loc:
                parts.append(f"<div class='{root}-meta'>{escape(loc)}</div>")
            parts.append("</div>")
            parts.append(
                f"<div class='{root}-job-date'>{escape(job.get('date_range') or '')}</div>"
            )
            parts.append("</div>")
        else:
            parts.append(f"<div class='{root}-job'>{escape(_job_heading(job, profile))}</div>")
            meta = " | ".join(
                part for part in [job.get("date_range"), job.get("location")] if part
            )
            if meta:
                parts.append(f"<div class='{root}-meta'>{escape(meta)}</div>")

        for bullet in job.get("bullets") or []:
            parts.append(f"<ul class='{root}-ul'><li>{escape(bullet)}</li></ul>")

        if include_projects:
            for project in job.get("projects") or []:
                tenure = f" ({project['tenure']})" if project.get("tenure") else ""
                if project_style == "card":
                    parts.append(f"<div class='{root}-project-card'>")
                elif project_style == "rail":
                    parts.append(f"<div class='{root}-project-rail'>")
                else:
                    parts.append(f"<div class='{root}-project'>")
                parts.append(
                    f"<div class='{root}-project-title'>"
                    f"{escape(project.get('name') or 'Project')}{escape(tenure)}</div>"
                )
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
                    parts.append(
                        f"<div class='{root}-meta'>{escape(' · '.join(meta_bits))}</div>"
                    )
                if project.get("description"):
                    parts.append(
                        f"<div class='{root}-desc'>{escape(project['description'])}</div>"
                    )
                if project.get("technologies"):
                    tech = project["technologies"]
                    if isinstance(tech, list):
                        tech = ", ".join(tech)
                    parts.append(
                        f"<div class='{root}-desc'><strong>Technologies:</strong> "
                        f"{escape(str(tech))}</div>"
                    )
                bullets = list(project.get("bullets") or [])
                achievements = project.get("achievements") or []
                if isinstance(achievements, str):
                    achievements = [
                        line.strip(" •-\t")
                        for line in achievements.splitlines()
                        if line.strip()
                    ]
                bullets.extend(achievements)
                if bullets:
                    parts.append(f"<ul class='{root}-ul'>")
                    for bullet in bullets:
                        parts.append(f"<li>{escape(bullet)}</li>")
                    parts.append("</ul>")
                parts.append("</div>")
    return "".join(parts)


def _education_block(resume: dict[str, Any], profile: dict[str, Any], root: str) -> str:
    education = resume.get("education") or []
    if not education:
        return ""
    parts = [f"<h2 class='{root}-h'>{escape(_label(profile, 'education'))}</h2>"]
    for edu in education:
        years = " – ".join(
            part for part in [edu.get("start_year"), edu.get("end_year")] if part
        )
        headline = f"{edu.get('degree', '')} — {edu.get('institution', '')}"
        if years:
            headline += f" ({years})"
        parts.append(f"<div class='{root}-job'>{escape(headline)}</div>")
        if edu.get("details"):
            parts.append(f"<div class='{root}-desc'>{escape(edu['details'])}</div>")
    return "".join(parts)


def _certs_block(resume: dict[str, Any], profile: dict[str, Any], root: str) -> str:
    items = resume.get("certifications") or []
    if not items:
        return ""
    parts = [f"<h2 class='{root}-h'>{escape(_label(profile, 'certifications'))}</h2><ul class='{root}-ul'>"]
    for item in items:
        parts.append(f"<li>{escape(item)}</li>")
    parts.append("</ul>")
    return "".join(parts)


def _section_order(profile: dict[str, Any]) -> list[str]:
    return list(profile.get("section_order") or DEFAULT_SECTION_ORDER)


def _body_sections(
    resume: dict[str, Any],
    profile: dict[str, Any],
    root: str,
    *,
    skills_mode: str = "rows",
    project_style: str = "nested",
    skip: set[str] | None = None,
) -> str:
    skip = skip or set()
    chunks: list[str] = []
    for key in _section_order(profile):
        if key in skip:
            continue
        if key == "summary":
            chunks.append(_summary_block(resume, profile, root))
        elif key == "skills":
            chunks.append(_skills_block(resume, profile, root, mode=skills_mode))
        elif key == "experience":
            chunks.append(
                _experience_block(resume, profile, root, project_style=project_style)
            )
        elif key == "education":
            chunks.append(_education_block(resume, profile, root))
        elif key == "certifications":
            chunks.append(_certs_block(resume, profile, root))
    return "".join(chunks)


def _header_standard(
    personal: dict[str, Any],
    profile: dict[str, Any],
    root: str,
    *,
    stacked_contact: bool = False,
) -> str:
    parts = [
        _badge(profile, root),
        f"<div class='{root}-name'>{escape(personal.get('full_name') or 'Your Name')}</div>",
    ]
    if personal.get("target_title"):
        parts.append(
            f"<div class='{root}-title'>{escape(personal.get('target_title') or '')}</div>"
        )
    if stacked_contact:
        for value in [
            personal.get("phone"),
            personal.get("email"),
            personal.get("location"),
            personal.get("linkedin"),
        ]:
            if value:
                parts.append(f"<div class='{root}-contact-line'>{escape(str(value))}</div>")
    else:
        parts.append(
            f"<div class='{root}-contact'>{escape(_contact(personal, profile))}</div>"
        )
    return "".join(parts)


# --- Layout-specific renderers -------------------------------------------------

def _render_classic(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Segoe UI,sans-serif;color:{c['text']};background:#fff;border:1px solid #d7e0e8;padding:1.2rem 1.4rem;}}
.{root}-badge{{text-align:center;font-size:.7rem;font-weight:700;color:{c['accent']};letter-spacing:.06em;text-transform:uppercase;}}
.{root}-structure{{text-align:center;font-size:.75rem;color:{c['muted']};margin:.15rem 0 .6rem;}}
.{root}-name{{text-align:center;font-size:1.85rem;font-weight:800;color:{c['name']};}}
.{root}-title{{text-align:center;font-size:1.05rem;color:{c['title']};font-weight:600;margin:.1rem 0 .35rem;}}
.{root}-contact{{text-align:center;font-size:.84rem;color:{c['muted']};margin-bottom:.55rem;}}
.{root}-rule{{border:0;border-top:2px solid {c['accent']};margin:.2rem 0 .85rem;}}
.{root}-h{{text-align:center;font-size:.88rem;letter-spacing:.08em;text-transform:uppercase;color:{c['heading']};
border-top:1px solid {c['accent']};border-bottom:1px solid {c['accent']};padding:.28rem 0;margin:1rem 0 .45rem;}}
.{root}-job{{font-weight:700;margin:.55rem 0 .1rem;}}
.{root}-meta{{font-style:italic;color:{c['muted']};font-size:.86rem;}}
.{root}-project-title{{font-weight:700;color:{c['accent']};margin:.45rem 0 .1rem;}}
.{root}-desc{{font-size:.9rem;margin:.12rem 0;}}
.{root}-skill{{font-size:.88rem;margin:.1rem 0;}}
.{root}-ul{{margin:.15rem 0 .3rem 1.1rem;padding:0;}}
</style>"""
    body = (
        f"<div class='{root}'>"
        + _header_standard(personal, profile, root)
        + f"<hr class='{root}-rule'/>"
        + _body_sections(resume, profile, root, project_style="nested")
        + "</div>"
    )
    return css + body


def _render_traditional(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:'Times New Roman',Times,serif;color:{c['text']};background:#fff;border:1px solid #ccc;padding:1.15rem 1.35rem;}}
.{root}-badge{{font-size:.7rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{font-size:.75rem;color:{c['muted']};margin:.1rem 0 .5rem;}}
.{root}-name{{font-size:1.7rem;font-weight:800;color:{c['name']};border-bottom:3px double {c['accent']};padding-bottom:.25rem;}}
.{root}-title{{font-size:1rem;font-style:italic;margin:.25rem 0;color:{c['title']};}}
.{root}-contact{{font-size:.84rem;color:{c['muted']};margin-bottom:.7rem;}}
.{root}-h{{font-size:.95rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:{c['heading']};
border-bottom:2px solid {c['accent']};margin:1rem 0 .4rem;padding-bottom:.15rem;}}
.{root}-job{{font-weight:700;font-size:1rem;}}
.{root}-meta{{font-size:.86rem;color:{c['muted']};}}
.{root}-project-title{{font-weight:700;margin-top:.4rem;text-decoration:underline;}}
.{root}-desc,.{{font-size:.9rem;}} .{root}-desc{{font-size:.9rem;margin:.1rem 0;}}
.{root}-skill{{font-size:.88rem;margin:.08rem 0;}}
.{root}-ul{{margin:.12rem 0 .28rem 1.15rem;}}
</style>"""
    return (
        css
        + f"<div class='{root}'>"
        + _header_standard(personal, profile, root)
        + _body_sections(resume, profile, root, project_style="nested")
        + "</div>"
    )


def _render_prime_ats(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Arial,Helvetica,sans-serif;color:#111;background:#fff;border:1px solid #bbb;padding:1rem 1.1rem;}}
.{root}-badge,.{{color:#333}} .{root}-badge{{font-size:.68rem;font-weight:700;color:#333;text-transform:uppercase;}}
.{root}-structure{{font-size:.74rem;color:#555;margin-bottom:.45rem;}}
.{root}-name{{font-size:1.45rem;font-weight:800;color:#111;text-transform:uppercase;}}
.{root}-title{{font-size:.95rem;font-weight:700;margin:.15rem 0;color:#222;}}
.{root}-contact{{font-size:.82rem;color:#333;margin-bottom:.35rem;}}
.{root}-h{{font-size:.86rem;font-weight:800;text-transform:uppercase;margin:.85rem 0 .3rem;color:#111;
border-bottom:1px solid #111;padding-bottom:.12rem;letter-spacing:.04em;}}
.{root}-job{{font-weight:700;}}
.{root}-meta{{font-size:.82rem;color:#333;}}
.{root}-project-title{{font-weight:700;margin-top:.35rem;}}
.{root}-desc,.{{font-size:.86rem}} .{root}-desc{{font-size:.86rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.84rem;margin:.05rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.05rem;}}
</style>"""
    return (
        css
        + f"<div class='{root}'>"
        + _header_standard(personal, profile, root)
        + _body_sections(resume, profile, root, skills_mode="compact", project_style="nested")
        + "</div>"
    )


def _render_specialist_ats(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Arial,sans-serif;color:{c['text']};background:#fff;border-left:5px solid {c['accent']};padding:1rem 1.15rem;}}
.{root}-badge{{font-size:.68rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{font-size:.74rem;color:{c['muted']};margin-bottom:.45rem;}}
.{root}-name{{font-size:1.55rem;font-weight:800;color:{c['name']};}}
.{root}-title{{font-size:1rem;font-weight:700;color:{c['title']};}}
.{root}-contact{{font-size:.82rem;color:{c['muted']};margin:.2rem 0 .55rem;}}
.{root}-skills-box{{background:{c['accent']}12;border:1px solid {c['accent']}55;padding:.55rem .7rem;margin:.35rem 0 .7rem;}}
.{root}-h{{font-size:.86rem;font-weight:800;text-transform:uppercase;color:{c['heading']};margin:.8rem 0 .3rem;
border-bottom:2px solid {c['accent']};padding-bottom:.12rem;}}
.{root}-job{{font-weight:700;}}
.{root}-meta{{font-size:.84rem;color:{c['muted']};font-style:italic;}}
.{root}-project-title{{font-weight:700;color:{c['accent']};margin-top:.4rem;}}
.{root}-desc{{font-size:.88rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.84rem;margin:.06rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.05rem;}}
</style>"""
    skills = _skills_block(resume, profile, root, mode="rows")
    # Put skills in a highlighted box after summary.
    parts = [
        css,
        f"<div class='{root}'>",
        _header_standard(personal, profile, root),
        _summary_block(resume, profile, root),
        f"<div class='{root}-skills-box'>{skills}</div>" if skills else "",
        _body_sections(
            resume,
            profile,
            root,
            project_style="nested",
            skip={"summary", "skills"},
        ),
        "</div>",
    ]
    return "".join(parts)


def _render_clean(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    """Two-column: left sidebar (contact + skills), right main story."""
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Segoe UI,sans-serif;color:{c['text']};background:#fff;border:1px solid #e2e8f0;display:grid;grid-template-columns:32% 68%;min-height:420px;}}
.{root}-side{{background:#f4f8fa;padding:1rem .9rem;border-right:1px solid #d9e4ea;}}
.{root}-main{{padding:1rem 1.1rem;}}
.{root}-badge{{font-size:.65rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{font-size:.72rem;color:{c['muted']};margin:.1rem 0 .55rem;}}
.{root}-name{{font-size:1.45rem;font-weight:800;color:{c['name']};line-height:1.2;}}
.{root}-title{{font-size:.95rem;font-weight:600;color:{c['title']};margin:.2rem 0 .5rem;}}
.{root}-contact-line{{font-size:.78rem;color:{c['muted']};margin:.12rem 0;}}
.{root}-h{{font-size:.82rem;font-weight:700;color:{c['heading']};margin:.85rem 0 .35rem;text-transform:none;
border-left:3px solid {c['accent']};padding-left:.4rem;}}
.{root}-job{{font-weight:700;font-size:.95rem;}}
.{root}-meta{{font-size:.8rem;color:{c['muted']};}}
.{root}-project-rail{{border-left:3px solid {c['accent']}66;padding-left:.55rem;margin:.45rem 0;}}
.{root}-project-title{{font-weight:700;color:{c['accent']};}}
.{root}-desc{{font-size:.86rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.8rem;margin:.1rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1rem;font-size:.86rem;}}
.{root}-chips{{display:flex;flex-wrap:wrap;gap:.25rem;}}
.{root}-chip{{background:#fff;border:1px solid {c['accent']}66;color:{c['accent']};border-radius:999px;padding:.12rem .45rem;font-size:.72rem;}}
</style>"""
    side = (
        f"<div class='{root}-side'>"
        + _badge(profile, root)
        + f"<div class='{root}-name'>{escape(personal.get('full_name') or 'Your Name')}</div>"
        + (
            f"<div class='{root}-title'>{escape(personal.get('target_title') or '')}</div>"
            if personal.get("target_title")
            else ""
        )
        + "".join(
            f"<div class='{root}-contact-line'>{escape(str(v))}</div>"
            for v in [
                personal.get("phone"),
                personal.get("email"),
                personal.get("location"),
                personal.get("linkedin"),
            ]
            if v
        )
        + _skills_block(resume, profile, root, mode="chips")
        + _certs_block(resume, profile, root)
        + "</div>"
    )
    main = (
        f"<div class='{root}-main'>"
        + _summary_block(resume, profile, root)
        + _experience_block(resume, profile, root, project_style="rail")
        + _education_block(resume, profile, root)
        + "</div>"
    )
    return css + f"<div class='{root}'>{side}{main}</div>"


def _render_simple_ats(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Arial,Helvetica,sans-serif;color:#000;background:#fff;border:1px solid #999;padding:.95rem 1rem;}}
.{root}-badge{{font-size:.65rem;font-weight:700;color:#000;text-transform:uppercase;}}
.{root}-structure{{font-size:.72rem;color:#333;margin-bottom:.4rem;}}
.{root}-name{{font-size:1.35rem;font-weight:800;}}
.{root}-title{{font-size:.92rem;margin:.1rem 0 .25rem;}}
.{root}-contact-line{{font-size:.8rem;margin:.05rem 0;}}
.{root}-h{{font-size:.84rem;font-weight:800;text-transform:uppercase;margin:.75rem 0 .25rem;
border-bottom:1px solid #000;padding-bottom:.08rem;}}
.{root}-job{{font-weight:700;font-size:.92rem;}}
.{root}-meta{{font-size:.8rem;}}
.{root}-project-title{{font-weight:700;margin-top:.3rem;}}
.{root}-desc{{font-size:.84rem;margin:.06rem 0;}}
.{root}-skill{{font-size:.82rem;}}
.{root}-ul{{margin:.08rem 0 .2rem 1rem;}}
</style>"""
    return (
        css
        + f"<div class='{root}'>"
        + _header_standard(personal, profile, root, stacked_contact=True)
        + _body_sections(resume, profile, root, skills_mode="compact", project_style="nested")
        + "</div>"
    )


def _render_corporate_fixed(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    """Corporate banner + split date rows (clean implementation)."""
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Segoe UI,sans-serif;color:{c['text']};background:#fff;border:1px solid #cfd8e3;overflow:hidden;}}
.{root}-banner{{background:{c['accent']};color:#fff;padding:1rem 1.15rem .85rem;}}
.{root}-badge{{font-size:.65rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;opacity:.9;}}
.{root}-structure{{font-size:.72rem;opacity:.85;margin:.1rem 0 .35rem;}}
.{root}-name{{font-size:1.7rem;font-weight:800;color:#fff;}}
.{root}-title{{font-size:1rem;font-weight:600;color:#e8f2f8;margin-top:.15rem;}}
.{root}-contact{{font-size:.82rem;color:#d7e6ef;margin-top:.35rem;}}
.{root}-body{{padding:.85rem 1.15rem 1.15rem;border-left:6px solid {c['accent']};}}
.{root}-h{{font-size:.86rem;font-weight:800;text-transform:uppercase;color:{c['heading']};background:{c['accent']}14;
padding:.28rem .45rem;margin:.85rem 0 .35rem;}}
.{root}-job-row{{display:flex;justify-content:space-between;gap:.75rem;margin-top:.5rem;}}
.{root}-job-main{{flex:1;}}
.{root}-job{{font-weight:700;}}
.{root}-job-date{{font-size:.82rem;color:{c['muted']};white-space:nowrap;}}
.{root}-meta{{font-size:.84rem;color:{c['muted']};}}
.{root}-project-title{{font-weight:700;color:{c['accent']};margin-top:.4rem;}}
.{root}-desc{{font-size:.88rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.86rem;margin:.06rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.05rem;}}
</style>"""
    header = (
        f"<div class='{root}-banner'>"
        + _badge(profile, root)
        + f"<div class='{root}-name'>{escape(personal.get('full_name') or 'Your Name')}</div>"
        + (
            f"<div class='{root}-title'>{escape(personal.get('target_title') or '')}</div>"
            if personal.get("target_title")
            else ""
        )
        + f"<div class='{root}-contact'>{escape(_contact(personal, profile))}</div>"
        + "</div>"
    )
    body = (
        _summary_block(resume, profile, root)
        + _skills_block(resume, profile, root, mode="rows")
        + _experience_block(resume, profile, root, project_style="split_date")
        + _education_block(resume, profile, root)
        + _certs_block(resume, profile, root)
    )
    return css + f"<div class='{root}'>{header}<div class='{root}-body'>{body}</div></div>"


def _render_harmonized(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Segoe UI,sans-serif;color:{c['text']};background:#fff;border:1px solid #d5e6ea;padding:1.15rem 1.3rem;border-radius:10px;}}
.{root}-badge{{text-align:center;font-size:.68rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{text-align:center;font-size:.74rem;color:{c['muted']};margin-bottom:.45rem;}}
.{root}-name{{text-align:center;font-size:1.8rem;font-weight:800;color:{c['name']};}}
.{root}-title{{text-align:center;font-size:1.02rem;color:{c['title']};font-weight:600;}}
.{root}-contact{{text-align:center;font-size:.84rem;color:{c['muted']};margin:.25rem 0 .55rem;}}
.{root}-h{{display:inline-block;background:{c['accent']};color:#fff;border-radius:999px;padding:.18rem .7rem;
font-size:.78rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin:.85rem 0 .4rem;}}
.{root}-job{{font-weight:700;}}
.{root}-meta{{font-size:.84rem;color:{c['muted']};font-style:italic;}}
.{root}-project-card{{background:{c['accent']}0d;border:1px solid {c['accent']}33;border-radius:8px;padding:.45rem .55rem;margin:.4rem 0;}}
.{root}-project-title{{font-weight:700;color:{c['accent']};}}
.{root}-desc{{font-size:.88rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.86rem;margin:.06rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.05rem;}}
</style>"""
    return (
        css
        + f"<div class='{root}'>"
        + _header_standard(personal, profile, root)
        + _body_sections(resume, profile, root, project_style="card")
        + "</div>"
    )


def _render_modern_professional(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:Calibri,Segoe UI,sans-serif;color:{c['text']};background:linear-gradient(#fff,#f7fbfc);border:1px solid #d7e7ec;padding:1.2rem 1.35rem;}}
.{root}-badge{{text-align:center;font-size:.68rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{text-align:center;font-size:.74rem;color:{c['muted']};margin-bottom:.4rem;}}
.{root}-name{{text-align:center;font-size:2rem;font-weight:800;color:{c['name']};}}
.{root}-title{{text-align:center;font-size:1.08rem;color:{c['title']};font-weight:600;margin-bottom:.2rem;}}
.{root}-accentbar{{height:4px;width:88px;background:{c['accent']};margin:.2rem auto .55rem;border-radius:4px;}}
.{root}-contact{{text-align:center;font-size:.84rem;color:{c['muted']};margin-bottom:.7rem;}}
.{root}-h{{font-size:.88rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:{c['heading']};
border-bottom:2px solid {c['accent']};padding-bottom:.18rem;margin:1rem 0 .4rem;}}
.{root}-job{{font-weight:700;}}
.{root}-meta{{font-size:.84rem;color:{c['muted']};}}
.{root}-project-rail{{margin:.45rem 0 .35rem;padding-left:.7rem;border-left:3px solid {c['accent']};}}
.{root}-project-title{{font-weight:700;color:{c['accent']};}}
.{root}-desc{{font-size:.88rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.86rem;margin:.06rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.05rem;}}
.{root}-chips{{display:flex;flex-wrap:wrap;gap:.28rem;margin-top:.2rem;}}
.{root}-chip{{background:{c['accent']}14;color:{c['accent']};border-radius:6px;padding:.14rem .45rem;font-size:.75rem;font-weight:600;}}
</style>"""
    header = (
        _badge(profile, root)
        + f"<div class='{root}-name'>{escape(personal.get('full_name') or 'Your Name')}</div>"
        + (
            f"<div class='{root}-title'>{escape(personal.get('target_title') or '')}</div>"
            if personal.get("target_title")
            else ""
        )
        + f"<div class='{root}-accentbar'></div>"
        + f"<div class='{root}-contact'>{escape(_contact(personal, profile))}</div>"
    )
    return (
        css
        + f"<div class='{root}'>{header}"
        + _summary_block(resume, profile, root)
        + _skills_block(resume, profile, root, mode="chips")
        + _experience_block(resume, profile, root, project_style="rail")
        + _education_block(resume, profile, root)
        + _certs_block(resume, profile, root)
        + "</div>"
    )


def _render_classic_corporate(resume: dict[str, Any], profile: dict[str, Any]) -> str:
    root = f"lay-{_scope(profile)}"
    c = _colors(profile)
    personal = resume.get("personal") or {}
    css = f"""
<style>
.{root}{{font-family:'Times New Roman',Times,serif;color:{c['text']};background:#fff;border:1px solid #b7c2cc;padding:1.1rem 1.25rem;}}
.{root}-badge{{font-size:.68rem;font-weight:700;color:{c['accent']};text-transform:uppercase;}}
.{root}-structure{{font-size:.74rem;color:{c['muted']};margin-bottom:.4rem;}}
.{root}-name{{font-size:1.65rem;font-weight:800;color:{c['name']};text-transform:uppercase;letter-spacing:.03em;}}
.{root}-title{{font-size:1rem;margin:.15rem 0;color:{c['title']};}}
.{root}-contact{{font-size:.84rem;color:{c['muted']};margin-bottom:.55rem;}}
.{root}-h{{font-size:.9rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:#fff;background:{c['accent']};
padding:.22rem .45rem;margin:.9rem 0 .35rem;}}
.{root}-job{{font-weight:700;}}
.{root}-meta{{font-size:.84rem;color:{c['muted']};}}
.{root}-project-title{{font-weight:700;margin-top:.35rem;text-decoration:underline;}}
.{root}-desc{{font-size:.9rem;margin:.08rem 0;}}
.{root}-skill{{font-size:.88rem;margin:.06rem 0;}}
.{root}-ul{{margin:.1rem 0 .25rem 1.1rem;}}
</style>"""
    return (
        css
        + f"<div class='{root}'>"
        + _header_standard(personal, profile, root)
        + _body_sections(resume, profile, root, project_style="nested")
        + "</div>"
    )


LAYOUT_RENDERERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], str]] = {
    "classic": _render_classic,
    "traditional": _render_traditional,
    "prime_ats": _render_prime_ats,
    "specialist_ats": _render_specialist_ats,
    "clean": _render_clean,
    "simple_ats": _render_simple_ats,
    "corporate": _render_corporate_fixed,
    "harmonized": _render_harmonized,
    "modern_professional": _render_modern_professional,
    "classic_corporate": _render_classic_corporate,
}
