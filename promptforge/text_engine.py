"""Generatorul de prompturi pentru modele de text."""

from __future__ import annotations

import re

from .assembly import count_words, fit, range_note, render_section
from .depth import (
    EXTRA_AVOID,
    EXTRA_METHOD,
    EXTRA_MUST,
    EXTRA_QUALITY,
    platform_section,
    text_depth,
)
from . import feedback, judgment
from .detect import Picker, detect_domain, keywords_of
from .models import Brief, GeneratedPrompt, MODE_TEXT, Section
from .targets import TEXT_TARGETS, default_text_target
from .vocab import TEXT_DOMAINS, TONES

# Titlurile secțiunilor: cheie -> (titlu RO, titlu EN, etichetă XML pentru Claude)
LABELS: dict[str, tuple[str, str, str]] = {
    "role": ("ROL", "ROLE", "rol"),
    "context": ("CONTEXT ȘI OBIECTIV", "CONTEXT AND OBJECTIVE", "context"),
    "audience": ("AUDIENȚĂ", "AUDIENCE", "audienta"),
    "deliverable": ("LIVRABIL", "DELIVERABLE", "livrabil"),
    "must": ("CERINȚE OBLIGATORII", "MANDATORY REQUIREMENTS", "cerinte"),
    "method": ("METODĂ DE LUCRU", "METHOD", "metoda"),
    "tone": ("TON ȘI STIL", "TONE AND STYLE", "ton"),
    "quality": ("CRITERII DE CALITATE", "QUALITY CRITERIA", "calitate"),
    "format": ("FORMAT DE IEȘIRE", "OUTPUT FORMAT", "format"),
    "avoid": ("DE EVITAT", "AVOID", "de_evitat"),
    "check": ("VERIFICARE FINALĂ", "FINAL CHECK", "verificare"),
    "depth": ("NIVEL DE DETALIU", "LEVEL OF DETAIL", "detaliu"),
    "platform": ("REGULI DE PLATFORMĂ", "PLATFORM RULES", "platforma"),
    "judgment": ("JUDECATĂ PROPRIE", "YOUR OWN JUDGMENT", "judecata"),
}


def _title(key: str, lang: str) -> str:
    ro, en, _ = LABELS[key]
    return ro if lang == "ro" else en


def _tag(key: str) -> str:
    return LABELS[key][2]


def slugify(title: str) -> str:
    """Etichetă XML dintr-un titlu: „CRITERII DE ACCEPTANȚĂ” -> `criterii_de_acceptanta`.

    Folosită ca ultimă soluție, pentru secțiunile care nu au o etichetă proprie.
    Mai bine o etichetă care spune ceva decât un `<sectiune>` repetat de zece ori.
    """
    from .vocab import normalize

    cleaned = re.sub(r"[^a-z0-9]+", "_", normalize(title)).strip("_")
    return cleaned or "sectiune"


def _join_ro(items: list[str]) -> str:
    """Enumerare naturală: a, b și c."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " și " + items[-1]


def _join_en(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_sections(brief: Brief, domain: str, picker: Picker) -> tuple[list[Section], list[Section]]:
    """Construiește secțiunile obligatorii și rezerva de completare."""
    lang = brief.lang
    data = TEXT_DOMAINS.get(domain, TEXT_DOMAINS["general"])
    role = data["role"][lang]           # type: ignore[index]
    deliverable = data["deliverable"][lang]  # type: ignore[index]
    steps: list[str] = list(data["steps"][lang])      # type: ignore[index]
    quality: list[str] = list(data["quality"][lang])  # type: ignore[index]
    pitfalls: list[str] = list(data["pitfalls"][lang])  # type: ignore[index]
    fmt = data["format"][lang]          # type: ignore[index]

    keywords = keywords_of(brief.idea)
    join = _join_ro if lang == "ro" else _join_en
    audience = brief.audience or (
        "un cititor competent, dar care nu cunoaște contextul intern al proiectului"
        if lang == "ro"
        else "a competent reader who does not know the project's internal context"
    )
    # Tonul: fie o cheie din vocabular, fie o descriere liberă dată de utilizator.
    if brief.tone:
        tone = TONES.get(brief.tone, {}).get(lang, brief.tone)
    else:
        tone = TONES["profesional"][lang]

    sections: list[Section] = []

    # --- ROL ---------------------------------------------------------------
    if lang == "ro":
        role_text = (
            f"Ești un {role}. Lucrezi pentru cineva care va folosi rezultatul imediat, "
            f"așa că răspunsul tău trebuie să fie complet și utilizabil fără reveniri. "
            f"Nu ceri clarificări suplimentare: acolo unde cererea lasă loc de interpretare, "
            f"alegi varianta cea mai rezonabilă, o aplici și menționezi alegerea într-un rând."
        )
    else:
        role_text = (
            f"You are a {role}. You are working for someone who will use the result immediately, "
            f"so your answer must be complete and usable without a second round. "
            f"Do not ask clarifying questions: where the request leaves room for interpretation, "
            f"pick the most reasonable reading, apply it, and note the choice in one line."
        )
    sections.append(Section(_title("role", lang), [role_text], priority=1))

    # --- CONTEXT -----------------------------------------------------------
    if lang == "ro":
        context_lines = [
            f"Cererea, exact așa cum a fost formulată: „{brief.idea}”.",
            (
                "Obiectivul tău este să transformi această cerere într-un rezultat finit, nu într-un "
                "plan despre cum ar putea fi obținut. Consideră reușit rezultatul dacă cel care l-a "
                "cerut îl poate folosi în forma primită, fără să mai adauge nimic esențial."
            ),
        ]
        if keywords:
            context_lines.append(
                f"Elementele care dau specificul acestei cereri și care nu au voie să lipsească din "
                f"răspuns: {join(keywords)}."
            )
    else:
        context_lines = [
            f'The request, exactly as stated: "{brief.idea}".',
            (
                "Your objective is to turn this request into a finished result, not into a plan for how "
                "one might produce it. Treat the result as successful if the person who asked can use it "
                "as delivered, without adding anything essential."
            ),
        ]
        if keywords:
            context_lines.append(
                f"The elements that make this request specific, none of which may be missing from the "
                f"answer: {join(keywords)}."
            )
    sections.append(Section(_title("context", lang), context_lines, priority=1))

    # --- AUDIENȚĂ ----------------------------------------------------------
    if lang == "ro":
        audience_text = (
            f"Scrii pentru: {audience}. Calibrează vocabularul, exemplele și nivelul de detaliu "
            f"pentru acest cititor: explică termenii pe care el nu îi folosește zilnic și nu pierde "
            f"timp explicând ce știe deja."
        )
    else:
        audience_text = (
            f"You are writing for: {audience}. Calibrate vocabulary, examples and level of detail to "
            f"this reader: explain the terms they do not use daily and do not spend time explaining "
            f"what they already know."
        )
    sections.append(
        Section(_title("audience", lang), [audience_text], priority=3, droppable=True, min_lines=0)
    )

    # --- LIVRABIL ----------------------------------------------------------
    if lang == "ro":
        deliverable_text = (
            f"Produci {deliverable}. Livrezi direct conținutul cerut, fără preambul, fără să repeți "
            f"cererea și fără comentarii despre propriul proces de lucru."
        )
    else:
        deliverable_text = (
            f"You produce {deliverable}. Deliver the requested content directly, with no preamble, "
            f"without restating the request and without commentary on your own process."
        )
    sections.append(Section(_title("deliverable", lang), [deliverable_text], priority=1))

    # --- PLATFORMĂ ----------------------------------------------------------
    if brief.platform:
        rules = platform_section(brief.platform, "text", lang)
        if rules is not None:
            sections.append(rules)

    # --- CERINȚE OBLIGATORII ----------------------------------------------
    if lang == "ro":
        must_lines = [
            "Acoperă integral cererea. Dacă o parte din ea nu poate fi rezolvată corect, spune "
            "explicit care parte și de ce, în loc să o ocolești discret.",
            "Fii concret. Fiecare afirmație importantă vine cu motivul, exemplul sau cifra care o susține; "
            "recomandările includ pașii necesari pentru a fi puse în practică.",
            "Nu inventa fapte, cifre, surse, citate sau denumiri de produse. Când nu ești sigur, "
            "marchează afirmația drept estimare și spune ce ar confirma-o.",
        ]
    else:
        must_lines = [
            "Cover the request in full. If part of it cannot be solved correctly, say explicitly which "
            "part and why, rather than quietly working around it.",
            "Be concrete. Every significant claim comes with the reason, example or number behind it; "
            "recommendations include the steps needed to act on them.",
            "Do not invent facts, numbers, sources, quotes or product names. When unsure, flag the claim "
            "as an estimate and state what would confirm it.",
        ]
    # Cerințele scrise explicit de utilizator trec înaintea celor implicite:
    # la scurtare se taie de la coadă, iar ele nu au voie să dispară.
    must_lines = list(brief.must) + must_lines
    sections.append(
        Section(_title("must", lang), must_lines, priority=1, bullet="1.",
                droppable=True, min_lines=3, expansions=list(EXTRA_MUST[lang]))
    )

    # --- METODĂ ------------------------------------------------------------
    sections.append(
        Section(_title("method", lang), steps, priority=1, bullet="1.",
                droppable=True, min_lines=4, expansions=list(EXTRA_METHOD[lang]))
    )

    # --- TON ---------------------------------------------------------------
    if lang == "ro":
        tone_text = (
            f"Tonul este {tone}. Fraze scurte acolo unde ideea e simplă, fraze lungi doar când "
            f"ideea chiar are nevoie de ele. Fără clișee, fără entuziasm decorativ, fără formule "
            f"de umplutură care nu adaugă informație."
        )
    else:
        tone_text = (
            f"The tone is {tone}. Short sentences where the idea is simple, long ones only when the idea "
            f"genuinely needs them. No clichés, no decorative enthusiasm, no filler phrasing that adds "
            f"no information."
        )
    # Un ton cerut explicit e o instrucțiune, nu o preferință: nu se taie.
    sections.append(
        Section(
            _title("tone", lang), [tone_text],
            priority=2 if brief.tone else 3,
            droppable=not brief.tone,
            min_lines=1 if brief.tone else 0,
        )
    )

    # --- CALITATE ----------------------------------------------------------
    quality_lines = list(quality)
    if lang == "ro":
        quality_lines.append("un cititor exigent nu ar avea de pus nicio întrebare de clarificare")
        prefix = "Înainte de a livra, verifică fiecare punct:"
    else:
        quality_lines.append("a demanding reader would have no clarifying question left")
        prefix = "Before delivering, check every point:"
    sections.append(
        Section(_title("quality", lang), quality_lines, priority=2, bullet="-",
                droppable=True, min_lines=3, lead=prefix,
                expansions=list(EXTRA_QUALITY[lang]))
    )

    # --- JUDECATĂ PROPRIE ---------------------------------------------------
    if not brief.strict:
        sections.append(judgment.text_section(lang))

    # --- FORMAT ------------------------------------------------------------
    if lang == "ro":
        format_text = (
            f"{fmt} Începe direct cu conținutul. Nu adăuga note despre cum ai lucrat și nu încheia "
            f"cu întrebări de tipul «vrei să detaliez?»."
        )
    else:
        format_text = (
            f"{fmt} Start directly with the content. Do not add notes about how you worked and do not "
            f"end with questions such as `would you like me to expand?`."
        )
    sections.append(Section(_title("format", lang), [format_text], priority=1))

    # --- DE EVITAT ---------------------------------------------------------
    avoid_lines = list(brief.avoid) + list(pitfalls)
    if lang == "ro":
        avoid_lines.append("răspunsuri care ar putea fi date oricărei alte cereri asemănătoare")
    else:
        avoid_lines.append("answers that could be given to any other similar request")
    sections.append(
        Section(_title("avoid", lang), avoid_lines, priority=2, bullet="-",
                droppable=True, min_lines=2, expansions=list(EXTRA_AVOID[lang]))
    )

    # --- REZERVĂ (folosită doar dacă textul e sub minim) --------------------
    reserve: list[Section] = []
    if lang == "ro":
        reserve.append(
            Section(
                _title("depth", lang),
                [
                    "Detaliul contează mai mult decât lungimea: preferă un exemplu concret în locul a "
                    "trei propoziții generale. Dacă un punct poate fi ilustrat, ilustrează-l; dacă poate "
                    "fi cuantificat, cuantifică-l; dacă depinde de context, spune de ce context depinde.",
                ],
                priority=3,
                droppable=True,
                min_lines=0,
            )
        )
        reserve.append(
            Section(
                _title("check", lang),
                [
                    "Recitește rezultatul o dată, ca și cum l-ai primi de la altcineva, și taie orice "
                    "propoziție care nu adaugă informație nouă.",
                    "Verifică dacă ai răspuns cererii inițiale, nu unei variante mai comode a ei.",
                    "Asigură-te că nicio afirmație rămasă nu are nevoie de o sursă pe care nu o poți indica.",
                ],
                priority=3,
                bullet="-",
                droppable=True,
                min_lines=0,
            )
        )
    else:
        reserve.append(
            Section(
                _title("depth", lang),
                [
                    "Detail matters more than length: prefer one concrete example over three general "
                    "sentences. If a point can be illustrated, illustrate it; if it can be quantified, "
                    "quantify it; if it depends on context, say which context.",
                ],
                priority=3,
                droppable=True,
                min_lines=0,
            )
        )
        reserve.append(
            Section(
                _title("check", lang),
                [
                    "Reread the result once as if someone else had handed it to you, and cut any sentence "
                    "that adds no new information.",
                    "Check that you answered the original request rather than a more convenient version of it.",
                    "Make sure no remaining claim needs a source you cannot point to.",
                ],
                priority=3,
                bullet="-",
                droppable=True,
                min_lines=0,
            )
        )

    reserve.extend(text_depth(lang))
    return sections, reserve


def render_sections(
    sections: list[Section],
    style: str,
    lang: str,
    tags: dict[str, str] | None = None,
) -> str:
    """Redă secțiunile în stilul cerut de modelul-țintă.

    `tags` permite altui mod (SEO, de pildă) să-și dea propriile etichete XML,
    fiindcă secțiunile lui nu sunt cele din `LABELS`.
    """
    extra = tags or {}
    if style == "xml":
        blocks = []
        for section in sections:
            if not section.lines:
                continue
            key = next((k for k, v in LABELS.items() if _title(k, lang) == section.title), None)
            tag = _tag(key) if key else extra.get(section.title) or slugify(section.title)
            body = render_section(Section("", section.lines, bullet=section.bullet, lead=section.lead))
            blocks.append(f"<{tag}>\n{body}\n</{tag}>")
        return "\n\n".join(blocks)

    heading = "##" if style == "markdown" else ""
    if heading:
        return "\n\n".join(
            render_section(s, heading) for s in sections if s.lines
        )
    # stil simplu: titluri în majuscule, fără marcaje
    blocks = []
    for section in sections:
        if not section.lines:
            continue
        body = render_section(Section("", section.lines, bullet=section.bullet, lead=section.lead))
        blocks.append(f"{section.title}\n{body}")
    return "\n\n".join(blocks)


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează promptul de text pentru un brief."""
    domain = brief.domain or detect_domain(brief.idea, MODE_TEXT)
    if domain not in TEXT_DOMAINS:
        raise ValueError(
            f"Domeniu text necunoscut: {domain!r}. Disponibile: {', '.join(sorted(TEXT_DOMAINS))}"
        )
    target = brief.target or default_text_target()
    if target not in TEXT_TARGETS:
        raise ValueError(
            f"Țintă necunoscută: {target!r}. Disponibile: {', '.join(sorted(TEXT_TARGETS))}"
        )

    liked, disliked = feedback.preferences()
    picker = Picker(brief.seed + variant * 1000, liked, disliked)
    sections, reserve = build_sections(brief, domain, picker)

    style = TEXT_TARGETS[target]["style"]
    _, prompt = fit(
        sections,
        brief.min_words,
        brief.max_words,
        reserve,
        renderer=lambda secs: render_sections(secs, style, brief.lang),
    )

    word_count = count_words(prompt)
    notes = list(TEXT_TARGETS[target].get("notes", []))
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
        mode=MODE_TEXT,
        domain=domain,
        target=target,
        word_count=word_count,
        variant=variant,
        notes=notes,
        used_descriptors=picker.chosen,
    )


# Numele vechi, păstrat pentru codul care îl folosește deja.
_render = render_sections
