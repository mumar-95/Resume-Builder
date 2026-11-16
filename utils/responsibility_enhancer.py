"""Enhance user-provided responsibilities into ATS-friendly bullets without inventing facts."""

from __future__ import annotations

import re
from typing import Any

ACTION_VERBS = (
    "Developed",
    "Designed",
    "Implemented",
    "Optimized",
    "Automated",
    "Migrated",
    "Managed",
    "Troubleshot",
    "Configured",
    "Integrated",
    "Enhanced",
    "Maintained",
    "Supported",
    "Delivered",
    "Built",
    "Created",
    "Resolved",
    "Analyzed",
)

WEAK_STARTERS = (
    "i ",
    "me ",
    "my ",
    "we ",
    "worked on",
    "responsible for",
    "was involved",
    "helped with",
    "did ",
    "handling",
    "handle ",
)

# Past-tense / informal openings stripped when we prepend a professional verb.
LEADING_VERBS = re.compile(
    r"^(fixed|resolved|handled|performed|completed|created|built|build|"
    r"develop(?:ed)?|implement(?:ed)?|design(?:ed)?|support(?:ed)?|"
    r"manage(?:d)?|optimize(?:d)?|automat(?:e|ed)|migrat(?:e|ed)|"
    r"configur(?:e|ed)|integrat(?:e|ed)|enhanc(?:e|ed)|maintain(?:ed)?|"
    r"deliver(?:ed)?|analy[sz]e(?:d)?|troubleshoot(?:ed)?|wrote|made|did|"
    r"doing|working on|worked on|looking after|looked after|"
    r"taking care of|took care of|involved in|involved with)\s+",
    re.I,
)

FIRST_PERSON = re.compile(r"\b(i|me|my|mine|we|our|ours)\b", re.I)

# Synonym rings used only to vary wording — never invent new facts.
VERB_SYNONYMS: dict[str, tuple[str, ...]] = {
    "Developed": ("Developed", "Built", "Delivered", "Engineered", "Created"),
    "Built": ("Built", "Developed", "Delivered", "Created", "Implemented"),
    "Implemented": ("Implemented", "Delivered", "Executed", "Developed", "Configured"),
    "Designed": ("Designed", "Architected", "Modeled", "Structured", "Defined"),
    "Optimized": ("Optimized", "Tuned", "Improved", "Enhanced", "Refined"),
    "Automated": ("Automated", "Streamlined", "Scripted", "Orchestrated", "Accelerated"),
    "Migrated": ("Migrated", "Converted", "Transitioned", "Ported", "Modernized"),
    "Managed": ("Managed", "Coordinated", "Oversaw", "Administered", "Led"),
    "Troubleshot": ("Troubleshot", "Resolved", "Diagnosed", "Remediated", "Corrected"),
    "Configured": ("Configured", "Set up", "Provisioned", "Established", "Prepared"),
    "Integrated": ("Integrated", "Connected", "Linked", "Combined", "Unified"),
    "Enhanced": ("Enhanced", "Improved", "Refined", "Upgraded", "Strengthened"),
    "Maintained": ("Maintained", "Supported", "Sustained", "Preserved", "Upkept"),
    "Supported": ("Supported", "Assisted", "Enabled", "Serviced", "Backed"),
    "Delivered": ("Delivered", "Shipped", "Completed", "Produced", "Provided"),
    "Created": ("Created", "Built", "Developed", "Established", "Produced"),
    "Resolved": ("Resolved", "Fixed", "Cleared", "Addressed", "Troubleshot"),
    "Analyzed": ("Analyzed", "Assessed", "Evaluated", "Reviewed", "Examined"),
}


def enhance_responsibilities(
    raw_text: str,
    *,
    job_title: str = "",
    technologies: str = "",
    role_focus: str = "",
    feedback: str = "",
    existing_bullets: str = "",
    variant_index: int = 0,
) -> dict[str, Any]:
    """
    Convert raw user responsibilities into professional bullets.

    Never invents technologies, metrics, or achievements not present in the input.
    variant_index rotates phrasing so regenerate keeps changing until the user is happy.
    """
    style = _feedback_style(feedback)
    # Cycle style packs even when feedback is empty so each regenerate is different.
    style = {
        **style,
        "concise": style.get("concise") or (int(variant_index) % 4 == 1),
        "stronger_verbs": style.get("stronger_verbs") or (int(variant_index) % 4 == 2),
        "ats": style.get("ats") or (int(variant_index) % 4 == 3),
    }

    previous_text = (existing_bullets or "").strip()
    previous = _split_points(previous_text) if previous_text else _split_points(raw_text)

    # Prefer raw facts as the semantic source; fall back to current draft.
    source_raw = (raw_text or "").strip() or previous_text
    lines = _split_points(source_raw)
    if not lines:
        return {
            "bullets": [],
            "needs_clarification": True,
            "clarification_message": (
                "Please enter at least one day-to-day responsibility so it can be "
                "converted into a professional resume statement."
            ),
            "warnings": [],
            "changes": [],
        }

    tech_tokens = _tech_tokens(technologies)
    warnings: list[str] = []
    vague_count = 0
    bullets: list[str] = []

    # Try several variants so regenerate does not return identical text.
    chosen: list[str] = []
    for attempt in range(8):
        attempt_index = int(variant_index) + attempt
        attempt_style = {
            **style,
            "concise": style.get("concise") or (attempt_index % 4 == 1),
            "stronger_verbs": True if attempt_index % 4 in (0, 2, 3) else style.get("stronger_verbs"),
            "ats": style.get("ats") or (attempt_index % 4 == 3),
        }
        bullets = []
        vague_count = 0
        for line in lines:
            enhanced, vague = _enhance_one(
                line,
                job_title=job_title,
                tech_tokens=tech_tokens,
                role_focus=role_focus,
                style=attempt_style,
                variant_index=attempt_index,
            )
            if enhanced:
                enhanced = _apply_verb_variant(enhanced, attempt_index)
                if enhanced not in bullets:
                    bullets.append(enhanced)
            if vague:
                vague_count += 1

        if bullets and attempt_index % 2 == 1 and len(bullets) > 1:
            # Rotate order for visible variety without changing meaning.
            shift = attempt_index % len(bullets)
            bullets = bullets[shift:] + bullets[:shift]

        if not previous or "\n".join(bullets).lower() != "\n".join(previous).lower():
            chosen = bullets
            break
        chosen = bullets

    bullets = chosen
    needs_clarification = vague_count > 0 and len(bullets) < 2
    clarification = ""
    if needs_clarification:
        clarification = (
            "Some entries are too generic. Add specifics such as modules owned, "
            "technologies used, troubleshooting work, or outcomes you personally delivered."
        )
    elif vague_count:
        warnings.append(
            "A few points were generic. Consider adding module names, tools, or outcomes for stronger ATS impact."
        )

    changes = _diff_bullets(previous, bullets)
    if not changes and bullets:
        changes = [f"Variant {int(variant_index) + 1}: refreshed professional wording."]

    return {
        "bullets": bullets,
        "needs_clarification": needs_clarification,
        "clarification_message": clarification,
        "warnings": warnings,
        "changes": changes,
    }


def _apply_verb_variant(bullet: str, variant_index: int) -> str:
    text = bullet.strip()
    if not text:
        return text
    first = text.split(" ", 1)[0].rstrip(".,;:")
    ring = VERB_SYNONYMS.get(first)
    if not ring:
        # Try case-insensitive match against known verbs.
        for key, values in VERB_SYNONYMS.items():
            if first.lower() == key.lower():
                ring = values
                first = key
                break
    if not ring:
        return text
    replacement = ring[int(variant_index) % len(ring)]
    rest = text[len(text.split(" ", 1)[0]) :]
    return f"{replacement}{rest}"


def responsibilities_to_text(bullets: list[str]) -> str:
    return "\n".join(f"• {bullet}" for bullet in bullets if bullet.strip())


def _split_points(raw_text: str) -> list[str]:
    points: list[str] = []
    for raw in (raw_text or "").replace("\r", "").split("\n"):
        line = raw.strip(" •-\t*")
        if line:
            points.append(line)
    return points


def _tech_tokens(technologies: str) -> list[str]:
    tokens: list[str] = []
    for chunk in (technologies or "").replace(";", ",").split(","):
        item = chunk.strip()
        if item and item not in tokens:
            tokens.append(item)
    return tokens


def _feedback_style(feedback: str) -> dict[str, bool]:
    lower = (feedback or "").lower()
    return {
        "concise": any(
            token in lower
            for token in ("concise", "shorter", "brief", "tighten", "compact")
        ),
        "stronger_verbs": any(
            token in lower
            for token in ("stronger", "action verb", "action verbs", "powerful", "impact")
        ),
        "ats": any(
            token in lower for token in ("ats", "keyword", "keywords", "recruiter")
        ),
    }


def _diff_bullets(before: list[str], after: list[str]) -> list[str]:
    changes: list[str] = []
    before_norm = [b.rstrip(".") for b in before]
    after_norm = [a.rstrip(".") for a in after]
    for index, new in enumerate(after_norm):
        if index < len(before_norm):
            old = before_norm[index]
            if old != new:
                changes.append(f"Updated: “{_short(old)}” → “{_short(new)}”")
        else:
            changes.append(f"Added: “{_short(new)}”")
    if len(before_norm) > len(after_norm):
        for old in before_norm[len(after_norm) :]:
            changes.append(f"Removed: “{_short(old)}”")
    if not changes and before_norm and after_norm:
        changes.append("Wording refreshed with the same meaning.")
    return changes[:8]


def _short(text: str, limit: int = 72) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rsplit(" ", 1)[0] + "…"


def _enhance_one(
    line: str,
    *,
    job_title: str,
    tech_tokens: list[str],
    role_focus: str,
    style: dict[str, bool] | None = None,
    variant_index: int = 0,
) -> tuple[str, bool]:
    style = style or {}
    text = " ".join(line.split()).strip(" .")
    if not text:
        return "", True

    vague = _is_vague(text)
    cleaned = FIRST_PERSON.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .")
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    # Strip weak openings
    lower = cleaned.lower()
    for weak in WEAK_STARTERS:
        if lower.startswith(weak):
            cleaned = cleaned[len(weak) :].strip(" .")
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
            lower = cleaned.lower()
            break

    if not cleaned:
        return "", True

    # Always normalize leading verbs so regenerate can swap them cleanly.
    cleaned = LEADING_VERBS.sub("", cleaned).strip(" .")
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    cleaned = re.sub(
        r"^(" + "|".join(re.escape(v) for v in ACTION_VERBS) + r")\b\s+",
        "",
        cleaned,
        flags=re.I,
    ).strip(" .")
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    starts_with_verb = any(cleaned.startswith(verb) for verb in ACTION_VERBS)
    if not starts_with_verb or style.get("stronger_verbs") or int(variant_index) >= 0:
        verb = _pick_verb(cleaned, role_focus)
        ring = VERB_SYNONYMS.get(verb) or (verb,)
        verb = ring[int(variant_index) % len(ring)]
        cleaned = re.sub(
            r"^(Worked|Helped|Handled|Did|Assisted|Performed)\b\s+",
            "",
            cleaned,
            flags=re.I,
        ).strip(" .")
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        starts_with_verb = any(cleaned.startswith(v) for v in ACTION_VERBS)
        if not starts_with_verb:
            cleaned = LEADING_VERBS.sub("", cleaned).strip(" .")
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
            cleaned = _strip_redundant_after_verb(verb, cleaned)
            if cleaned and not cleaned.lower().startswith(verb.lower()):
                cleaned = f"{verb} {_join_verb_body(cleaned)}"
            elif not cleaned:
                cleaned = verb

    # Do not inject technologies the user did not mention in this responsibility.
    _ = (tech_tokens, job_title)

    cleaned = cleaned.rstrip(".")
    if not cleaned.endswith("."):
        cleaned += "."

    # Keep concise — tighter when feedback asks for it.
    limit = 140 if style.get("concise") else (180 if int(variant_index) % 4 == 1 else 220)
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 3].rsplit(" ", 1)[0].rstrip(",.;:") + "."

    if style.get("concise"):
        cleaned = re.sub(r"\b(in order to|as well as|the process of)\b", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        if cleaned and not cleaned.endswith("."):
            cleaned += "."

    return cleaned, vague


def _join_verb_body(body: str) -> str:
    """Keep proper nouns/tech casing; lowercase only plain sentence starts."""
    if not body:
        return body
    if body[:1].isupper() and (len(body) == 1 or body[1:2].islower() or body[1:2] in " -_/"):
        # Likely a proper noun or acronym start — keep as-is
        first_word = body.split(" ", 1)[0]
        if first_word.isupper() or (first_word[:1].isupper() and any(ch.isupper() for ch in first_word[1:])):
            return body
        if first_word.lower() in {
            "informatica",
            "python",
            "java",
            "sql",
            "etl",
            "aws",
            "azure",
            "spark",
            "hadoop",
            "tableau",
            "power",
            "selenium",
            "oracle",
            "mysql",
            "postgres",
            "postgresql",
            "mongodb",
            "kafka",
            "docker",
            "kubernetes",
        }:
            return body
    return body[0].lower() + body[1:]


def _strip_redundant_after_verb(verb: str, body: str) -> str:
    if not body:
        return body
    if verb == "Supported":
        # Keep "production" when stripping "production support and ..."
        updated = re.sub(
            r"^production\s+support(\s+and)?\s*",
            "production ",
            body,
            flags=re.I,
        )
        updated = re.sub(r"^support(ing)?\s+(for\s+)?", "", updated, flags=re.I)
    else:
        patterns = {
            "Managed": r"^(management|managing)\s+(of\s+)?",
            "Troubleshot": r"^(troubleshooting|troubleshoot(ing)?)\s+(of\s+)?",
            "Optimized": r"^(optimization|optimizing)\s+(of\s+)?",
            "Automated": r"^(automation|automating)\s+(of\s+)?",
            "Migrated": r"^(migration|migrating)\s+(of\s+)?",
        }
        pattern = patterns.get(verb)
        if not pattern:
            return body
        updated = re.sub(pattern, "", body, flags=re.I)
    updated = updated.strip(" .")
    if updated:
        return updated[0].upper() + updated[1:]
    return updated


def _is_vague(text: str) -> bool:
    words = text.split()
    if len(words) < 4:
        return True
    vague_phrases = (
        "worked on project",
        "did development",
        "handled tasks",
        "various tasks",
        "daily work",
        "as required",
        "etc",
    )
    lower = text.lower()
    return any(phrase in lower for phrase in vague_phrases)


def _pick_verb(text: str, role_focus: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ("fix", "issue", "error", "fail", "bug", "defect")):
        return "Troubleshot"
    if any(token in lower for token in ("test", "qa", "selenium")):
        return "Implemented"
    if any(token in lower for token in ("support", "monitor", "incident", "on-call", "prod")):
        return "Supported"
    if any(token in lower for token in ("deploy", "release")):
        return "Managed"
    if any(token in lower for token in ("migrat", "upgrade")):
        return "Migrated"
    if any(token in lower for token in ("automat", "script", "pipeline")):
        return "Automated"
    if any(token in lower for token in ("optim", "performance", "improv", "reduc", "tun")):
        return "Optimized"
    if any(token in lower for token in ("design", "architect")):
        return "Designed"
    if any(token in lower for token in ("mapping", "mapplet", "workflow", "etl", "informatica")):
        return "Developed"
    if "Testing" in (role_focus or "") and "test" in lower:
        return "Implemented"
    return "Developed"
