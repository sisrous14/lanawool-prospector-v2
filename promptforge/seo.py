"""Prompturi SEO pornind de la conținutul tău.

Îi dai un text, un fișier, o adresă sau o poză, iar el construiește promptul
care produce textul optimizat pentru căutare: title, meta description,
structură de titluri, alt text, FAQ, slug.

Ce se întâmplă local, fără niciun model: extragerea cuvintelor-cheie din
conținutul dat, statisticile lui și limitele exacte de caractere. Promptul e
astfel legat de textul tău concret, nu de o idee generică despre el.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from .catalog import known_fields
from .models import Section
from .vocab import normalize

# Cuvinte care apar des în orice text și nu spun nimic despre subiect.
_STOP = {
    # română
    "acest", "acesta", "aceasta", "aceste", "acestea", "acel", "acea", "acele",
    "adica", "afara", "aici", "alta", "alte", "altul", "apoi", "asta", "astfel",
    "atat", "atunci", "avea", "avem", "aveti", "care", "cand", "catre", "ceea",
    "cele", "celor", "chiar", "cine", "cred", "cum", "cumva", "daca", "dar",
    "dat", "decat", "deci", "despre", "din", "dintre", "doar", "dupa", "este",
    "eram", "erau", "fata", "fara", "fiind", "foarte", "fost", "insa", "intre",
    "isi", "iti", "lor", "mai", "mare", "mult", "multe", "nici", "noastre",
    "nostru", "numai", "orice", "pana", "pentru", "peste", "poate", "prea",
    "prin", "sale", "sau", "sunt", "toate", "toti", "tot", "trebuie", "unde",
    "unei", "unor", "unui", "vom", "vor", "vrea", "vreau", "aveau", "asupra",
    "cateva", "fiecare", "aproape", "totusi", "deja", "iar", "ori", "ca",
    # engleză
    "about", "after", "again", "against", "all", "also", "and", "any", "are",
    "because", "been", "before", "being", "between", "both", "but", "can",
    "cannot", "could", "did", "does", "doing", "down", "during", "each", "few",
    "for", "from", "further", "had", "has", "have", "having", "here", "how",
    "into", "its", "itself", "just", "more", "most", "not", "now", "only",
    "other", "our", "out", "over", "own", "same", "should", "some", "such",
    "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "too", "under", "until", "very", "was", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will",
    "with", "would", "you", "your",
}

_WORD = re.compile(r"[a-zăâîșşțţ][a-zăâîșşțţ0-9-]{2,}", re.IGNORECASE)


def _stems(phrase: str) -> tuple[str, ...]:
    """Rădăcinile aproximative ale cuvintelor, pentru comparație."""
    return tuple(sorted(word[:5] for word in phrase.split()))


@dataclass
class SourceStats:
    """Ce știm despre conținutul primit, măsurat local."""

    words: int
    sentences: int
    avg_sentence: float
    headings: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)

    def describe(self, lang: str) -> str:
        if lang == "ro":
            text = (
                f"Sursa are {self.words} de cuvinte în {self.sentences} propoziții, "
                f"cu o medie de {self.avg_sentence:.0f} de cuvinte pe propoziție."
            )
            if self.headings:
                text += f" Titluri existente: {len(self.headings)}."
            if self.questions:
                text += f" Întrebări puse în text: {len(self.questions)}."
            return text
        text = (
            f"The source has {self.words} words across {self.sentences} sentences, "
            f"averaging {self.avg_sentence:.0f} words per sentence."
        )
        if self.headings:
            text += f" Existing headings: {len(self.headings)}."
        if self.questions:
            text += f" Questions raised in the text: {len(self.questions)}."
        return text


def analyse(text: str) -> SourceStats:
    """Măsoară textul sursă: lungime, ritm, titluri, întrebări."""
    lines = [line.strip() for line in text.splitlines()]
    headings = [
        line.lstrip("#").strip()
        for line in lines
        if line.startswith("#") or (0 < len(line) < 70 and line.isupper())
    ]
    # Propozițiile se taie păstrând semnul de la final, ca întrebările să poată
    # fi recunoscute după el — și ca o întrebare să fie doar propoziția ei, nu
    # tot textul dinaintea semnului.
    pieces = [piece.strip() for piece in re.findall(r"[^.!?]*[.!?]", text)]
    sentences = [piece for piece in pieces if piece]
    questions = [piece for piece in sentences if piece.endswith("?")]
    words = len(_WORD.findall(text))
    return SourceStats(
        words=words,
        sentences=max(len(sentences), 1),
        avg_sentence=words / max(len(sentences), 1),
        headings=headings[:8],
        questions=[q for q in questions if len(q) < 160][:6],
    )


def keywords(text: str, limit: int = 8) -> tuple[str, list[str]]:
    """Extrage cuvântul-cheie principal și variantele secundare.

    Frecvență simplă peste cuvinte și perechi de cuvinte, fără cele de umplutură.
    Nu e un instrument de cercetare a cuvintelor-cheie — nu are date de volum de
    căutare — dar spune fidel despre ce e textul primit.
    """
    tokens = [normalize(word) for word in _WORD.findall(text)]
    content = [token for token in tokens if token not in _STOP and len(token) > 3]
    if not content:
        return "", []

    singles = Counter(content)
    # Perechile prind expresiile reale: „paine cu maia” bate „paine” singur.
    pairs = Counter(
        f"{first} {second}"
        for first, second in zip(content, content[1:])
        if first != second
    )

    ranked: list[tuple[str, int]] = []
    for phrase, count in pairs.most_common(limit * 2):
        if count >= 2:
            ranked.append((phrase, count * 2))     # expresiile cântăresc dublu
    ranked.extend(singles.most_common(limit * 2))
    ranked.sort(key=lambda item: -item[1])

    chosen: list[str] = []
    seen_stems: set[tuple[str, ...]] = set()
    for phrase, _ in ranked:
        # „paine maia” și „painea maia” sunt aceeași expresie: comparăm rădăcinile,
        # fiindcă româna articulează substantivele prin sufix.
        stems = _stems(phrase)
        if stems in seen_stems or any(phrase in existing for existing in chosen):
            continue
        seen_stems.add(stems)
        chosen.append(phrase)
        if len(chosen) > limit:
            break

    return (chosen[0] if chosen else ""), chosen[1:limit]


# ---------------------------------------------------------------------------
# Tipuri de conținut și livrabilele lor
# ---------------------------------------------------------------------------

CONTENT_TYPES: dict[str, dict[str, object]] = {
    "articol": {
        "label": {"ro": "articol de blog", "en": "blog article"},
        "deliverables": {
            "ro": [
                "TITLE TAG — maximum 60 de caractere, cu cuvântul-cheie în prima jumătate",
                "META DESCRIPTION — maximum 155 de caractere, cu un motiv concret de clic",
                "H1 — diferit de title tag, formulat pentru cititor, nu pentru motor",
                "STRUCTURA — patru până la șapte titluri H2, fiecare răspunzând unei întrebări reale",
                "INTRODUCERE — 60-90 de cuvinte, cu răspunsul principal deja în primul paragraf",
                "CORPUL — text complet, cu cuvântul-cheie apărând natural, nu forțat",
                "FAQ — trei-cinci întrebări cu răspunsuri de 40-60 de cuvinte, gata de marcaj FAQPage",
                "SLUG — scurt, cu cuvântul-cheie, fără cuvinte de umplutură",
                "ANCORE INTERNE — trei texte de link către pagini înrudite",
            ],
            "en": [
                "TITLE TAG — at most 60 characters, keyword in the first half",
                "META DESCRIPTION — at most 155 characters, with a concrete reason to click",
                "H1 — different from the title tag, written for the reader, not the engine",
                "STRUCTURE — four to seven H2 headings, each answering a real question",
                "INTRODUCTION — 60-90 words, with the main answer already in the first paragraph",
                "BODY — the full text, with the keyword appearing naturally rather than forced",
                "FAQ — three to five questions with 40-60 word answers, ready for FAQPage markup",
                "SLUG — short, with the keyword, no filler words",
                "INTERNAL ANCHORS — three link texts pointing to related pages",
            ],
        },
    },
    "produs": {
        "label": {"ro": "pagină de produs", "en": "product page"},
        "deliverables": {
            "ro": [
                "TITLE TAG — maximum 60 de caractere: produs, atribut distinctiv, marcă",
                "META DESCRIPTION — maximum 155 de caractere, cu beneficiul și un semnal de încredere",
                "H1 — numele produsului așa cum îl caută oamenii, nu codul intern",
                "DESCRIERE SCURTĂ — 40-60 de cuvinte, pentru listare și pentru primul ecran",
                "DESCRIERE LUNGĂ — 200-350 de cuvinte, organizată pe beneficii, nu pe specificații",
                "BULLET-URI — cinci, fiecare cu un beneficiu concret, nu cu un adjectiv",
                "SPECIFICAȚII — tabel cu atributele care contează la comparație",
                "FAQ — trei întrebări reale de dinainte de cumpărare",
                "TEXT ALTERNATIV — pentru fiecare imagine de produs, descriptiv, sub 100 de caractere",
                "SLUG — categorie plus produs, fără cod de articol",
            ],
            "en": [
                "TITLE TAG — at most 60 characters: product, distinguishing attribute, brand",
                "META DESCRIPTION — at most 155 characters, with the benefit and a trust signal",
                "H1 — the product name as people search for it, not the internal code",
                "SHORT DESCRIPTION — 40-60 words, for listings and the first screen",
                "LONG DESCRIPTION — 200-350 words, organised by benefit rather than by spec",
                "BULLETS — five, each with a concrete benefit, not an adjective",
                "SPECIFICATIONS — a table of the attributes that matter when comparing",
                "FAQ — three real pre-purchase questions",
                "ALT TEXT — for each product image, descriptive, under 100 characters",
                "SLUG — category plus product, no article code",
            ],
        },
    },
    "imagine": {
        "label": {"ro": "optimizare de imagine", "en": "image optimisation"},
        "deliverables": {
            "ro": [
                "TEXT ALTERNATIV — sub 100 de caractere, descriptiv, cu cuvântul-cheie doar dacă e natural",
                "NUME DE FIȘIER — cuvinte separate prin cratimă, fără diacritice, fără cifre aleatorii",
                "TITLU DE IMAGINE — atributul title, complementar textului alternativ, nu identic",
                "LEGENDĂ — una-două propoziții care adaugă context, nu repetă alt text-ul",
                "TEXT ÎNCONJURĂTOR — 50-80 de cuvinte de context, fiindcă motoarele citesc și vecinătatea",
                "SCHEMA ImageObject — câmpurile contentUrl, caption, creator, license",
                "TITLE TAG ȘI META pentru pagina care găzduiește imaginea",
            ],
            "en": [
                "ALT TEXT — under 100 characters, descriptive, keyword only if it fits naturally",
                "FILE NAME — hyphen-separated words, no diacritics, no random digits",
                "IMAGE TITLE — the title attribute, complementary to the alt text rather than identical",
                "CAPTION — one or two sentences adding context, not repeating the alt text",
                "SURROUNDING TEXT — 50-80 words of context, because engines read the neighbourhood too",
                "ImageObject SCHEMA — contentUrl, caption, creator and license fields",
                "TITLE TAG AND META for the page hosting the image",
            ],
        },
    },
    "categorie": {
        "label": {"ro": "pagină de categorie", "en": "category page"},
        "deliverables": {
            "ro": [
                "TITLE TAG — maximum 60 de caractere, cu categoria și un calificativ",
                "META DESCRIPTION — maximum 155 de caractere, cu numărul de produse dacă e relevant",
                "H1 — numele categoriei, curat",
                "TEXT INTRODUCTIV — 80-120 de cuvinte, deasupra listei, care ajută alegerea",
                "GHID DE ALEGERE — trei criterii după care cumpărătorul decide",
                "FAQ — trei întrebări despre categorie, nu despre un produs anume",
                "ANCORE — către subcategorii și către produsele reprezentative",
            ],
            "en": [
                "TITLE TAG — at most 60 characters, with the category and a qualifier",
                "META DESCRIPTION — at most 155 characters, with the product count if relevant",
                "H1 — the category name, clean",
                "INTRO TEXT — 80-120 words above the listing, helping the choice",
                "BUYING GUIDE — three criteria the buyer decides on",
                "FAQ — three questions about the category, not about one product",
                "ANCHORS — to subcategories and to representative products",
            ],
        },
    },
    "landing": {
        "label": {"ro": "pagină de aterizare", "en": "landing page"},
        "deliverables": {
            "ro": [
                "TITLE TAG și META DESCRIPTION, în limitele exacte",
                "H1 — promisiunea centrală, în maximum 10 cuvinte",
                "SUBTITLU — o propoziție care explică pentru cine e",
                "TREI SECȚIUNI — problemă, soluție, dovadă, fiecare cu H2 propriu",
                "DOVEZI — trei elemente concrete: cifră, mărturie sau mecanism",
                "CTA — textul butonului plus rândul de sub el",
                "FAQ — trei obiecții reale, tratate ca întrebări",
            ],
            "en": [
                "TITLE TAG and META DESCRIPTION, within the exact limits",
                "H1 — the central promise, in at most 10 words",
                "SUBHEAD — one sentence saying who it is for",
                "THREE SECTIONS — problem, solution, proof, each with its own H2",
                "PROOF — three concrete items: a number, a testimonial or a mechanism",
                "CTA — the button text plus the line beneath it",
                "FAQ — three real objections, phrased as questions",
            ],
        },
    },
    "local": {
        "label": {"ro": "SEO local", "en": "local SEO"},
        "deliverables": {
            "ro": [
                "TITLE TAG — serviciu plus oraș, sub 60 de caractere",
                "META DESCRIPTION — cu zona deservită și un motiv de contact",
                "H1 — serviciul, formulat cum îl caută localnicii",
                "DESCRIERE GOOGLE BUSINESS — 700-750 de caractere",
                "TEXT DE PAGINĂ — 250-400 de cuvinte, cu repere locale reale, nu inventate",
                "NAP — nume, adresă, telefon, scrise identic peste tot",
                "FAQ — trei întrebări locale: program, parcare, zonă deservită",
            ],
            "en": [
                "TITLE TAG — service plus city, under 60 characters",
                "META DESCRIPTION — with the area served and a reason to get in touch",
                "H1 — the service, phrased the way locals search for it",
                "GOOGLE BUSINESS DESCRIPTION — 700-750 characters",
                "PAGE TEXT — 250-400 words, with real local landmarks, not invented ones",
                "NAP — name, address, phone, written identically everywhere",
                "FAQ — three local questions: hours, parking, area served",
            ],
        },
    },
}

INTENTS: dict[str, dict[str, str]] = {
    "informational": {
        "ro": "informațională: omul vrea să înțeleagă ceva, nu să cumpere. Răspunsul vine primul, vânzarea nu vine deloc.",
        "en": "informational: the person wants to understand something, not to buy. The answer comes first; the sell does not come at all.",
    },
    "comercial": {
        "ro": "comercială: omul compară opțiuni înainte de a decide. Are nevoie de criterii, nu de superlative.",
        "en": "commercial: the person is comparing options before deciding. They need criteria, not superlatives.",
    },
    "tranzactional": {
        "ro": "tranzacțională: omul e gata să cumpere. Are nevoie de preț, disponibilitate, livrare și un buton.",
        "en": "transactional: the person is ready to buy. They need price, availability, delivery and a button.",
    },
    "navigational": {
        "ro": "navigațională: omul caută ceva anume și trebuie doar să ajungă acolo repede.",
        "en": "navigational: the person is looking for something specific and just needs to get there fast.",
    },
}

DEFAULT_TYPE = "articol"
DEFAULT_INTENT = "informational"
