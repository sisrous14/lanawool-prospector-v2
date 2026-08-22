"""Rafinare opțională a promptului printr-un model Claude.

Motorul local funcționează fără rețea și fără dependențe. Când există
credențiale Anthropic și se cere `--refine`, promptul generat local este
trimis unui model Claude, care îl rescrie: adaptează formulările la ideea
concretă, traduce subiectele vizuale în engleză și elimină pasajele generice.

Fără pachetul `anthropic` sau fără credențiale, apelantul primește
`RefineUnavailable` și livrează promptul local nemodificat.
"""

from __future__ import annotations

import re

from .assembly import count_words
from .llm import DEFAULT_EFFORT, DEFAULT_MODEL, ModelUnavailable, Sender, resolve_sender
from .models import Brief, GeneratedPrompt, MODE_IMAGE

# Numele istoric al excepției, păstrat pentru codul care îl importă deja.
RefineUnavailable = ModelUnavailable

_SYSTEM = """\
Ești un inginer de prompturi. Primești o idee brută și un prompt-schelet generat automat, \
și îl rescrii într-un prompt final, de calitate profesională.

Reguli:
- Păstrează structura și secțiunile scheletului; îmbunătățește conținutul lor.
- Înlocuiește orice formulare generică cu una specifică ideii primite. Dacă o propoziție \
s-ar potrivi la fel de bine altei idei, rescrie-o.
- Nu inventa cerințe pe care ideea nu le implică și nu adăuga fapte, cifre sau denumiri.
- Respectă limita de cuvinte cerută. Numără înainte de a răspunde.
- Pentru prompturile de imagine cerute în engleză, scrie în engleză indiferent de limba \
ideii, și tradu subiectul cu termeni vizuali potriviți, nu cuvânt cu cuvânt.
- Răspunzi numai cu blocurile delimitate cerute, fără comentarii în afara lor.\
"""

_TEMPLATE = """\
MOD: {mode}
MODEL-ȚINTĂ: {target}
DOMENIU DETECTAT: {domain}
LIMBA PROMPTULUI FINAL: {lang}
LUNGIME CERUTĂ: între {min_words} și {max_words} de cuvinte pentru blocul PROMPT

IDEEA UTILIZATORULUI (sursa adevărului):
{idea}

SCHELETUL GENERAT AUTOMAT:
{draft}

Rescrie scheletul. Răspunde exact în forma următoare:

<<<PROMPT>>>
(promptul final, gata de copiat)
<<<NEGATIVE>>>
(prompt negativ, doar pentru imagine și doar dacă modelul-țintă îl suportă; altfel lasă gol)
<<<PARAMS>>>
(parametrii modelului-țintă, dacă există; altfel lasă gol)
"""


def _parse(raw: str) -> tuple[str, str, str]:
    def block(name: str) -> str:
        match = re.search(rf"<<<{name}>>>\s*(.*?)(?=\n<<<|\Z)", raw, flags=re.DOTALL)
        return match.group(1).strip() if match else ""

    prompt = block("PROMPT")
    if not prompt:
        # Modelul a răspuns fără delimitatori; folosim tot textul.
        prompt = raw.strip()
    return prompt, block("NEGATIVE"), block("PARAMS")


def refine(
    brief: Brief,
    generated: GeneratedPrompt,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    sender: Sender | None = None,
) -> GeneratedPrompt:
    """Rescrie promptul cu ajutorul unui model Claude.

    Ridică `RefineUnavailable` dacă SDK-ul lipsește sau nu există credențiale;
    apelantul decide dacă asta e o eroare sau doar un motiv de avertisment.
    """
    send = resolve_sender(sender)

    lang = "engleză" if generated.mode == MODE_IMAGE and brief.lang == "en" else brief.lang
    message = _TEMPLATE.format(
        mode=generated.mode,
        target=generated.target,
        domain=generated.domain,
        lang=lang,
        min_words=brief.min_words,
        max_words=brief.max_words,
        idea=brief.idea,
        draft=generated.full_text(),
    )

    raw = send(
        system=_SYSTEM,
        content=[{"type": "text", "text": message}],
        model=model,
        effort=effort,
    )
    prompt, negative, params = _parse(raw)

    return GeneratedPrompt(
        prompt=prompt,
        mode=generated.mode,
        domain=generated.domain,
        target=generated.target,
        word_count=count_words(prompt),
        variant=generated.variant,
        negative_prompt=negative or generated.negative_prompt,
        parameters=params or generated.parameters,
        notes=generated.notes,
        refined_by=model,
    )
