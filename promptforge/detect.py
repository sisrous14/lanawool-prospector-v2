"""Detecția domeniului și alegerea deterministă a descriptorilor."""

from __future__ import annotations

import random
import re

from .models import MODE_IMAGE, MODE_TEXT, MODE_VIDEO
from .vocab import IMAGE_DOMAINS, TEXT_DOMAINS, VIDEO_DOMAINS, normalize

# Cuvinte prea frecvente ca să spună ceva despre subiect.
_STOPWORDS = {
    # legături și determinanți
    "un", "una", "unei", "unui", "sau", "si", "de", "la", "in", "pe", "cu",
    "care", "pentru", "din", "al", "ale", "alta", "altul", "cel", "cea",
    "acest", "aceasta", "acesta", "aceste", "meu", "mea", "mele", "lui", "ei",
    "lor", "sale", "catre", "fara", "langa", "sub", "peste", "intre", "dupa",
    "inainte", "prin", "despre", "asupra", "deci", "doar", "chiar", "foarte",
    "mult", "multe", "putin", "orice", "ceva", "toate", "tot", "toti",
    # verbe și adverbe golite de conținut într-o cerere
    "este", "sunt", "fie", "avea", "are", "aiba", "face", "faca", "fac",
    "vreau", "vrea", "voi", "poate", "pot", "trebuie", "arata", "arate",
    "spune", "spuna", "dau", "dea", "folosesc", "folosi", "ajute", "ajuta",
    "unde", "cand", "cum", "cine", "ceea", "asa", "cat", "cate", "imi",
    "mie", "sine", "mai", "apoi", "acum", "atunci",
    # engleză
    "the", "an", "of", "to", "on", "with", "for", "and", "or", "that", "this",
    "is", "are", "be", "been", "it", "its", "my", "our", "your", "want",
    "make", "create", "build", "need", "would", "should", "could", "will",
    "shows", "show", "using", "used", "from", "into", "about", "very",
    "some", "any", "all", "which", "where", "when", "what", "how",
}


def detect_domain(idea: str, mode: str) -> str:
    """Alege domeniul care se potrivește cel mai bine ideii.

    Scorul e numărul de cuvinte-cheie găsite; la egalitate câștigă domeniul cu
    potrivirea cea mai lungă, ca „concept art” să bată „art”.
    """
    table = {
        MODE_IMAGE: IMAGE_DOMAINS,
        MODE_VIDEO: VIDEO_DOMAINS,
    }.get(mode, TEXT_DOMAINS)
    haystack = normalize(idea)
    best_domain = "general"
    best_score = (0, 0)

    for name, data in table.items():
        keywords: list[str] = data.get("keywords", [])  # type: ignore[assignment]
        hits = 0
        longest = 0
        for keyword in keywords:
            key = normalize(keyword)
            pattern = r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])"
            if re.search(pattern, haystack):
                hits += 1
                longest = max(longest, len(key))
        score = (hits, longest)
        if score > best_score:
            best_score = score
            best_domain = name

    return best_domain


def keywords_of(idea: str, limit: int = 6) -> list[str]:
    """Extrage cuvintele purtătoare de sens din idee (pentru accente)."""
    words = re.findall(r"[\wăâîșț-]+", idea.lower(), flags=re.UNICODE)
    seen: list[str] = []
    for word in words:
        if len(word) < 4 or normalize(word) in _STOPWORDS:
            continue
        if word not in seen:
            seen.append(word)
    return seen[:limit]


class Picker:
    """Alegere reproductibilă din liste de descriptori.

    Același `seed` dă mereu aceleași alegeri; `--variants` schimbă seed-ul și
    obține o direcție creativă diferită pentru aceeași idee.

    `liked` și `disliked` vin din feedback-ul utilizatorului: descriptorii pe
    care i-a marcat ca buni sunt preferați, cei marcați ca slabi sunt ocoliți —
    dar niciodată în așa fel încât să rămână fără opțiuni.
    """

    def __init__(
        self,
        seed: int,
        liked: set[str] | None = None,
        disliked: set[str] | None = None,
    ) -> None:
        self._random = random.Random(seed)
        self._liked = liked or set()
        self._disliked = disliked or set()
        self.chosen: list[str] = []

    def _shortlist(self, options: list[str]) -> list[str]:
        allowed = [option for option in options if option not in self._disliked]
        if not allowed:
            allowed = options            # totul e pe lista neagră: o ignorăm
        preferred = [option for option in allowed if option in self._liked]
        return preferred or allowed

    def one(self, options: list[str], fallback: str = "") -> str:
        if not options:
            return fallback
        choice = self._random.choice(self._shortlist(options))
        self.chosen.append(choice)
        return choice

    def some(self, options: list[str], count: int) -> list[str]:
        if not options:
            return []
        allowed = self._shortlist(options)
        count = min(count, len(allowed))
        picks = self._random.sample(allowed, count)
        self.chosen.extend(picks)
        return picks


__all__ = ["detect_domain", "keywords_of", "Picker", "MODE_TEXT", "MODE_IMAGE", "MODE_VIDEO"]
