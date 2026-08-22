"""Generatorul de prompturi pentru modele de imagine.

Descriptorii vizuali (optică, iluminare, peliculă) rămân în engleză și în
varianta românească a promptului: așa sunt folosiți și de fotografii români,
iar modelele de imagine sunt antrenate pe ei. Ce se traduce sunt etichetele
blocurilor și frazele de legătură.

Câmpurile pot veni din trei surse, în ordinea priorității: analiza unei
imagini (`brief.overrides`), o opțiune dată explicit de utilizator, sau
alegerea deterministă din vocabular.
"""

from __future__ import annotations

import re

from .assembly import count_words, fit, range_note, render_section, sentence
from .detect import Picker, detect_domain
from .models import Brief, GeneratedPrompt, MODE_IMAGE, Section
from .targets import IMAGE_TARGETS, default_image_target
from .translate import IMAGE_LABELS, IMAGE_PHRASES, to_english
from .vocab import ASPECT_BY_DOMAIN, COMMON_IMAGE, IMAGE_DOMAINS, normalize

# Cuvinte româneşti frecvente, pentru a semnala că subiectul nu e în engleză.
_RO_MARKERS = {
    "un", "o", "cu", "in", "pe", "care", "si", "de", "la", "pentru", "din",
    "langa", "sub", "peste", "intr", "catre", "fara", "este", "sunt",
}

# Frazele de legătură în engleză; perechile românești sunt în `translate`.
EN_PHRASES: dict[str, str] = {
    "subject_tail": (
        "This is the single focal point of the image and every other choice below "
        "exists to serve it. Render it prominently, unambiguously and in full — no "
        "part of the main subject is cropped away or hidden behind other elements."
    ),
    "setting_head": "Placed in",
    "setting_tail": (
        "The environment supports the subject and never competes with it for "
        "attention; secondary elements stay subordinate in contrast and detail."
    ),
    "composition_tail": (
        "The frame is balanced and intentional, with a clear reading order from the "
        "primary subject outward."
    ),
    "camera_join": ", shot on",
    "camera_tail": (
        "Perspective is natural and undistorted, with the plane of focus falling "
        "exactly on the subject."
    ),
    "lighting_tail": (
        "A single coherent light direction governs the whole frame; highlights are "
        "shaped rather than blown out and shadows retain detail."
    ),
    "mood_head": "The overall mood is",
    "mood_tail": (
        "carried by the light and the colour relationships rather than by added effects."
    ),
    "style_tail": (
        "The stylistic treatment stays consistent across the entire image, with no "
        "mixing of incompatible rendering approaches."
    ),
    "must_head": "The image must also contain, clearly visible:",
    "coherence": (
        "Every element in the frame is physically plausible: scale relationships hold, "
        "shadows fall consistently with the stated light direction, reflections match "
        "their sources, and materials behave the way real materials behave under this light."
    ),
    "focus": (
        "If any instruction above conflicts with another, resolve it in favour of the "
        "subject description: a clear, correct, well-lit subject matters more than any "
        "stylistic flourish."
    ),
    "guards": (
        "Technical requirements stated positively: anatomy and hands must be correct and "
        "complete, focus sharp on the subject, background clean and uncluttered, colour "
        "balance natural rather than oversaturated, surfaces textured rather than plastic, "
        "and the frame entirely free of text, watermarks, signatures or logos."
    ),
    "guards_avoid": "Keep the frame free of",
}


def looks_romanian(text: str) -> bool:
    """Euristică simplă: diacritice sau cuvinte de legătură româneşti."""
    if re.search(r"[ăâîșşțţ]", text, flags=re.IGNORECASE):
        return True
    words = set(normalize(text).split())
    return len(words & _RO_MARKERS) >= 2


def _phrases(lang: str) -> dict[str, str]:
    return IMAGE_PHRASES if lang == "ro" else EN_PHRASES


def _label(name: str, lang: str) -> str:
    return IMAGE_LABELS.get(name, name) if lang == "ro" else name


def _resolve_subject(brief: Brief) -> tuple[str, list[str]]:
    """Alege subiectul și explică, dacă e cazul, ce s-a întâmplat cu el."""
    notes: list[str] = []

    override = brief.overrides.get("subject")
    if override:
        return override.strip().rstrip("."), notes

    if brief.subject:
        return brief.subject.strip().rstrip("."), notes

    subject = brief.idea.strip().rstrip(".")
    if brief.lang == "ro" or not looks_romanian(subject):
        return subject, notes

    # Prompt în engleză pornit de la o idee în română: traducem ce putem.
    translated, coverage = to_english(subject)
    if translated != subject:
        notes.append(
            f"Subiectul a fost tradus automat în engleză: „{subject}” → "
            f"„{translated}”. Traducerea e aproximativă ({coverage:.0%} din cuvinte "
            f"recunoscute); corecteaz-o cu --subject dacă a ratat ceva."
        )
        return translated, notes

    notes.append(
        "Subiectul a rămas în română: prea puține cuvinte recunoscute pentru o "
        "traducere sigură. Dă-l în engleză cu --subject, folosește --refine, sau "
        "generează promptul în română cu --lang ro."
    )
    return subject, notes


def _pick(brief: Brief, key: str, options: list[str], picker: Picker) -> str:
    """Suprascrierea din analiză bate alegerea din vocabular."""
    override = brief.overrides.get(key)
    if override:
        return override
    return picker.one(options)


def build_sections(
    brief: Brief, domain: str, picker: Picker
) -> tuple[list[Section], list[Section], list[str], list[str]]:
    """Construiește blocurile, rezerva, lista de negative și observațiile."""
    data = IMAGE_DOMAINS.get(domain, IMAGE_DOMAINS["general"])
    lang = brief.lang
    p = _phrases(lang)

    subject, notes = _resolve_subject(brief)

    environment = _pick(brief, "environment", list(data["environment"]), picker)  # type: ignore[arg-type]
    camera = _pick(brief, "camera", list(data["camera"]), picker)                # type: ignore[arg-type]
    lens = _pick(brief, "lens", list(data["lens"]), picker)                      # type: ignore[arg-type]
    lighting = _pick(brief, "lighting", list(data["lighting"]), picker)          # type: ignore[arg-type]
    style = brief.style or _pick(brief, "style", list(data["style"]), picker)    # type: ignore[arg-type]
    composition = _pick(brief, "composition", COMMON_IMAGE["composition"], picker)
    palette = _pick(brief, "palette", COMMON_IMAGE["palette"], picker)
    mood = _pick(brief, "mood", COMMON_IMAGE["mood"], picker)
    detail = _pick(brief, "detail", COMMON_IMAGE["detail"], picker)
    quality = picker.one(COMMON_IMAGE["quality"])

    extras: list[str] = list(data.get("extra", []))  # type: ignore[arg-type]
    if brief.overrides.get("extra"):
        extras = [brief.overrides["extra"]] + extras

    # Interdicțiile utilizatorului stau primele: Midjourney păstrează doar
    # începutul listei, iar ce a cerut el explicit nu are voie să cadă.
    negatives = (
        list(brief.avoid)
        + list(brief.extra_negatives)
        + list(COMMON_IMAGE["negative"])
        + list(data.get("negative", []))  # type: ignore[arg-type]
    )

    sections: list[Section] = [
        Section(_label("SUBJECT", lang), [f"{sentence(subject)} {p['subject_tail']}"], priority=1),
        Section(
            _label("SETTING", lang),
            [f"{sentence(p['setting_head'] + ' ' + environment)} {p['setting_tail']}"],
            priority=1,
        ),
        Section(
            _label("COMPOSITION", lang),
            [f"{sentence(composition)} {p['composition_tail']}"],
            priority=1,
        ),
        Section(
            _label("CAMERA", lang),
            [f"{sentence(camera + p['camera_join'] + ' ' + lens)} {p['camera_tail']}"],
            priority=1,
        ),
        Section(
            _label("LIGHTING", lang),
            [f"{sentence(lighting)} {p['lighting_tail']}"],
            priority=1,
        ),
        Section(
            _label("COLOUR AND MOOD", lang),
            [f"{sentence(palette)} {p['mood_head']} {mood}, {p['mood_tail']}"],
            priority=2,
        ),
        Section(_label("STYLE", lang), [f"{sentence(style)} {p['style_tail']}"], priority=2),
        Section(
            _label("DETAIL", lang),
            [" ".join(sentence(part) for part in ([detail] + extras[:1]))],
            priority=2,
            droppable=True,
        ),
        Section(_label("TECHNICAL", lang), [sentence(quality)], priority=2,
                droppable=True, min_lines=0),
    ]

    if brief.must:
        sections.append(
            Section(
                _label("MUST INCLUDE", lang),
                [f"{p['must_head']} {'; '.join(brief.must)}."],
                priority=1,
            )
        )

    reserve: list[Section] = []
    if len(extras) > 1:
        reserve.append(
            Section(_label("ADDITIONAL DIRECTION", lang), [sentence(extras[1])],
                    priority=3, droppable=True, min_lines=0)
        )
    reserve.append(
        Section(_label("COHERENCE", lang), [p["coherence"]], priority=3,
                droppable=True, min_lines=0)
    )
    reserve.append(
        Section(_label("FOCUS DISCIPLINE", lang), [p["focus"]], priority=3,
                droppable=True, min_lines=0)
    )

    return sections, reserve, negatives, notes


def _to_prose(sections: list[Section]) -> str:
    """Transformă blocurile într-un paragraf continuu (Midjourney, DALL·E)."""
    parts = [line.strip() for section in sections for line in section.lines]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează promptul de imagine pentru un brief."""
    domain = brief.domain or brief.overrides.get("domain") or detect_domain(brief.idea, MODE_IMAGE)
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
    sections, reserve, negatives, notes = build_sections(brief, domain, picker)

    aspect = brief.aspect or brief.overrides.get("aspect") or ASPECT_BY_DOMAIN.get(domain, "16:9")

    # Transferul între imagini descrie de unde vine fiecare element. Nu intră în
    # prompt: modelul-țintă primește doar text, iar „imaginea 1” nu înseamnă
    # nimic pentru el — elementele preluate sunt deja topite în descriere.
    if brief.transfer:
        notes.append(f"Combinare: {brief.transfer}")
        if target == "midjourney":
            notes.append(
                "La Midjourney poți atașa imaginea-sursă de stil cu --sref <adresă>, "
                "ca referința să fie și vizuală, nu doar descrisă."
            )

    if brief.lang == "ro":
        notes.append(
            "Prompt în română, bun pentru citit și editat. Descriptorii tehnici rămân "
            "în engleză intenționat. Când îl trimiți efectiv unui model de imagine, "
            "varianta engleză (fără --lang ro) dă rezultate mai bune."
        )

    notes = notes + list(spec.get("notes", []))
    p = _phrases(brief.lang)

    # Interdicțiile, tratate după cum le suportă modelul-țintă.
    negative_prompt = ""
    if spec["negative"] == "prompt":
        negative_prompt = ", ".join(dict.fromkeys(negatives))
    elif spec["negative"] == "none":
        guards = p["guards"]
        if brief.avoid:
            guards += f" {p['guards_avoid']} " + ", ".join(brief.avoid) + "."
        sections.append(
            Section(_label("QUALITY GUARDS", brief.lang), [guards], priority=2, droppable=True)
        )

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
