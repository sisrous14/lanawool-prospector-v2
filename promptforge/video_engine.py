"""Generatorul de prompturi pentru modele video.

Un clip nu este o imagine în mișcare. Are durată, ritm, o mișcare de cameră
care trebuie spusă explicit, fizică plauzibilă între cadre și, la modelele
noi, sunet. Blocurile de aici acoperă exact ce nu are un prompt de imagine.
"""

from __future__ import annotations

import re

from .assembly import count_words, fit, range_note, render_section, sentence
from .catalog import PLATFORMS, aspect_of
from .depth import image_depth, platform_section
from . import feedback, judgment
from .detect import Picker, detect_domain
from .models import Brief, GeneratedPrompt, MODE_VIDEO, Section
from .targets import VIDEO_TARGETS, default_video_target
from .translate import to_english
from .vocab import ASPECT_BY_VIDEO_DOMAIN, COMMON_VIDEO, VIDEO_DOMAINS

DEFAULT_DURATION = 8

_LABELS_RO = {
    "SUBJECT AND ACTION": "SUBIECT ȘI ACȚIUNE",
    "SHOT": "CADRU",
    "CAMERA MOVEMENT": "MIȘCAREA CAMEREI",
    "PACING": "RITM",
    "LIGHTING AND LOOK": "LUMINĂ ȘI ASPECT",
    "MOTION PHYSICS": "FIZICA MIȘCĂRII",
    "AUDIO": "SUNET",
    "OPENING AND ENDING": "ÎNCEPUT ȘI FINAL",
    "TECHNICAL": "CERINȚE TEHNICE",
    "QUALITY GUARDS": "GARANȚII DE CALITATE",
    "MUST INCLUDE": "TREBUIE SĂ CONȚINĂ",
}

_GUARDS = (
    "Stated positively: faces and bodies stay consistent from the first frame to the last, "
    "geometry holds while the camera moves, lighting continuity is maintained across the whole "
    "clip, motion is smooth and physically plausible, and the frame stays free of text, "
    "watermarks and logos."
)


def _label(name: str, lang: str) -> str:
    return _LABELS_RO.get(name, name) if lang == "ro" else name


def build_sections(
    brief: Brief, domain: str, picker: Picker, duration: int
) -> tuple[list[Section], list[Section], list[str], list[str], dict[str, str]]:
    """Blocurile video, rezerva, negativele, observațiile și câmpurile alese."""
    data = VIDEO_DOMAINS.get(domain, VIDEO_DOMAINS["general"])
    lang = brief.lang
    notes: list[str] = []

    subject = (brief.subject or brief.overrides.get("subject") or brief.idea).strip().rstrip(".")
    if brief.subject is None and not brief.overrides.get("subject") and lang == "en":
        translated, coverage = to_english(subject)
        if translated != subject:
            notes.append(
                f"Subiectul a fost tradus automat în engleză: „{subject}” → „{translated}” "
                f"({coverage:.0%} din cuvinte recunoscute)."
            )
            subject = translated

    shot = brief.overrides.get("camera") or picker.one(list(data["shot"]))       # type: ignore[arg-type]
    beat = picker.one(list(data["beat"]))                                        # type: ignore[arg-type]
    movement = picker.one(COMMON_VIDEO["camera_move"])
    pacing = picker.one(COMMON_VIDEO["pacing"])
    physics = picker.one(COMMON_VIDEO["physics"])
    audio = picker.one(COMMON_VIDEO["audio"])
    transition = picker.one(COMMON_VIDEO["transition"])
    look = brief.style or picker.one(COMMON_VIDEO["look"])

    negatives = list(brief.avoid) + list(brief.extra_negatives) + list(COMMON_VIDEO["negative"])

    sections: list[Section] = [
        Section(
            _label("SUBJECT AND ACTION", lang),
            [
                f"{sentence(subject)} The action is continuous and readable for the full "
                f"{duration} seconds: one thing happens, and it finishes inside the shot."
            ],
            priority=1,
        ),
        Section(_label("SHOT", lang), [f"{sentence(shot)} {sentence(beat)}"], priority=1,
                expansions=[sentence(item) for item in data["shot"] if item != shot]),  # type: ignore[union-attr]
        Section(
            _label("CAMERA MOVEMENT", lang),
            [
                f"{sentence(movement)} The movement is motivated by the action, starts and stops "
                f"smoothly, and never changes direction mid-shot."
            ],
            priority=1,
            expansions=[sentence(m) for m in picker.some(
                [m for m in COMMON_VIDEO["camera_move"] if m != movement], 3)],
        ),
        Section(
            _label("PACING", lang),
            [f"{sentence(pacing)} Total duration {duration} seconds."],
            priority=1,
            expansions=[sentence(p) for p in COMMON_VIDEO["pacing"] if p != pacing],
        ),
        Section(
            _label("LIGHTING AND LOOK", lang),
            [
                f"{sentence(look)} Lighting direction and colour temperature stay identical from "
                f"the first frame to the last; no flicker, no drift in exposure."
            ],
            priority=1,
            expansions=[sentence(item) for item in COMMON_VIDEO["look"] if item != look],
        ),
        Section(
            _label("MOTION PHYSICS", lang),
            [sentence(physics)],
            priority=2,
            droppable=True,
            expansions=[sentence(item) for item in COMMON_VIDEO["physics"] if item != physics],
        ),
        Section(
            _label("AUDIO", lang),
            [sentence(audio)],
            priority=2,
            droppable=True,
            min_lines=0,
            expansions=[sentence(item) for item in COMMON_VIDEO["audio"] if item != audio],
        ),
        Section(
            _label("OPENING AND ENDING", lang),
            [sentence(transition)] + ([] if brief.strict else [judgment.visual_line(lang)]),
            priority=2,
            droppable=True,
            expansions=[sentence(item) for item in COMMON_VIDEO["transition"] if item != transition],
        ),
    ]

    if brief.platform:
        rules = platform_section(brief.platform, "video", lang)
        if rules is not None:
            sections.insert(1, rules)

    if brief.must:
        sections.append(
            Section(
                _label("MUST INCLUDE", lang),
                [f"The clip must also show, clearly: {'; '.join(brief.must)}."],
                priority=1,
            )
        )

    # Adâncimea vizuală se aplică și clipului: compoziție, materiale, lumină,
    # atmosferă sunt aceleași probleme, doar că trebuie să rămână stabile în timp.
    reserve = image_depth(lang)
    chosen = {
        "camera": shot, "movement": movement, "pacing": pacing,
        "style": look, "audio": audio, "physics": physics,
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
    """Generează promptul video pentru un brief."""
    domain = brief.domain or brief.overrides.get("domain") or detect_domain(brief.idea, MODE_VIDEO)
    if domain not in VIDEO_DOMAINS:
        raise ValueError(
            f"Domeniu video necunoscut: {domain!r}. "
            f"Disponibile: {', '.join(sorted(VIDEO_DOMAINS))}"
        )
    target = brief.target or default_video_target()
    if target not in VIDEO_TARGETS:
        raise ValueError(
            f"Țintă video necunoscută: {target!r}. "
            f"Disponibile: {', '.join(sorted(VIDEO_TARGETS))}"
        )

    spec = VIDEO_TARGETS[target]
    duration = brief.duration or DEFAULT_DURATION
    liked, disliked = feedback.preferences()
    picker = Picker(brief.seed + variant * 1000, liked, disliked)
    sections, reserve, negatives, notes, chosen = build_sections(brief, domain, picker, duration)

    if brief.aspect:
        aspect = brief.aspect
    elif brief.width and brief.height:
        aspect = aspect_of(brief.width, brief.height)
    elif brief.platform and PLATFORMS[brief.platform].aspect:
        aspect = PLATFORMS[brief.platform].aspect
    else:
        aspect = ASPECT_BY_VIDEO_DOMAIN.get(domain, "16:9")

    notes = notes + list(spec.get("notes", []))

    negative_prompt = ""
    if spec["negative"] == "prompt":
        negative_prompt = ", ".join(dict.fromkeys(negatives))
    else:
        guards = _GUARDS
        if brief.avoid:
            guards += " Keep the clip free of " + ", ".join(brief.avoid) + "."
        sections.append(
            Section(_label("QUALITY GUARDS", brief.lang), [guards], priority=2, droppable=True)
        )

    if spec["layout"] == "prose":
        renderer = _to_prose
    else:
        def renderer(secs: list[Section]) -> str:
            return "\n\n".join(render_section(s, "") for s in secs if s.lines)

    _, prompt = fit(sections, brief.min_words, brief.max_words, reserve, renderer=renderer)

    parameters = spec["params"].format(aspect=aspect, duration=duration)
    word_count = count_words(prompt)
    warning = range_note(word_count, brief.min_words, brief.max_words)
    if warning:
        notes.insert(0, warning)

    return GeneratedPrompt(
        prompt=prompt,
        mode=MODE_VIDEO,
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
