"""Generatorul de prompturi SEO.

Diferența față de un prompt de text obișnuit: aici conținutul tău e sursa
adevărului. Cuvintele-cheie sunt extrase din el, statisticile sunt măsurate pe
el, iar limitele de caractere sunt cele reale ale platformei — nu aproximări.
"""

from __future__ import annotations

from .assembly import count_words, fit, range_note
from .catalog import known_fields
from .depth import text_depth
from . import judgment
from .models import Brief, GeneratedPrompt, MODE_SEO, Section
from .seo import (
    CONTENT_TYPES,
    DEFAULT_INTENT,
    DEFAULT_TYPE,
    INTENTS,
    analyse,
    keywords,
)
from .targets import TEXT_TARGETS, default_text_target
from .text_engine import render_sections

MAX_SOURCE_CHARS = 2500

_TITLES = {
    "role": {"ro": "ROL", "en": "ROLE"},
    "source": {"ro": "CONȚINUTUL SURSĂ", "en": "SOURCE CONTENT"},
    "keywords": {"ro": "CUVINTE-CHEIE", "en": "KEYWORDS"},
    "intent": {"ro": "INTENȚIA DE CĂUTARE", "en": "SEARCH INTENT"},
    "deliverables": {"ro": "LIVRABILE", "en": "DELIVERABLES"},
    "limits": {"ro": "LIMITE DE CARACTERE", "en": "CHARACTER LIMITS"},
    "rules": {"ro": "REGULI DE OPTIMIZARE", "en": "OPTIMISATION RULES"},
    "avoid": {"ro": "DE EVITAT", "en": "AVOID"},
    "format": {"ro": "FORMAT DE IEȘIRE", "en": "OUTPUT FORMAT"},
    "check": {"ro": "VERIFICARE FINALĂ", "en": "FINAL CHECK"},
    "judgment": {"ro": "JUDECATĂ PROPRIE", "en": "YOUR OWN JUDGMENT"},
}

_RULES = {
    "ro": [
        "Cuvântul-cheie principal apare în title tag, în H1, în primele 100 de cuvinte "
        "și în cel puțin un H2 — de fiecare dată într-o formulare care sună natural citită cu voce tare.",
        "Folosește variante semantice și sinonime, nu repetarea aceluiași cuvânt. "
        "Motoarele înțeleg legătura dintre termeni; cititorul observă repetiția.",
        "Fiecare titlu H2 răspunde unei întrebări pe care cineva chiar ar scrie-o în căutare.",
        "Primul paragraf conține deja răspunsul, nu promisiunea lui. Cine pleacă după 10 secunde "
        "trebuie să plece cu informația.",
        "Scrie pentru cineva care compară trei pagini deschise în paralel: dă-i motivul să rămână "
        "pe a ta în primele două rânduri.",
        "Fiecare afirmație verificabilă are o cifră, un exemplu sau o sursă. Textul fără dovezi "
        "nu se distinge de cele o mie de pagini identice pe același subiect.",
    ],
    "en": [
        "The primary keyword appears in the title tag, the H1, the first 100 words and at least "
        "one H2 — each time phrased so it sounds natural read aloud.",
        "Use semantic variants and synonyms rather than repeating the same word. Engines understand "
        "the relationship between terms; the reader notices the repetition.",
        "Every H2 answers a question someone would actually type into a search box.",
        "The first paragraph already contains the answer, not the promise of it. Whoever leaves after "
        "ten seconds must leave with the information.",
        "Write for someone comparing three open tabs: give them a reason to stay on yours within two lines.",
        "Every checkable claim carries a number, an example or a source. Text without evidence is "
        "indistinguishable from the thousand identical pages on the same subject.",
    ],
}

_AVOID = {
    "ro": [
        "repetarea cuvântului-cheie peste densitatea la care textul mai sună omenesc",
        "text alternativ umplut cu cuvinte-cheie în loc de descriere a imaginii",
        "meta description identică pe mai multe pagini",
        "titluri care promit altceva decât livrează pagina",
        "paragrafe introductive care explică despre ce va fi vorba, în loc să înceapă",
        "conținut subțire întins cu perifraze ca să atingă un număr de cuvinte",
        "liste de orașe sau de servicii generate mecanic, fără text propriu",
    ],
    "en": [
        "repeating the keyword past the density at which the text still sounds human",
        "alt text stuffed with keywords instead of describing the image",
        "the same meta description on more than one page",
        "headlines promising something the page does not deliver",
        "introductory paragraphs explaining what the text will be about instead of starting",
        "thin content padded with circumlocution to reach a word count",
        "mechanically generated lists of cities or services with no writing of their own",
    ],
}


# Etichetele XML pentru ținta Claude, indexate pe titlul afișat.
_TAGS = {
    "role": "rol", "source": "sursa", "keywords": "cuvinte_cheie",
    "intent": "intentie", "deliverables": "livrabile", "limits": "limite",
    "rules": "reguli", "avoid": "de_evitat", "format": "format",
    "check": "verificare", "judgment": "judecata",
}


def _title(key: str, lang: str) -> str:
    return _TITLES[key][lang]


def _tag_map(lang: str) -> dict[str, str]:
    """Titlu afișat -> etichetă XML, pentru randarea către Claude."""
    return {_TITLES[key][lang]: tag for key, tag in _TAGS.items()}


def build_sections(brief: Brief) -> tuple[list[Section], list[Section], list[str]]:
    """Secțiunile promptului SEO, rezerva și observațiile."""
    lang = brief.lang
    notes: list[str] = []

    content_type = brief.domain or DEFAULT_TYPE
    spec = CONTENT_TYPES[content_type]
    intent_key = brief.intent or DEFAULT_INTENT
    source = brief.source_text.strip()

    primary, secondary = keywords(source or brief.idea)
    if brief.keyword:
        primary = brief.keyword
        secondary = [word for word in secondary if word != primary]
    elif primary:
        notes.append(
            f"Cuvântul-cheie principal a fost extras din conținut: „{primary}”. "
            f"Impune altul cu --keyword dacă nu e cel pe care îl vizezi."
        )

    stats = analyse(source) if source else None
    sections: list[Section] = []

    # --- ROL ---------------------------------------------------------------
    label = spec["label"][lang]  # type: ignore[index]
    if lang == "ro":
        role = (
            f"Ești specialist SEO și copywriter, într-o singură persoană. Ai scris destule pagini "
            f"cât să știi că un text care se poziționează bine și unul care se citește bine sunt "
            f"același text, nu două. Lucrezi la: {label}. Livrezi conținut gata de publicat, "
            f"nu recomandări despre ce ar trebui făcut."
        )
    else:
        role = (
            f"You are an SEO specialist and a copywriter in one person. You have written enough pages "
            f"to know that text which ranks well and text which reads well are the same text, not two. "
            f"You are working on: {label}. You deliver publish-ready content, not recommendations "
            f"about what should be done."
        )
    sections.append(Section(_title("role", lang), [role], priority=1))

    # --- CONȚINUTUL SURSĂ ---------------------------------------------------
    if source:
        excerpt = source[:MAX_SOURCE_CHARS]
        truncated = len(source) > MAX_SOURCE_CHARS
        lines = [
            "Optimizezi conținutul de mai jos. Este sursa adevărului: nu contrazice faptele din el "
            "și nu adăuga informații pe care nu le conține."
            if lang == "ro" else
            "You are optimising the content below. It is the source of truth: do not contradict the "
            "facts in it and do not add information it does not contain.",
            "",
            excerpt + ("…" if truncated else ""),
        ]
        if stats:
            lines.append("")
            lines.append(stats.describe(lang))
        if truncated:
            notes.append(
                f"Sursa a fost scurtată la {MAX_SOURCE_CHARS} de caractere în prompt; "
                f"restul nu ar fi încăput fără să sufere celelalte secțiuni."
            )
        sections.append(Section(_title("source", lang), lines, priority=1))
    else:
        subject = brief.idea
        sections.append(Section(
            _title("source", lang),
            [
                f"Nu ai primit un text sursă. Scrii de la zero despre: „{subject}”."
                if lang == "ro" else
                f'No source text was provided. You are writing from scratch about: "{subject}".'
            ],
            priority=1,
        ))

    # --- CUVINTE-CHEIE ------------------------------------------------------
    keyword_lines = []
    if primary:
        keyword_lines.append(
            f"Cuvânt-cheie principal: „{primary}”." if lang == "ro"
            else f'Primary keyword: "{primary}".'
        )
    if secondary:
        joined = ", ".join(f"„{word}”" if lang == "ro" else f'"{word}"' for word in secondary)
        keyword_lines.append(
            f"Variante secundare, de folosit acolo unde intră firesc: {joined}."
            if lang == "ro" else
            f"Secondary variants, to use where they fit naturally: {joined}."
        )
    keyword_lines.append(
        "Nu forța niciunul. Un cuvânt-cheie care strică propoziția face mai mult rău decât "
        "absența lui din acea propoziție."
        if lang == "ro" else
        "Force none of them. A keyword that breaks the sentence does more harm than its absence "
        "from that sentence."
    )
    if stats and stats.questions:
        keyword_lines.append(
            ("Întrebări deja prezente în sursă, bune ca titluri H2: " if lang == "ro"
             else "Questions already present in the source, good as H2 headings: ")
            + " ".join(stats.questions[:3])
        )
    sections.append(Section(_title("keywords", lang), keyword_lines, priority=1))

    # --- INTENȚIE -----------------------------------------------------------
    sections.append(Section(
        _title("intent", lang),
        [
            (f"Intenția de căutare este {INTENTS[intent_key][lang]}"
             if lang == "ro" else
             f"The search intent is {INTENTS[intent_key][lang]}")
        ],
        priority=1,
    ))

    # --- LIVRABILE ----------------------------------------------------------
    deliverables: list[str] = list(spec["deliverables"][lang])  # type: ignore[index]
    sections.append(Section(
        _title("deliverables", lang), deliverables, priority=1, bullet="1.",
        droppable=True, min_lines=4,
        lead=("Livrezi, în ordinea asta, fiecare element complet:" if lang == "ro"
              else "You deliver each of these in full, in this order:"),
    ))

    # --- LIMITE DE CARACTERE ------------------------------------------------
    platform = brief.platform or "google"
    limits = known_fields(platform)
    if limits:
        limit_lines = []
        for key, limit in limits.items():
            recommended = (
                (f", recomandat sub {limit.recommended}" if lang == "ro"
                 else f", recommended under {limit.recommended}")
                if limit.recommended else ""
            )
            limit_lines.append(f"{limit.label}: maximum {limit.maximum} de caractere{recommended}. {limit.note}")
        limit_lines.append(
            "Numără caracterele, nu le estima. Un titlu de 32 de caractere într-un câmp de 30 "
            "nu se scurtează la afișare — e respins."
            if lang == "ro" else
            "Count the characters, do not estimate them. A 32-character title in a 30-character field "
            "is not shortened on display — it is rejected."
        )
        sections.append(Section(
            _title("limits", lang), limit_lines, priority=1, bullet="-",
            droppable=True, min_lines=2,
        ))

    # --- REGULI -------------------------------------------------------------
    sections.append(Section(
        _title("rules", lang), _RULES[lang][:3], priority=1, bullet="-",
        droppable=True, min_lines=2, expansions=_RULES[lang][3:],
    ))

    # --- DE EVITAT ----------------------------------------------------------
    avoid_lines = list(brief.avoid) + _AVOID[lang][:3]
    sections.append(Section(
        _title("avoid", lang), avoid_lines, priority=2, bullet="-",
        droppable=True, min_lines=2, expansions=_AVOID[lang][3:],
    ))

    if brief.must:
        sections.append(Section(
            _title("deliverables", lang) + (" — CERINȚE SUPLIMENTARE" if lang == "ro" else " — EXTRA"),
            list(brief.must), priority=1, bullet="-",
        ))

    if not brief.strict:
        sections.append(judgment.text_section(lang))

    # --- FORMAT -------------------------------------------------------------
    sections.append(Section(
        _title("format", lang),
        [
            "Fiecare livrabil sub eticheta lui, cu majuscule, pe rând separat, urmat de conținut. "
            "La title tag, meta description și alt text pune numărul de caractere în paranteză, "
            "la finalul rândului. Începe direct cu primul livrabil."
            if lang == "ro" else
            "Each deliverable under its own upper-case label on a separate line, followed by the content. "
            "For the title tag, meta description and alt text, put the character count in brackets at the "
            "end of the line. Start directly with the first deliverable."
        ],
        priority=1,
    ))

    # --- VERIFICARE ---------------------------------------------------------
    reserve = [Section(
        _title("check", lang),
        [
            "Numără caracterele fiecărui câmp limitat și corectează ce depășește."
            if lang == "ro" else
            "Count the characters of every limited field and fix whatever exceeds.",
            "Citește textul cu voce tare: unde te împiedici, acolo ai forțat un cuvânt-cheie."
            if lang == "ro" else
            "Read the text aloud: wherever you stumble is where you forced a keyword.",
            "Verifică dacă cineva care caută expresia principală ar găsi în text răspunsul complet."
            if lang == "ro" else
            "Check whether someone searching the primary phrase would find the complete answer in the text.",
        ],
        priority=3, bullet="-", droppable=True, min_lines=0,
    )]
    reserve.extend(text_depth(lang))

    return sections, reserve, notes


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează promptul SEO."""
    content_type = brief.domain or DEFAULT_TYPE
    if content_type not in CONTENT_TYPES:
        raise ValueError(
            f"Tip de conținut necunoscut: {content_type!r}. "
            f"Disponibile: {', '.join(sorted(CONTENT_TYPES))}"
        )
    if brief.intent and brief.intent not in INTENTS:
        raise ValueError(
            f"Intenție necunoscută: {brief.intent!r}. Disponibile: {', '.join(sorted(INTENTS))}"
        )
    target = brief.target or default_text_target()
    if target not in TEXT_TARGETS:
        raise ValueError(
            f"Țintă necunoscută: {target!r}. Disponibile: {', '.join(sorted(TEXT_TARGETS))}"
        )

    sections, reserve, notes = build_sections(brief)
    style = TEXT_TARGETS[target]["style"]
    _, prompt = fit(
        sections, brief.min_words, brief.max_words, reserve,
        renderer=lambda secs: render_sections(secs, style, brief.lang, _tag_map(brief.lang)),
    )

    word_count = count_words(prompt)
    notes = notes + list(TEXT_TARGETS[target].get("notes", []))
    warning = range_note(word_count, brief.min_words, brief.max_words)
    if warning:
        notes.insert(0, warning)

    return GeneratedPrompt(
        prompt=prompt,
        mode=MODE_SEO,
        domain=content_type,
        target=target,
        word_count=word_count,
        variant=variant,
        notes=notes,
    )
