"""Template-aware soft page backgrounds for the Streamlit UI."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Family → soft atmospheric backdrop (low-contrast, designed for overlays).
BACKGROUND_FILES = {
    "ats": ASSETS / "bg_ats_soft.jpg",
    "corporate": ASSETS / "bg_corporate_soft.jpg",
    "modern": ASSETS / "bg_modern_soft.jpg",
}

TEMPLATE_BACKGROUND_FAMILY = {
    "Prime ATS": "ats",
    "Specialist ATS": "ats",
    "Simple ATS": "ats",
    "Tech Minimal": "ats",
    "Midnight ATS": "ats",
    "Fresh Graduate": "ats",
    "Skill Forward": "ats",
    "Classic": "corporate",
    "Traditional": "corporate",
    "Corporate": "corporate",
    "Classic Corporate": "corporate",
    "Executive Compact": "corporate",
    "Elegant Serif": "corporate",
    "Consultant Focus": "corporate",
    "Clean": "modern",
    "Harmonized": "modern",
    "Modern Professional": "modern",
    "Impact Banner": "modern",
    "Timeline Pro": "modern",
    "Nordic Clean": "modern",
}

# Fallback to existing hero art if generated backgrounds are missing.
FAMILY_FALLBACKS = {
    "ats": ASSETS / "step_preview.jpg",
    "corporate": ASSETS / "careerforge_hero.jpg",
    "modern": ASSETS / "step_personal.jpg",
}


def background_family_for_template(template_name: str) -> str:
    return TEMPLATE_BACKGROUND_FAMILY.get(template_name or "", "modern")


def welcome_background_path() -> Path | None:
    """Prefer the CareerForge hero artwork for the Welcome landing page."""
    hero = ASSETS / "careerforge_hero.jpg"
    if hero.exists():
        return hero
    modern = BACKGROUND_FILES.get("modern")
    if modern and modern.exists():
        return modern
    fallback = FAMILY_FALLBACKS.get("modern")
    return fallback if fallback and fallback.exists() else None


def background_image_path(template_name: str) -> Path | None:
    family = background_family_for_template(template_name)
    primary = BACKGROUND_FILES.get(family)
    if primary and primary.exists():
        return primary
    fallback = FAMILY_FALLBACKS.get(family)
    if fallback and fallback.exists():
        return fallback
    hero = ASSETS / "careerforge_hero.jpg"
    return hero if hero.exists() else None


def _data_uri(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def page_atmosphere_css(
    template_name: str,
    *,
    accent_color: str = "#0E7C86",
    intensity: str = "balanced",
) -> str:
    """
    Background image behind the app; content panels stay opaque in the foreground.

    intensity:
      - hero: Welcome page — strong full-bleed background image
      - vivid: slightly softer than hero
      - balanced: wizard steps — readable with softer image
    """
    if intensity == "hero":
        path = welcome_background_path() or background_image_path(template_name)
    else:
        path = background_image_path(template_name)
    if not path:
        return ""

    uri = _data_uri(path)
    family = background_family_for_template(template_name)
    if intensity == "hero":
        # Soft page backdrop: image visible at top, content area stays bright/readable.
        bg_layers = (
            "linear-gradient(180deg, "
            "rgba(234, 241, 245, 0.55) 0%, "
            "rgba(234, 241, 245, 0.88) 34%, "
            "rgba(234, 241, 245, 0.97) 100%), "
            f'url("{uri}")'
        )
    elif intensity == "vivid":
        veil = {
            "ats": "rgba(234, 241, 245, 0.55)",
            "corporate": "rgba(232, 238, 244, 0.58)",
            "modern": "rgba(245, 248, 250, 0.52)",
        }.get(family, "rgba(234, 241, 245, 0.55)")
        bg_layers = f"linear-gradient({veil}, {veil}), url(\"{uri}\")"
    else:
        veil = {
            "ats": "rgba(234, 241, 245, 0.78)",
            "corporate": "rgba(232, 238, 244, 0.80)",
            "modern": "rgba(245, 248, 250, 0.76)",
        }.get(family, "rgba(234, 241, 245, 0.78)")
        bg_layers = f"linear-gradient({veil}, {veil}), url(\"{uri}\")"

    welcome_hero_css = ""
    if intensity == "hero":
        welcome_hero_css = f"""
.cf-welcome-hero {{
  position: relative;
  isolation: isolate;
  min-height: clamp(200px, 32vh, 300px);
  margin: 0 0 1rem 0;
  border-radius: 1.1rem;
  overflow: hidden;
  border: 1px solid {accent_color}55;
  box-shadow: 0 16px 36px rgba(16, 42, 58, 0.16);
}}
.cf-welcome-hero::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image:
    linear-gradient(115deg, rgba(10, 47, 69, 0.82) 0%, rgba(14, 124, 134, 0.62) 55%, rgba(10, 47, 69, 0.55) 100%),
    url("{uri}");
  background-size: cover;
  background-position: center;
}}
.cf-welcome-hero-inner {{
  position: relative;
  z-index: 1;
  padding: clamp(1.35rem, 3.5vw, 2.2rem) clamp(1.1rem, 3vw, 2rem);
  color: #F7FBFC;
  text-align: center;
}}
.cf-welcome-hero-inner h1 {{
  margin: 0 0 0.35rem 0;
  font-size: clamp(2rem, 4.5vw, 3rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #FFFFFF !important;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.4);
}}
.cf-welcome-hero-inner h2 {{
  margin: 0 0 0.5rem 0;
  font-size: clamp(1.05rem, 2.2vw, 1.4rem);
  font-weight: 600;
  color: #F2FBFC !important;
}}
.cf-welcome-hero-inner p {{
  margin: 0;
  font-size: 0.95rem;
  color: #EAF6F8;
  max-width: 40rem;
  margin-inline: auto;
}}
.cf-welcome-content {{
  background: #FFFFFF !important;
  border: 1px solid {accent_color}40 !important;
  border-radius: 1rem;
  padding: 1rem 1.1rem 1.2rem;
  box-shadow: 0 12px 28px rgba(16, 42, 58, 0.10);
  position: relative;
  z-index: 5;
}}
.cf-welcome-selected {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  margin: 0 0 0.85rem 0;
  padding: 0.7rem 1rem;
  border-radius: 0.85rem;
  background: #E6F7F5;
  border: 2px solid {accent_color};
  color: #0A2F45;
  font-weight: 700;
}}
.cf-welcome-selected span {{
  color: {accent_color};
  font-weight: 800;
}}
"""

    panel_bg = "#FFFFFF" if intensity == "hero" else "rgba(255, 255, 255, 0.96)"

    return f"""
<style>
/* Background image layer — always behind UI content */
[data-testid="stAppViewContainer"],
.stApp {{
  background-image: {bg_layers} !important;
  background-size: cover !important;
  background-position: center top !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
  background-color: #EAF1F5 !important;
}}

section.main > div {{
  background: transparent !important;
}}

[data-testid="stHeader"] {{
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(10px);
}}

/* Foreground content stays clear and non-overlapping */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"],
[data-testid="stForm"],
div[data-testid="stMetric"],
div[data-baseweb="tab-panel"] {{
  background: {panel_bg} !important;
  border-color: {accent_color}44 !important;
  box-shadow: 0 10px 28px rgba(16, 42, 58, 0.10);
  position: relative;
  z-index: 3;
  color: #102A3A !important;
}}

/* Keep text dark/readable over any residual backdrop */
.block-container p,
.block-container span,
.block-container label,
.block-container [data-testid="stMarkdownContainer"],
.block-container [data-testid="stCaptionContainer"] {{
  color: #102A3A !important;
}}

section[data-testid="stSidebar"] {{
  background: rgba(10, 47, 69, 0.96) !important;
  position: relative;
  z-index: 4;
}}

.block-container {{
  position: relative;
  z-index: 2;
}}

.block-container h1,
.block-container h2,
.block-container h3 {{
  position: relative;
  z-index: 3;
  color: #0A2F45 !important;
}}

div[class^="lay-"],
div[class*=" resume-sheet"] {{
  background: #ffffff !important;
  position: relative;
  z-index: 4;
}}

.cf-atmosphere-strip {{
  height: 6px;
  width: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, {accent_color}, transparent 85%);
  margin: 0 0 0.85rem 0;
  opacity: 0.9;
}}
.cf-main-hero-panel {{
  background: #FFFFFF;
  border: 1px solid {accent_color}33;
  border-radius: 1rem;
  padding: 1.1rem 1.25rem 1.25rem;
  box-shadow: 0 12px 30px rgba(16, 42, 58, 0.10);
  position: relative;
  z-index: 3;
}}
.cf-atmosphere-caption {{
  font-size: 0.82rem;
  color: #5A7585;
  margin: 0 0 0.75rem 0;
}}
.cf-template-selected-badge {{
  display: inline-block;
  margin: 0 0 0.45rem 0;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  background: {accent_color};
  color: #FFFFFF !important;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.cf-template-selected-badge) {{
  border: 2px solid {accent_color} !important;
  background: #F3FBFA !important;
  box-shadow: 0 0 0 3px {accent_color}33, 0 12px 28px rgba(16, 42, 58, 0.12) !important;
}}
{welcome_hero_css}
</style>
"""


def atmosphere_meta(template_name: str) -> dict[str, Any]:
    family = background_family_for_template(template_name)
    labels = {
        "ats": "ATS soft backdrop",
        "corporate": "Corporate soft backdrop",
        "modern": "Modern soft backdrop",
        "welcome": "CareerForge hero backdrop",
    }
    path = background_image_path(template_name)
    return {
        "family": family,
        "label": labels.get(family, "Soft backdrop"),
        "path": path,
        "welcome_path": welcome_background_path(),
    }
