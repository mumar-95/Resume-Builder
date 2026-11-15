"""Parse uploaded Word/PDF reference resumes into text + format profile."""

from __future__ import annotations

import io
import re
from typing import Any

SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("summary", re.compile(r"^(professional\s+)?summary|profile|objective|about\s+me$", re.I)),
    ("skills", re.compile(r"^(technical\s+)?skills|core\s+competenc|technologies|tech\s+stack|expertise$", re.I)),
    ("experience", re.compile(r"^(professional\s+|work\s+)?experience|employment|work\s+history|career$", re.I)),
    ("projects", re.compile(r"^projects?|key\s+projects$", re.I)),
    ("education", re.compile(r"^education|academic|qualifications?$", re.I)),
    ("certifications", re.compile(r"^certifications?|licenses?|credentials$", re.I)),
    ("achievements", re.compile(r"^(key\s+)?achievements?|accomplishments?|awards?$", re.I)),
]

DEFAULT_SECTION_ORDER = [
    "summary",
    "skills",
    "experience",
    "education",
    "certifications",
    "achievements",
]

DEFAULT_LABELS = {
    "summary": "PROFESSIONAL SUMMARY",
    "skills": "TECHNICAL SKILLS",
    "experience": "PROFESSIONAL EXPERIENCE",
    "projects": "PROJECTS",
    "education": "EDUCATION",
    "certifications": "CERTIFICATIONS",
    "achievements": "KEY ACHIEVEMENTS",
}


def parse_reference_resume(file_bytes: bytes, filename: str) -> dict[str, Any]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = _extract_pdf_text(file_bytes)
        file_type = "pdf"
        format_profile = _format_profile_from_text(text, file_type="pdf")
    elif lower.endswith(".docx"):
        text, format_profile = _extract_docx_with_format(file_bytes)
        file_type = "docx"
    elif lower.endswith(".doc"):
        raise ValueError(
            "Legacy .doc files are not supported. Please save as .docx or PDF and upload again."
        )
    else:
        raise ValueError("Unsupported file type. Upload a .docx or .pdf file.")

    hints = _extract_hints(text)
    return {
        "text": text.strip(),
        "file_type": file_type,
        "hints": hints,
        "format_profile": format_profile,
    }


def _extract_pdf_text(file_bytes: bytes) -> str:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n".join(pages)


def _extract_docx_with_format(file_bytes: bytes) -> tuple[str, dict[str, Any]]:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    document = Document(io.BytesIO(file_bytes))
    parts: list[str] = []
    paragraph_meta: list[dict[str, Any]] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        parts.append(text)
        alignment = paragraph.alignment
        first_run = paragraph.runs[0] if paragraph.runs else None
        font_name = None
        font_size = None
        bold = False
        if first_run is not None:
            font_name = first_run.font.name
            if first_run.font.size:
                font_size = first_run.font.size.pt
            bold = bool(first_run.bold or (first_run.font.bold if first_run.font else False))
        paragraph_meta.append(
            {
                "text": text,
                "alignment": _alignment_name(alignment),
                "font_name": font_name,
                "font_size": font_size,
                "bold": bold,
                "all_caps": text.isupper() and len(text) > 2,
            }
        )

    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    text = "\n".join(parts)
    profile = _format_profile_from_text(text, file_type="docx")

    section = document.sections[0]
    profile["margins_inches"] = {
        "top": round(section.top_margin.inches, 2) if section.top_margin else 0.6,
        "bottom": round(section.bottom_margin.inches, 2) if section.bottom_margin else 0.6,
        "left": round(section.left_margin.inches, 2) if section.left_margin else 0.7,
        "right": round(section.right_margin.inches, 2) if section.right_margin else 0.7,
    }
    profile["page_width_inches"] = (
        round(section.page_width.inches, 2) if section.page_width else 8.5
    )
    profile["page_height_inches"] = (
        round(section.page_height.inches, 2) if section.page_height else 11.0
    )
    profile["has_tables"] = bool(document.tables)

    # Font / header cues from early paragraphs
    if paragraph_meta:
        name_para = paragraph_meta[0]
        profile["name_alignment"] = name_para.get("alignment") or "center"
        profile["name_font_size"] = name_para.get("font_size") or 18
        profile["name_bold"] = bool(name_para.get("bold", True))
        body_fonts = [
            p.get("font_name")
            for p in paragraph_meta[1:8]
            if p.get("font_name")
        ]
        profile["body_font"] = body_fonts[0] if body_fonts else (name_para.get("font_name") or "Calibri")
        profile["name_font"] = name_para.get("font_name") or profile["body_font"]

        heading_sizes = [
            p.get("font_size")
            for p in paragraph_meta
            if p.get("all_caps") or (p.get("bold") and len(p.get("text", "").split()) <= 5)
        ]
        profile["heading_font_size"] = next((s for s in heading_sizes if s), 11)
        profile["heading_all_caps"] = any(p.get("all_caps") for p in paragraph_meta[:20])
        profile["heading_bold"] = True

        # Contact separator style
        contact_candidates = paragraph_meta[1:4]
        for candidate in contact_candidates:
            sample = candidate["text"]
            if "@" in sample or "linkedin" in sample.lower() or re.search(r"\d{3}", sample):
                if " | " in sample:
                    profile["contact_separator"] = " | "
                elif " • " in sample or "·" in sample:
                    profile["contact_separator"] = " • "
                elif " - " in sample:
                    profile["contact_separator"] = " - "
                else:
                    profile["contact_separator"] = " | "
                profile["contact_alignment"] = candidate.get("alignment") or profile["name_alignment"]
                break

        # Job line style heuristic from experience block
        profile["job_line_style"] = _detect_job_line_style(parts)

    return text, profile


def _format_profile_from_text(text: str, *, file_type: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    section_labels: dict[str, str] = {}
    section_order: list[str] = []

    for line in lines:
        key = _match_section_key(line)
        if key and key not in section_labels:
            section_labels[key] = line.strip()
            section_order.append(key)

    if not section_order:
        section_order = list(DEFAULT_SECTION_ORDER)
        section_labels = dict(DEFAULT_LABELS)
    else:
        for key in DEFAULT_SECTION_ORDER:
            section_labels.setdefault(key, DEFAULT_LABELS[key])
            if key not in section_order and key in ("summary", "skills", "experience", "education"):
                section_order.append(key)

    heading_all_caps = any(label.isupper() for label in section_labels.values())
    return {
        "file_type": file_type,
        "section_order": section_order,
        "section_labels": section_labels,
        "name_alignment": "center",
        "contact_alignment": "center",
        "contact_separator": " | ",
        "body_font": "Calibri",
        "name_font": "Calibri",
        "name_font_size": 18,
        "name_bold": True,
        "heading_font_size": 11,
        "heading_all_caps": heading_all_caps,
        "heading_bold": True,
        "heading_underline": True,
        "body_font_size": 11,
        "job_line_style": "title_emdash_company",
        "margins_inches": {"top": 0.6, "bottom": 0.6, "left": 0.7, "right": 0.7},
        "has_tables": False,
        "include_projects_under_experience": "projects" not in section_order,
    }


def _match_section_key(line: str) -> str | None:
    cleaned = re.sub(r"^[\W_]+|[\W_]+$", "", line.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    if len(cleaned.split()) > 6:
        return None
    for key, pattern in SECTION_PATTERNS:
        if pattern.match(cleaned):
            return key
    return None


def _alignment_name(alignment: Any) -> str:
    try:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if alignment == WD_ALIGN_PARAGRAPH.LEFT:
            return "left"
        if alignment == WD_ALIGN_PARAGRAPH.RIGHT:
            return "right"
        if alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
            return "justify"
        if alignment == WD_ALIGN_PARAGRAPH.CENTER:
            return "center"
    except Exception:
        pass
    return "center"


def _detect_job_line_style(lines: list[str]) -> str:
    for line in lines:
        lower = line.lower()
        if " at " in lower and len(line) < 90:
            return "title_at_company"
        if " | " in line and len(line) < 100:
            return "title_pipe_company"
        if " — " in line or " – " in line:
            return "title_emdash_company"
        if " - " in line and len(line.split(" - ")) == 2 and len(line) < 90:
            return "title_dash_company"
    return "title_emdash_company"


def _extract_hints(text: str) -> dict[str, str]:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(
        r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}",
        text,
    )
    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s]+", text, re.I)
    github_match = re.search(r"(https?://)?(www\.)?github\.com/[^\s]+", text, re.I)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    possible_name = lines[0] if lines else ""
    if "@" in possible_name or len(possible_name.split()) > 6:
        possible_name = ""

    return {
        "full_name": possible_name[:80],
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "linkedin": linkedin_match.group(0) if linkedin_match else "",
        "github": github_match.group(0) if github_match else "",
    }
