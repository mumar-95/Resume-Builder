"""Professional titles and related visual assets."""

from __future__ import annotations

from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

PROFESSIONAL_TITLES = [
    "Software Engineer",
    "Software Developer",
    "Java Developer",
    "Python Developer",
    "Full Stack Developer",
    "ETL Developer",
    "Informatica Developer",
    "Data Engineer",
    "Backend Developer",
    "Frontend Developer",
    "DevOps Engineer",
    "QA Engineer",
    "Other",
]

# Map title -> (image filename, alt text)
_PROFESSION_IMAGE_MAP = {
    "Software Engineer": ("profession_engineer.jpg", "Software engineer professional visual"),
    "Software Developer": ("profession_software.jpg", "Software developer professional visual"),
    "Java Developer": ("profession_software.jpg", "Java developer professional visual"),
    "Python Developer": ("profession_software.jpg", "Python developer professional visual"),
    "Full Stack Developer": ("profession_software.jpg", "Full stack developer professional visual"),
    "Backend Developer": ("profession_software.jpg", "Backend developer professional visual"),
    "Frontend Developer": ("profession_software.jpg", "Frontend developer professional visual"),
    "ETL Developer": ("profession_data.jpg", "ETL developer professional visual"),
    "Informatica Developer": ("profession_data.jpg", "Informatica developer professional visual"),
    "Data Engineer": ("profession_data.jpg", "Data engineer professional visual"),
    "DevOps Engineer": ("profession_engineer.jpg", "DevOps engineer professional visual"),
    "QA Engineer": ("profession_engineer.jpg", "QA engineer professional visual"),
    "Other": ("profession_engineer.jpg", "Professional technology career visual"),
}


def profession_image(title: str) -> tuple[Path | None, str]:
    filename, alt = _PROFESSION_IMAGE_MAP.get(
        title, _PROFESSION_IMAGE_MAP["Other"]
    )
    path = ASSETS / filename
    if path.exists():
        return path, alt
    # Graceful fallback to existing step image
    fallback = ASSETS / "step_personal.jpg"
    if fallback.exists():
        return fallback, alt
    return None, alt
