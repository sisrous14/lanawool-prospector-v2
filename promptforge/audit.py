"""Auditul unui prompt existent.

Îi dai un prompt scris de tine sau găsit undeva și îți spune ce îi lipsește
față de structura completă, cu un scor și cu ce ar trebui adăugat.

Verificarea e locală și se bazează pe cuvinte-cheie: nu poate judeca dacă un
prompt e *bun*, doar dacă are părțile care de obicei lipsesc. Un scor mare nu
garantează calitatea, dar unul mic arată aproape sigur o problemă.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assembly import count_words
from .vocab import normalize


@dataclass
class Check:
    """Un element pe care un prompt complet ar trebui să îl aibă."""

    key: str
    label: str
    hint: str
    keywords: tuple[str, ...]
    weight: int = 1


_TEXT_CHECKS: tuple[Check, ...] = (
    Check("role", "Rol sau expertiză",
          "Spune-i modelului cine este: „ești un inginer software senior…”.",
          ("esti un", "esti o", "you are a", "you are an", "act as", "rol:", "role:")),
    Check("goal", "Obiectiv explicit",
          "Spune ce trebuie să iasă, nu doar despre ce e vorba.",
          ("obiectiv", "scop", "objective", "goal", "produci", "produce", "livrezi", "deliver")),
    Check("audience", "Audiență",
          "Pentru cine e rezultatul? De asta depinde tot nivelul de detaliu.",
          ("audienta", "cititor", "pentru cine", "audience", "reader", "for a")),
    Check("format", "Format de ieșire",
          "Descrie forma concretă: secțiuni, lungime, tip de bloc.",
          ("format", "structura", "sectiuni", "structure", "sections", "output"), 2),
    Check("constraints", "Constrângeri și interdicții",
          "Ce NU trebuie să facă e la fel de important ca ce trebuie.",
          ("nu ", "fara ", "evita", "do not", "don't", "avoid", "never"), 2),
    Check("quality", "Criterii de calitate",
          "Dă-i o listă după care să se autoverifice înainte să răspundă.",
          ("criterii", "verifica", "calitate", "criteria", "check", "quality")),
    Check("examples", "Exemple sau referințe",
          "Un exemplu de bun și unul de slab valorează cât zece adjective.",
          ("exemplu", "de exemplu", "example", "for instance", "such as")),
    Check("specifics", "Detalii concrete",
          "Fără cifre, nume sau context specific, promptul se potrivește oricui.",
          ("cifr", "numar", "exact", "specific", "concret", "number", "precise")),
)

_IMAGE_CHECKS: tuple[Check, ...] = (
    Check("subject", "Subiect clar",
          "Descrie subiectul principal în detaliu, nu într-un cuvânt.",
          ("subject", "subiect", "portrait", "a man", "a woman", "product", "scene"), 2),
    Check("composition", "Compoziție și încadrare",
          "Spune unde stă subiectul în cadru și cum e încadrat.",
          ("composition", "framing", "rule of thirds", "centred", "centered",
           "close-up", "wide shot", "compozitie")),
    Check("camera", "Cameră și obiectiv",
          "Unghi, tip de cadru, focală și diafragmă schimbă complet rezultatul.",
          ("mm", "f/", "lens", "camera", "angle", "shot", "aperture", "obiectiv"), 2),
    Check("lighting", "Lumină",
          "Direcția și calitatea luminii sunt cel mai puternic control pe care îl ai.",
          ("light", "lighting", "backlit", "softbox", "golden hour", "shadow", "lumina"), 2),
    Check("colour", "Culoare și atmosferă",
          "O paletă numită dă un rezultat mult mai consecvent.",
          ("colour", "color", "palette", "tone", "mood", "paleta", "atmosfera")),
    Check("style", "Stil sau mediu",
          "Fotografie, ilustrație, randare 3D? Fără asta, modelul alege singur.",
          ("style", "photography", "illustration", "render", "painting", "film", "stil")),
    Check("detail", "Textură și nivel de detaliu",
          "Spune cât de detaliat vrei și unde anume.",
          ("detail", "texture", "sharp", "grain", "detaliu", "textura")),
    Check("technical", "Cerințe tehnice",
          "Rezoluție, raport de aspect, parametri specifici modelului.",
          ("resolution", "8k", "aspect", "--ar", "ratio", "rezolutie")),
    Check("negative", "Ce trebuie evitat",
          "Un prompt negativ sau o reformulare pozitivă a interdicțiilor.",
          ("negative", "avoid", "no ", "without", "fara", "evita")),
)


@dataclass
class AuditResult:
    """Ce lipsește dintr-un prompt și cât de complet e."""

    mode: str
    word_count: int
    score: int              # 0-100
    present: list[str]
    missing: list[tuple[str, str]]   # (etichetă, sugestie)
    notes: list[str]

    @property
    def verdict(self) -> str:
        if self.score >= 80:
            return "complet"
        if self.score >= 55:
            return "utilizabil, dar are goluri"
        return "incomplet"


def audit(prompt: str, mode: str = "text") -> AuditResult:
    """Verifică ce părți standard îi lipsesc unui prompt."""
    if not prompt.strip():
        raise ValueError("Nu am ce audita: promptul e gol.")

    checks = _IMAGE_CHECKS if mode in ("image", "video") else _TEXT_CHECKS
    haystack = normalize(prompt)

    present: list[str] = []
    missing: list[tuple[str, str]] = []
    earned = 0
    total = sum(check.weight for check in checks)

    for check in checks:
        if any(normalize(keyword) in haystack for keyword in check.keywords):
            present.append(check.label)
            earned += check.weight
        else:
            missing.append((check.label, check.hint))

    words = count_words(prompt)
    notes: list[str] = []
    if words < 60:
        notes.append(
            f"Doar {words} de cuvinte. Prompturile scurte lasă modelul să aleagă "
            f"în locul tău exact acolo unde ai fi vrut să decizi tu."
        )
    elif words > 1200:
        notes.append(
            f"{words} de cuvinte. Peste circa 1000, instrucțiunile de la mijloc "
            f"încep să fie urmate mai slab."
        )
    if mode == "text" and "?" in prompt and prompt.count("?") > 3:
        notes.append(
            "Multe semne de întrebare. Un prompt care întreabă în loc să ceară "
            "primește de obicei un răspuns evaziv."
        )

    score = round(100 * earned / total) if total else 0
    return AuditResult(
        mode=mode,
        word_count=words,
        score=score,
        present=present,
        missing=missing,
        notes=notes,
    )
