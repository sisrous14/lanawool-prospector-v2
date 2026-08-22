"""Rafinare opțională a promptului printr-un model Claude.

Motorul local funcționează fără rețea și fără dependențe. Când există
credențiale Anthropic și se cere `--refine`, promptul generat local este
trimis unui model Claude, care îl rescrie: adaptează formulările la ideea
concretă, traduce subiectele vizuale în engleză și elimină pasajele generice.

Fără pachetul `anthropic` instalat sau fără credențiale, funcția întoarce
promptul local nemodificat și explică de ce.
"""

from __future__ import annotations

import re

from .models import Brief, GeneratedPrompt, MODE_IMAGE

DEFAULT_MODEL = "claude-opus-5"

_SYSTEM = """\
Ești un inginer de prompturi. Primești o idee brută și un prompt-schelet generat automat, \
și îl rescrii într-un prompt final, de calitate profesională.

Reguli:
- Păstrează structura și secțiunile scheletului; îmbunătățește conținutul lor.
- Înlocuiește orice formulare generică cu una specifică ideii primite. Dacă o propoziție \
s-ar potrivi la fel de bine altei idei, rescrie-o.
- Nu inventa cerințe pe care ideea nu le implică și nu adăuga fapte, cifre sau denumiri.
- Respectă limita de cuvinte cerută. Numără înainte de a răspunde.
- Pentru prompturile de imagine, scrie întotdeauna în engleză, indiferent de limba ideii, \
și tradu subiectul cu termeni vizuali potriviți, nu cuvânt cu cuvânt.
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


class RefineUnavailable(RuntimeError):
    """Rafinarea nu poate rula (lipsă pachet, credențiale sau rețea)."""


def _parse(raw: str) -> tuple[str, str, str]:
    def block(name: str) -> str:
        match = re.search(
            rf"<<<{name}>>>\s*(.*?)(?=\n<<<|\Z)", raw, flags=re.DOTALL
        )
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
    effort: str = "high",
) -> GeneratedPrompt:
    """Rescrie promptul cu ajutorul unui model Claude.

    Ridică `RefineUnavailable` dacă SDK-ul lipsește sau nu există credențiale;
    apelantul decide dacă asta e o eroare sau doar un motiv de avertisment.
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depinde de mediu
        raise RefineUnavailable(
            "Pachetul `anthropic` nu este instalat. Rulează: pip install anthropic"
        ) from exc

    try:
        client = anthropic.Anthropic()
    except Exception as exc:  # pragma: no cover - depinde de mediu
        raise RefineUnavailable(
            f"Nu am putut construi clientul Anthropic: {exc}. "
            "Setează ANTHROPIC_API_KEY sau autentifică-te cu `ant auth login`."
        ) from exc

    message = _TEMPLATE.format(
        mode=generated.mode,
        target=generated.target,
        domain=generated.domain,
        lang="engleză" if generated.mode == MODE_IMAGE else brief.lang,
        min_words=brief.min_words,
        max_words=brief.max_words,
        idea=brief.idea,
        draft=generated.full_text(),
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=16000,
            system=_SYSTEM,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=[{"role": "user", "content": message}],
        )
    except anthropic.AuthenticationError as exc:
        raise RefineUnavailable(
            "Credențiale Anthropic invalide sau lipsă (ANTHROPIC_API_KEY)."
        ) from exc
    except anthropic.NotFoundError as exc:
        raise RefineUnavailable(
            f"Modelul {model!r} nu este disponibil pentru acest cont. "
            "Alege altul cu --model."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise RefineUnavailable("Limită de rată atinsă; încearcă din nou peste puțin.") from exc
    except anthropic.APIStatusError as exc:
        raise RefineUnavailable(f"Eroare API ({exc.status_code}): {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise RefineUnavailable(f"Eroare de rețea: {exc}") from exc

    if response.stop_reason == "refusal":
        raise RefineUnavailable("Modelul a refuzat cererea de rafinare.")

    raw = "".join(block.text for block in response.content if block.type == "text")
    prompt, negative, params = _parse(raw)

    from .assembly import count_words

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
        refined_by=response.model,
    )
