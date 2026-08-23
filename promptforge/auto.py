"""Modul automat: programul decide singur ce e mai bine pentru cererea ta.

`promptforge auto "..."` — sau, mai simplu, `promptforge "..."` — se uită la ce
ai scris și alege modul, domeniul, modelul-țintă, platforma, formatul, lungimea
și numărul de variante. Apoi spune ce a ales și de ce, ca să poți contrazice.

Deciziile sunt luate din semnalele din text, nu ghicite: cuvintele care indică
un clip, o platformă, o intenție de căutare, o cerință de detaliu. Orice opțiune
pe care o dai explicit rămâne a ta — automatul completează doar ce lipsește.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .catalog import PLATFORMS
from .detect import detect_domain
from .models import (
    DEFAULT_MAX_WORDS,
    DEFAULT_MIN_WORDS,
    MODE_IMAGE,
    MODE_SEO,
    MODE_TEXT,
    MODE_VIDEO,
)
from .vocab import normalize

# Semnalele care mută cererea dintr-un mod în altul. Ordinea contează: SEO și
# video sunt mai specifice decât imaginea, iar imaginea decât textul.
_VIDEO_HINTS = (
    "video", "clip", "filmare", "filmulet", "reel", "shorts", "spot", "reclama tv",
    "animatie", "secunde", "cadru", "montaj", "trailer", "storyboard", "footage",
)
_SEO_HINTS = (
    "seo", "google", "cautare", "motor de cautare", "keyword", "cuvant cheie",
    "cuvinte cheie", "meta description", "title tag", "ranking", "pozitionare",
    "indexare", "trafic organic", "serp", "alt text", "optimizat pentru cautare",
)
_IMAGE_HINTS = (
    "imagine", "poza", "fotografie", "portret", "ilustratie", "desen", "randare",
    "logo", "banner", "afis", "poster", "coperta", "miniatura", "grafica",
    "wallpaper", "mockup", "picture", "photo", "image", "artwork",
)

# Cererile care cer explicit amploare primesc un buget mai mare.
_DEPTH_HINTS = (
    "detaliat", "amanuntit", "complet", "exhaustiv", "aprofundat", "in detaliu",
    "pas cu pas", "ghid complet", "documentatie", "specificatie", "riguros",
    "cat mai bun", "cel mai bun", "profesionist", "temeinic",
)
_BREVITY_HINTS = (
    "scurt", "rapid", "concis", "pe scurt", "simplu", "o singura fraza",
    "cateva randuri", "sumar",
)

_INTENT_HINTS = {
    "tranzactional": ("cumpar", "comanda", "pret", "livrare", "reducere", "oferta", "vand"),
    "comercial": ("compar", "cel mai bun", "recenzie", "review", "alternativ", "vs "),
    "navigational": ("contact", "program", "unde se afla", "adresa"),
}

_VARIANT_HINTS = ("variante", "optiuni", "mai multe idei", "alternative", "propuneri")


@dataclass
class Decision:
    """Ce a ales automatul și motivul fiecărei alegeri."""

    options: dict[str, object] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    variants: int = 1

    def explain(self) -> str:
        return " ".join(self.reasons)


def _has(haystack: str, needles: tuple[str, ...]) -> str | None:
    for needle in needles:
        pattern = r"(?<![a-z0-9])" + re.escape(normalize(needle))
        if re.search(pattern, haystack):
            return needle
    return None


def _pick_mode(haystack: str) -> tuple[str, str]:
    hit = _has(haystack, _SEO_HINTS)
    if hit:
        return MODE_SEO, f"mod SEO, fiindcă ai scris „{hit}”"
    hit = _has(haystack, _VIDEO_HINTS)
    if hit:
        return MODE_VIDEO, f"mod video, fiindcă ai scris „{hit}”"
    hit = _has(haystack, _IMAGE_HINTS)
    if hit:
        return MODE_IMAGE, f"mod imagine, fiindcă ai scris „{hit}”"
    return MODE_TEXT, "mod text, fiindcă nu am găsit semnale de imagine, video sau SEO"


def _pick_platform(haystack: str) -> tuple[str | None, str]:
    for key, entry in PLATFORMS.items():
        for candidate in (key, normalize(entry.label.split()[0])):
            if re.search(r"(?<![a-z0-9])" + re.escape(candidate), haystack):
                return key, f"platformă {entry.label}, fiindcă ai numit-o"
    return None, ""


def _pick_length(haystack: str, mode: str) -> tuple[int, int, str]:
    if _has(haystack, _BREVITY_HINTS):
        return 300, 450, "prompt scurt, fiindcă ai cerut ceva concis"
    hit = _has(haystack, _DEPTH_HINTS)
    if hit:
        return 900, 1300, f"prompt mai lung, fiindcă ai cerut ceva „{hit}”"
    # Cu cât ideea e mai bogată, cu atât are sens un prompt mai amănunțit.
    words = len(haystack.split())
    if words >= 30:
        return 600, 900, "prompt mai amplu, fiindcă ideea ta e detaliată"
    return DEFAULT_MIN_WORDS, DEFAULT_MAX_WORDS, ""


def decide(idea: str, given: dict[str, object] | None = None) -> Decision:
    """Alege opțiunile lipsă pentru o idee, explicând fiecare alegere.

    `given` sunt opțiunile pe care le-a dat deja utilizatorul: nu se ating.
    """
    if not idea.strip():
        raise ValueError("Nu pot decide nimic fără o idee.")

    fixed = {key: value for key, value in (given or {}).items() if value not in (None, "", [], 0)}
    haystack = normalize(idea)
    decision = Decision()
    chosen: dict[str, object] = {}

    mode = fixed.get("mode")
    if mode:
        decision.reasons.append(f"mod {mode}, cum ai cerut")
    else:
        mode, why = _pick_mode(haystack)
        decision.reasons.append(why)
    chosen["mode"] = mode

    if "domain" not in fixed and mode != MODE_SEO:
        domain = detect_domain(idea, str(mode))
        if domain != "general":
            chosen["domain"] = domain
            decision.reasons.append(f"domeniul „{domain}”, din cuvintele cheie ale ideii")

    if "platform" not in fixed:
        platform, why = _pick_platform(haystack)
        if platform:
            chosen["platform"] = platform
            decision.reasons.append(why)

    if mode == MODE_SEO and "intent" not in fixed:
        for intent, hints in _INTENT_HINTS.items():
            if _has(haystack, hints):
                chosen["intent"] = intent
                decision.reasons.append(f"intenție {intent}, din felul în care e formulată cererea")
                break

    if "min_words" not in fixed and "max_words" not in fixed:
        low, high, why = _pick_length(haystack, str(mode))
        chosen["min_words"], chosen["max_words"] = low, high
        if why:
            decision.reasons.append(why)

    # Variante: la imagine, diversitatea chiar ajută; la text, rareori.
    if _has(haystack, _VARIANT_HINTS):
        decision.variants = 3
        decision.reasons.append("trei variante, fiindcă ai cerut mai multe opțiuni")
    elif mode == MODE_IMAGE:
        decision.variants = 3
        decision.reasons.append("trei variante, fiindcă la imagini direcția vizuală merită comparată")

    decision.options = {**chosen, **fixed}
    return decision
