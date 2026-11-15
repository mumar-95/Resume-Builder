"""Export generated resumes to Word (.docx) and PDF, optionally matching a reference format."""

from __future__ import annotations

import io
from typing import Any

from utils.resume_parser import DEFAULT_LABELS, DEFAULT_SECTION_ORDER


def export_docx(resume: dict[str, Any]) -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    profile = _active_profile(resume)
    document = Document()
    section = document.sections[0]
    margins = profile.get("margins_inches", {})
    section.top_margin = Inches(float(margins.get("top", 0.6)))
    section.bottom_margin = Inches(float(margins.get("bottom", 0.6)))
    section.left_margin = Inches(float(margins.get("left", 0.7)))
    section.right_margin = Inches(float(margins.get("right", 0.7)))

    body_font = profile.get("body_font") or "Calibri"
    body_size = float(profile.get("body_font_size") or 11)
    normal = document.styles["Normal"]
    normal.font.name = body_font
    normal.font.size = Pt(body_size)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), body_font)

    personal = resume["personal"]
    name_align = _docx_align(profile.get("name_alignment", "center"))
    contact_align = _docx_align(profile.get("contact_alignment", profile.get("name_alignment", "center")))

    name = document.add_paragraph()
    name.alignment = name_align
    run = name.add_run(personal.get("full_name") or "Your Name")
    run.bold = bool(profile.get("name_bold", True))
    run.font.size = Pt(float(profile.get("name_font_size") or 18))
    run.font.name = profile.get("name_font") or body_font
    run.font.color.rgb = RGBColor(0x0A, 0x2F, 0x45)

    if personal.get("target_title"):
        title = document.add_paragraph()
        title.alignment = name_align
        title_run = title.add_run(personal.get("target_title") or "")
        title_run.font.size = Pt(12)
        title_run.font.name = body_font
        title_run.font.color.rgb = RGBColor(0x0E, 0x7C, 0x86)

    contact = document.add_paragraph()
    contact.alignment = contact_align
    contact_run = contact.add_run(_contact_line(personal, profile))
    contact_run.font.size = Pt(9)
    contact_run.font.name = body_font

    for section_key in profile.get("section_order") or DEFAULT_SECTION_ORDER:
        _write_docx_section(document, resume, section_key, profile)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def export_pdf(resume: dict[str, Any]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    profile = _active_profile(resume)
    margins = profile.get("margins_inches", {})
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=float(margins.get("left", 0.7)) * inch,
        rightMargin=float(margins.get("right", 0.7)) * inch,
        topMargin=float(margins.get("top", 0.6)) * inch,
        bottomMargin=float(margins.get("bottom", 0.6)) * inch,
    )

    align_map = {
        "left": TA_LEFT,
        "center": TA_CENTER,
        "right": TA_RIGHT,
        "justify": TA_JUSTIFY,
    }
    name_align = align_map.get(profile.get("name_alignment", "center"), TA_CENTER)
    contact_align = align_map.get(
        profile.get("contact_alignment", profile.get("name_alignment", "center")),
        TA_CENTER,
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "NameStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=float(profile.get("name_font_size") or 18),
        textColor=colors.HexColor("#0A2F45"),
        alignment=name_align,
        spaceAfter=2,
    )
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=colors.HexColor("#0E7C86"),
        alignment=name_align,
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "ContactStyle",
        parent=styles["Normal"],
        fontSize=8.5,
        alignment=contact_align,
        textColor=colors.HexColor("#102A3A"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=float(profile.get("heading_font_size") or 11),
        textColor=colors.HexColor("#0A2F45"),
        spaceBefore=10,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=float(profile.get("body_font_size") or 10),
        leading=13,
        textColor=colors.HexColor("#102A3A"),
    )
    job_style = ParagraphStyle(
        "JobStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#102A3A"),
        spaceBefore=6,
    )
    meta_style = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#5A7585"),
        spaceAfter=2,
    )
    project_style = ParagraphStyle(
        "ProjectStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#0E7C86"),
        spaceBefore=4,
    )

    personal = resume["personal"]
    story: list[Any] = [
        Paragraph(_escape(personal.get("full_name") or "Your Name"), name_style),
    ]
    if personal.get("target_title"):
        story.append(Paragraph(_escape(personal.get("target_title") or ""), title_style))
    story.append(Paragraph(_escape(_contact_line(personal, profile)), contact_style))
    if profile.get("heading_underline", True):
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0E7C86")))

    for section_key in profile.get("section_order") or DEFAULT_SECTION_ORDER:
        story.extend(
            _pdf_section_flowables(
                resume,
                section_key,
                profile,
                section_style=section_style,
                body_style=body_style,
                job_style=job_style,
                meta_style=meta_style,
                project_style=project_style,
            )
        )

    story.append(Spacer(1, 8))
    doc.build(story)
    return buffer.getvalue()


def _active_profile(resume: dict[str, Any]) -> dict[str, Any]:
    if resume.get("use_reference_format") and resume.get("format_profile"):
        return resume["format_profile"]
    return {
        "section_order": list(DEFAULT_SECTION_ORDER),
        "section_labels": dict(DEFAULT_LABELS),
        "name_alignment": "center",
        "contact_alignment": "center",
        "contact_separator": " | ",
        "body_font": "Calibri",
        "name_font": "Calibri",
        "name_font_size": 18,
        "name_bold": True,
        "heading_font_size": 11,
        "heading_all_caps": True,
        "heading_bold": True,
        "heading_underline": True,
        "body_font_size": 11,
        "job_line_style": "title_emdash_company",
        "margins_inches": {"top": 0.6, "bottom": 0.6, "left": 0.7, "right": 0.7},
        "include_projects_under_experience": True,
    }


def _section_label(profile: dict[str, Any], key: str) -> str:
    labels = profile.get("section_labels") or {}
    label = labels.get(key) or DEFAULT_LABELS.get(key, key.upper())
    if profile.get("heading_all_caps", True):
        return label.upper()
    return label


def _contact_line(personal: dict[str, Any], profile: dict[str, Any]) -> str:
    sep = profile.get("contact_separator") or " | "
    return sep.join(
        part
        for part in [
            personal.get("email"),
            personal.get("phone"),
            personal.get("location"),
            personal.get("linkedin"),
            personal.get("github"),
            personal.get("portfolio"),
        ]
        if part
    )


def _job_heading(job: dict[str, Any], profile: dict[str, Any]) -> str:
    title = job.get("job_title", "") or ""
    company = job.get("company_name", "") or ""
    style = profile.get("job_line_style") or "title_emdash_company"
    if style == "title_at_company":
        return f"{title} at {company}".strip()
    if style == "title_pipe_company":
        return f"{title} | {company}".strip(" |")
    if style == "title_dash_company":
        return f"{title} - {company}".strip(" -")
    return f"{title} — {company}".strip(" —")


def _write_docx_section(
    document: Any, resume: dict[str, Any], section_key: str, profile: dict[str, Any]
) -> None:
    label = _section_label(profile, section_key)

    if section_key == "summary":
        _add_heading(document, label, profile)
        document.add_paragraph(resume["personal"].get("summary") or "")
        return

    if section_key == "skills":
        skills = resume.get("skills") or {}
        if not any(skills.values()):
            return
        _add_heading(document, label, profile)
        for skill_label, values in skills.items():
            if values:
                paragraph = document.add_paragraph()
                label_run = paragraph.add_run(f"{skill_label}: ")
                label_run.bold = True
                paragraph.add_run(", ".join(values))
        return

    if section_key == "experience":
        if not resume.get("experience"):
            return
        _add_heading(document, label, profile)
        include_projects = profile.get("include_projects_under_experience", True)
        for job in resume["experience"]:
            heading = document.add_paragraph()
            company_run = heading.add_run(_job_heading(job, profile))
            company_run.bold = True
            company_run.font.size = Pt_safe(12)

            meta = document.add_paragraph()
            meta_text = " | ".join(
                part for part in [job.get("date_range"), job.get("location")] if part
            )
            meta_run = meta.add_run(meta_text)
            meta_run.italic = True
            meta_run.font.size = Pt_safe(10)

            if job.get("technologies"):
                tech = document.add_paragraph()
                tech_label = tech.add_run("Technologies: ")
                tech_label.bold = True
                tech.add_run(", ".join(job["technologies"]))

            for bullet in job.get("bullets", []):
                document.add_paragraph(bullet, style="List Bullet")

            if include_projects:
                _write_docx_projects(document, job.get("projects", []))
        return

    if section_key == "projects":
        projects = [
            project
            for job in resume.get("experience", [])
            for project in job.get("projects", [])
        ]
        if not projects:
            return
        _add_heading(document, label, profile)
        _write_docx_projects(document, projects)
        return

    if section_key == "education":
        if not resume.get("education"):
            return
        _add_heading(document, label, profile)
        for edu in resume["education"]:
            years = " – ".join(
                part for part in [edu.get("start_year"), edu.get("end_year")] if part
            )
            line = document.add_paragraph()
            degree_run = line.add_run(edu.get("degree") or "")
            degree_run.bold = True
            rest = f" — {edu.get('institution', '')}"
            if years:
                rest += f" ({years})"
            line.add_run(rest)
            if edu.get("details"):
                document.add_paragraph(edu["details"])
        return

    if section_key == "certifications":
        if not resume.get("certifications"):
            return
        _add_heading(document, label, profile)
        for item in resume["certifications"]:
            document.add_paragraph(item, style="List Bullet")
        return

    if section_key == "achievements":
        if not resume.get("achievements"):
            return
        _add_heading(document, label, profile)
        for item in resume["achievements"]:
            document.add_paragraph(item, style="List Bullet")


def _write_docx_projects(document: Any, projects: list[dict[str, Any]]) -> None:
    for project in projects:
        project_heading = document.add_paragraph()
        tenure = f" ({project['tenure']})" if project.get("tenure") else ""
        project_run = project_heading.add_run(f"{project.get('name', 'Project')}{tenure}")
        project_run.bold = True
        if project.get("description"):
            document.add_paragraph(project["description"])
        for bullet in project.get("bullets", []):
            document.add_paragraph(bullet, style="List Bullet")


def _pdf_section_flowables(
    resume: dict[str, Any],
    section_key: str,
    profile: dict[str, Any],
    *,
    section_style: Any,
    body_style: Any,
    job_style: Any,
    meta_style: Any,
    project_style: Any,
) -> list[Any]:
    from reportlab.platypus import Paragraph

    label = _section_label(profile, section_key)
    flows: list[Any] = []

    if section_key == "summary":
        flows.append(Paragraph(_escape(label), section_style))
        flows.append(Paragraph(_escape(resume["personal"].get("summary") or ""), body_style))
        return flows

    if section_key == "skills":
        skills = resume.get("skills") or {}
        if not any(skills.values()):
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        for skill_label, values in skills.items():
            if values:
                flows.append(
                    Paragraph(
                        f"<b>{_escape(skill_label)}:</b> {_escape(', '.join(values))}",
                        body_style,
                    )
                )
        return flows

    if section_key == "experience":
        if not resume.get("experience"):
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        include_projects = profile.get("include_projects_under_experience", True)
        for job in resume["experience"]:
            flows.append(Paragraph(_escape(_job_heading(job, profile)), job_style))
            meta = " | ".join(
                part for part in [job.get("date_range"), job.get("location")] if part
            )
            if meta:
                flows.append(Paragraph(_escape(meta), meta_style))
            if job.get("technologies"):
                flows.append(
                    Paragraph(
                        f"<b>Technologies:</b> {_escape(', '.join(job['technologies']))}",
                        body_style,
                    )
                )
            flows.extend(_bullet_list(job.get("bullets", []), body_style))
            if include_projects:
                flows.extend(
                    _pdf_projects(
                        job.get("projects", []),
                        body_style=body_style,
                        project_style=project_style,
                    )
                )
        return flows

    if section_key == "projects":
        projects = [
            project
            for job in resume.get("experience", [])
            for project in job.get("projects", [])
        ]
        if not projects:
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        flows.extend(
            _pdf_projects(projects, body_style=body_style, project_style=project_style)
        )
        return flows

    if section_key == "education":
        if not resume.get("education"):
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        for edu in resume["education"]:
            years = " – ".join(
                part for part in [edu.get("start_year"), edu.get("end_year")] if part
            )
            line = f"<b>{_escape(edu.get('degree') or '')}</b> — {_escape(edu.get('institution') or '')}"
            if years:
                line += f" ({_escape(years)})"
            flows.append(Paragraph(line, body_style))
            if edu.get("details"):
                flows.append(Paragraph(_escape(edu["details"]), body_style))
        return flows

    if section_key == "certifications":
        if not resume.get("certifications"):
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        flows.extend(_bullet_list(resume["certifications"], body_style))
        return flows

    if section_key == "achievements":
        if not resume.get("achievements"):
            return flows
        flows.append(Paragraph(_escape(label), section_style))
        flows.extend(_bullet_list(resume["achievements"], body_style))
        return flows

    return flows


def _pdf_projects(
    projects: list[dict[str, Any]], *, body_style: Any, project_style: Any
) -> list[Any]:
    from reportlab.platypus import Paragraph

    flows: list[Any] = []
    for project in projects:
        tenure = f" ({project['tenure']})" if project.get("tenure") else ""
        flows.append(
            Paragraph(_escape(f"{project.get('name', 'Project')}{tenure}"), project_style)
        )
        if project.get("description"):
            flows.append(Paragraph(_escape(project["description"]), body_style))
        flows.extend(_bullet_list(project.get("bullets", []), body_style))
    return flows


def _add_heading(document: Any, text: str, profile: dict[str, Any] | None = None) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    profile = profile or {}
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    run.bold = bool(profile.get("heading_bold", True))
    run.font.size = Pt(float(profile.get("heading_font_size") or 11))
    run.font.name = profile.get("body_font") or "Calibri"
    run.font.color.rgb = RGBColor(0x0A, 0x2F, 0x45)

    if profile.get("heading_underline", True):
        p = paragraph._p
        p_pr = p.get_or_add_pPr()
        p_bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "0E7C86")
        p_bdr.append(bottom)
        p_pr.append(p_bdr)


def _docx_align(name: str) -> Any:
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    return {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
    }.get(name, WD_ALIGN_PARAGRAPH.CENTER)


def Pt_safe(value: float) -> Any:
    from docx.shared import Pt

    return Pt(value)


def _bullet_list(items: list[str], style: Any) -> list[Any]:
    from reportlab.platypus import ListFlowable, ListItem, Paragraph

    if not items:
        return []
    return [
        ListFlowable(
            [
                ListItem(
                    Paragraph(_escape(item), style),
                    leftIndent=12,
                    bulletColor="#0E7C86",
                )
                for item in items
            ],
            bulletType="bullet",
            start="•",
            leftIndent=12,
            bulletFontSize=8,
        )
    ]


def _escape(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
