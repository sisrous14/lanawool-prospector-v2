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
from .catalog import PLATFORMS, aspect_of, describe_size
from .depth import image_depth, platform_section
from . import feedback, judgment
from .detect import Picker, detect_domain
from .models import Brief, GeneratedPrompt, MODE_IMAGE, Section
from .targets import IMAGE_TARGETS, default_image_target
from .translate import IMAGE_LABELS, IMAGE_PHRASES, lookup_romanian, to_english
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
    """Decide dacă textul e în română.

    Trei semnale, în ordinea siguranței: diacriticele, cuvintele de legătură
    româneşti, și cât din text recunoaște lexiconul vizual. Al treilea prinde
    fraze scurte ca „un pescar batran”, unde primele două nu sunt de ajuns.
    """
    if re.search(r"[ăâîșşțţ]", text, flags=re.IGNORECASE):
        return True

    words = normalize(text).split()
    if len(set(words) & _RO_MARKERS) >= 2:
        return True

    content = [word for word in words if len(word) > 2]
    if len(content) < 2:
        return False
    known = sum(1 for word in content if lookup_romanian(word) is not None)
    return known >= 2 and known / len(content) >= 0.5


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


def _more(options: list[str], used: str, picker: Picker, count: int = 4) -> list[str]:
    """Descriptori suplimentari din același vocabular, fără să-l repete pe cel folosit.

    Servesc drept extensii: apar doar când bugetul de cuvinte e mare, și atunci
    îmbogățesc blocul în loc să-l repete.
    """
    pool = [option for option in options if option != used]
    return [sentence(option) for option in picker.some(pool, count)]


def build_sections(
    brief: Brief, domain: str, picker: Picker
) -> tuple[list[Section], list[Section], list[str], list[str], dict[str, str]]:
    """Construiește blocurile, rezerva, negativele, observațiile și câmpurile alese."""
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
            expansions=_more(list(data["environment"]), environment, picker),  # type: ignore[arg-type]
        ),
        Section(
            _label("COMPOSITION", lang),
            [f"{sentence(composition)} {p['composition_tail']}"],
            priority=1,
            expansions=_more(COMMON_IMAGE["composition"], composition, picker),
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
            expansions=_more(list(data["lighting"]), lighting, picker),  # type: ignore[arg-type]
        ),
        Section(
            _label("COLOUR AND MOOD", lang),
            [f"{sentence(palette)} {p['mood_head']} {mood}, {p['mood_tail']}"],
            priority=2,
            expansions=_more(COMMON_IMAGE["palette"], palette, picker),
        ),
        Section(_label("STYLE", lang), [f"{sentence(style)} {p['style_tail']}"], priority=2,
                expansions=_more(list(data["style"]), style, picker)),  # type: ignore[arg-type]
        Section(
            _label("DETAIL", lang),
            [" ".join(sentence(part) for part in ([detail] + extras[:1]))],
            priority=2,
            droppable=True,
            expansions=_more(COMMON_IMAGE["detail"], detail, picker) + [
                sentence(item) for item in extras[1:3]
            ],
        ),
        Section(_label("TECHNICAL", lang), [sentence(quality)], priority=2,
                droppable=True, min_lines=0),
    ]

    if brief.platform:
        rules = platform_section(brief.platform, "image", lang)
        if rules is not None:
            sections.append(rules)

    if brief.width and brief.height:
        sections.append(
            Section(
                _label("OUTPUT SPECIFICATION", lang),
                [
                    f"Final output at {describe_size(brief.width, brief.height)}. "
                    f"Compose for this exact frame: the subject must sit correctly inside "
                    f"{aspect_of(brief.width, brief.height)} without needing a crop, and fine "
                    f"detail must hold at this pixel size rather than at a larger one."
                ],
                priority=1,
            )
        )

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
    focus_lines = [p["focus"]]
    if not brief.strict:
        focus_lines.append(judgment.visual_line(lang))
    reserve.append(
        Section(_label("FOCUS DISCIPLINE", lang), focus_lines, priority=3,
                droppable=True, min_lines=0)
    )

    reserve.extend(image_depth(lang))

    chosen = {
        "environment": environment, "camera": camera, "lens": lens,
        "lighting": lighting, "style": style, "composition": composition,
        "palette": palette, "mood": mood, "detail": detail,
    }
    return sections, reserve, negatives, notes, chosen


def _to_prose(sections: list[Section]) -> str:
    """Transformă blocurile într-un paragraf continuu.

    Fiecare rând devine o propoziție de sine stătătoare: fără etichete care să
    le separe, un rând fără punct final s-ar lipi de următorul.
    """
    parts: list[str] = []
    for section in sections:
        if section.lead:
            parts.append(sentence(section.lead))
        parts.extend(sentence(line) for line in section.lines if line.strip())
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
    liked, disliked = feedback.preferences()
    picker = Picker(brief.seed + variant * 1000, liked, disliked)
    sections, reserve, negatives, notes, chosen = build_sections(brief, domain, picker)

    # Aspectul, în ordinea autorității: ce a cerut explicit utilizatorul, apoi
    # dimensiunea în pixeli pe care a dat-o, apoi formatul platformei, apoi ce a
    # observat analiza în poza-sursă, apoi obiceiul domeniului.
    if brief.aspect:
        aspect = brief.aspect
    elif brief.width and brief.height:
        aspect = aspect_of(brief.width, brief.height)
    elif brief.platform and PLATFORMS[brief.platform].aspect:
        aspect = PLATFORMS[brief.platform].aspect
    else:
        aspect = brief.overrides.get("aspect") or ASPECT_BY_DOMAIN.get(domain, "16:9")

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
    if word_count > 1200:
        notes.append(
            "Prompt lung. Peste circa 1000 de cuvinte, modelele urmăresc tot mai slab "
            "instrucțiunile de la mijloc; câștigul scade, iar riscul de contradicții "
            "crește. Folosește lungimea asta când chiar ai de spus atât."
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
        used_descriptors=picker.chosen,
        chosen_fields=chosen,
    )
