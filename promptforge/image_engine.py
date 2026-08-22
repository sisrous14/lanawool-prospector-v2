"""Generatorul de prompturi pentru modele de imagine.

Vocabularul vizual este în engleză indiferent de limba interfeței: modelele de
imagine sunt antrenate pe termeni englezești de optică, iluminare și peliculă,
iar traducerea lor degradează vizibil rezultatul.
"""

from __future__ import annotations

import re

from .assembly import count_words, fit, range_note, render_section, sentence
from .detect import Picker, detect_domain
from .models import Brief, GeneratedPrompt, MODE_IMAGE, Section
from .targets import IMAGE_TARGETS, default_image_target
from .vocab import ASPECT_BY_DOMAIN, COMMON_IMAGE, IMAGE_DOMAINS, normalize

# Cuvinte româneşti frecvente, pentru a semnala că subiectul nu e în engleză.
_RO_MARKERS = {
    "un", "o", "cu", "in", "pe", "care", "si", "de", "la", "pentru", "din",
    "langa", "sub", "peste", "intr", "catre", "fara", "este", "sunt",
}

def looks_romanian(text: str) -> bool:
    """Euristică simplă: diacritice sau cuvinte de legătură româneşti."""
    if re.search(r"[ăâîșşțţ]", text, flags=re.IGNORECASE):
        return True
    words = set(normalize(text).split())
    return len(words & _RO_MARKERS) >= 2


def _positive_from_negatives(extra_avoid: list[str]) -> str:
    """Reformulează interdicțiile pentru modelele fără prompt negativ.

    DALL·E și Imagen nu au prompt negativ și tind să deseneze exact ce li se
    cere să evite, așa că interdicțiile devin cerințe pozitive.
    """
    guard = (
        "Technical requirements stated positively: anatomy and hands must be correct and complete, "
        "focus sharp on the subject, background clean and uncluttered, colour balance natural rather "
        "than oversaturated, surfaces textured rather than plastic, and the frame entirely free of "
        "text, watermarks, signatures or logos."
    )
    if extra_avoid:
        guard += " Keep the frame free of " + ", ".join(extra_avoid) + "."
    return guard


def build_sections(brief: Brief, domain: str, picker: Picker) -> tuple[list[Section], list[Section], list[str]]:
    """Construiește blocurile promptului vizual, rezerva și lista de negative."""
    data = IMAGE_DOMAINS.get(domain, IMAGE_DOMAINS["general"])
    subject = (brief.subject or brief.idea).strip().rstrip(".")

    environment = picker.one(list(data["environment"]))          # type: ignore[arg-type]
    camera = picker.one(list(data["camera"]))                    # type: ignore[arg-type]
    lens = picker.one(list(data["lens"]))                        # type: ignore[arg-type]
    lighting = picker.one(list(data["lighting"]))                # type: ignore[arg-type]
    style = brief.style or picker.one(list(data["style"]))       # type: ignore[arg-type]
    composition = picker.one(COMMON_IMAGE["composition"])
    palette = picker.one(COMMON_IMAGE["palette"])
    mood = picker.one(COMMON_IMAGE["mood"])
    detail = picker.one(COMMON_IMAGE["detail"])
    quality = picker.one(COMMON_IMAGE["quality"])
    extras: list[str] = list(data.get("extra", []))              # type: ignore[arg-type]

    # Interdicțiile utilizatorului stau primele: Midjourney păstrează doar
    # începutul listei, iar ce a cerut el explicit nu are voie să cadă.
    negatives = (
        list(brief.avoid)
        + list(COMMON_IMAGE["negative"])
        + list(data.get("negative", []))  # type: ignore[arg-type]
    )

    sections: list[Section] = [
        Section(
            "SUBJECT",
            [
                f"{sentence(subject)} This is the single focal point of the image and every other choice "
                f"below exists to serve it. Render it prominently, unambiguously and in full — no part of "
                f"the main subject is cropped away or hidden behind other elements."
            ],
            priority=1,
        ),
        Section(
            "SETTING",
            [f"{sentence('placed in ' + environment)} The environment supports the subject and never "
             f"competes with it for attention; secondary elements stay subordinate in contrast and detail."],
            priority=1,
        ),
        Section(
            "COMPOSITION",
            [f"{sentence(composition)} The frame is balanced and intentional, with a clear reading order "
             f"from the primary subject outward."],
            priority=1,
        ),
        Section(
            "CAMERA",
            [f"{sentence(camera + ', shot on ' + lens)} Perspective is natural and undistorted, with the "
             f"plane of focus falling exactly on the subject."],
            priority=1,
        ),
        Section(
            "LIGHTING",
            [f"{sentence(lighting)} A single coherent light direction governs the whole frame; highlights "
             f"are shaped rather than blown out and shadows retain detail."],
            priority=1,
        ),
        Section(
            "COLOUR AND MOOD",
            [f"{sentence(palette)} The overall mood is {mood}, carried by the light and the colour "
             f"relationships rather than by added effects."],
            priority=2,
        ),
        Section(
            "STYLE",
            [f"{sentence(style)} The stylistic treatment stays consistent across the entire image, with "
             f"no mixing of incompatible rendering approaches."],
            priority=2,
        ),
        Section(
            "DETAIL",
            [" ".join(sentence(part) for part in ([detail] + extras[:1]))],
            priority=2,
            droppable=True,
        ),
        Section(
            "TECHNICAL",
            [sentence(quality)],
            priority=2,
            droppable=True,
            min_lines=0,
        ),
    ]

    if brief.must:
        sections.append(
            Section(
                "MUST INCLUDE",
                [f"The image must also contain, clearly visible: {'; '.join(brief.must)}."],
                priority=1,
            )
        )

    reserve: list[Section] = []
    if len(extras) > 1:
        reserve.append(
            Section("ADDITIONAL DIRECTION", [sentence(extras[1])], priority=3,
                    droppable=True, min_lines=0)
        )
    reserve.append(
        Section(
            "COHERENCE",
            [
                "Every element in the frame is physically plausible: scale relationships hold, shadows "
                "fall consistently with the stated light direction, reflections match their sources, and "
                "materials behave the way real materials behave under this light."
            ],
            priority=3,
            droppable=True,
            min_lines=0,
        )
    )
    reserve.append(
        Section(
            "FOCUS DISCIPLINE",
            [
                "If any instruction above conflicts with another, resolve it in favour of the subject "
                "description: a clear, correct, well-lit subject matters more than any stylistic flourish."
            ],
            priority=3,
            droppable=True,
            min_lines=0,
        )
    )

    return sections, reserve, negatives


def _to_prose(sections: list[Section]) -> str:
    """Transformă blocurile într-un paragraf continuu (Midjourney, DALL·E)."""
    parts: list[str] = []
    for section in sections:
        for line in section.lines:
            parts.append(line.strip())
    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează promptul de imagine pentru un brief."""
    domain = brief.domain or detect_domain(brief.idea, MODE_IMAGE)
    if domain not in IMAGE_DOMAINS:
        raise ValueError(
            f"Domeniu vizual necunoscut: {domain!r}. Disponibile: {', '.join(sorted(IMAGE_DOMAINS))}"
        )
    target = brief.target or default_image_target()
    if target not in IMAGE_TARGETS:
        raise ValueError(
            f"Țintă necunoscută: {target!r}. Disponibile: {', '.join(sorted(IMAGE_TARGETS))}"
        )

    spec = IMAGE_TARGETS[target]
    picker = Picker(brief.seed + variant * 1000)
    sections, reserve, negatives = build_sections(brief, domain, picker)

    aspect = brief.aspect or ASPECT_BY_DOMAIN.get(domain, "16:9")
    notes = list(spec.get("notes", []))

    # Interdicțiile, tratate după cum le suportă modelul-țintă.
    negative_prompt = ""
    positive_rewrite = ""
    if spec["negative"] == "prompt":
        negative_prompt = ", ".join(dict.fromkeys(negatives))
    elif spec["negative"] == "none":
        positive_rewrite = _positive_from_negatives(brief.avoid)
        sections.append(Section("QUALITY GUARDS", [positive_rewrite], priority=2, droppable=True))

    if spec["layout"] == "prose":
        renderer = _to_prose
    else:
        def renderer(secs: list[Section]) -> str:
            return "\n\n".join(render_section(s, "") for s in secs if s.lines)

    _, prompt = fit(sections, brief.min_words, brief.max_words, reserve, renderer=renderer)

    parameters = spec["params"].format(aspect=aspect) if spec["params"] else ""
    if spec["negative"] == "param":
        short_negatives = list(dict.fromkeys(negatives))[:10]
        parameters = (parameters + " --no " + ", ".join(short_negatives)).strip()

    word_count = count_words(prompt)
    warning = range_note(word_count, brief.min_words, brief.max_words)
    if warning:
        notes.insert(0, warning)

    if brief.subject is None and looks_romanian(brief.idea):
        notes.insert(
            0,
            "Subiectul a rămas în română. Modelele de imagine lucrează mult mai bine în engleză: "
            "rulează cu --refine pentru traducere sau folosește --subject pentru a da subiectul în engleză.",
        )

    return GeneratedPrompt(
        prompt=prompt,
        mode=MODE_IMAGE,
        domain=domain,
        target=target,
        word_count=word_count,
        variant=variant,
        negative_prompt=negative_prompt,
        parameters=parameters,
        notes=notes,
    )
