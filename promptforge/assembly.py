"""Asamblarea secțiunilor într-un prompt care respectă limita de cuvinte.

Motoarele produc mai mult material decât încape; aici se decide ce intră.
Algoritmul e determinist și evită rezultatele care arată a text tăiat:

1. cât timp textul e sub minim, se adaugă secțiuni din rezervă;
2. cât timp e peste maxim, secțiunile marcate `droppable` sunt scurtate în
   ordinea descrescătoare a priorității, dar niciodată sub `min_lines`;
3. dacă tot nu încape, secțiunile cu `min_lines == 0` sunt eliminate întregi.

Un rând nu este niciodată tăiat la jumătate.
"""

from __future__ import annotations

import re
from typing import Callable

from .models import Section

_WORD_RE = re.compile(r"[^\s]+")


def count_words(text: str) -> int:
    """Numără cuvintele ignorând marcajele de titlu și de listă."""
    cleaned = re.sub(r"^[#\-*\d.]+\s*", " ", text, flags=re.MULTILINE)
    return len(_WORD_RE.findall(cleaned))


def render_section(section: Section, heading: str = "##") -> str:
    """Transformă o secțiune în text."""
    if not section.lines:
        return ""
    body: list[str] = []
    if section.lead:
        body.append(section.lead)
    if section.bullet == "1.":
        body.extend(f"{i}. {line}" for i, line in enumerate(section.lines, start=1))
    elif section.bullet:
        body.extend(f"{section.bullet} {line}" for line in section.lines)
    else:
        body.extend(section.lines)
    if section.title:
        title = f"{heading} {section.title}".strip()
        return f"{title}\n" + "\n".join(body)
    return "\n".join(body)


def range_note(word_count: int, min_words: int, max_words: int) -> str | None:
    """Semnalează onest când intervalul cerut nu a putut fi respectat.

    Structura obligatorie a unui prompt are o lungime minimă; sub ea nu se poate
    coborî fără ca promptul să devină un ciot. Când se întâmplă, spunem.
    """
    if word_count > max_words:
        return (
            f"Structura minimă a promptului ocupă {word_count} de cuvinte, peste limita de "
            f"{max_words} cerută. Scade numărul de cerințe (--must) sau acceptă lungimea."
        )
    if word_count < min_words:
        return (
            f"Materialul disponibil s-a epuizat la {word_count} de cuvinte, sub minimul de "
            f"{min_words}. Adaugă detalii în idee sau cerințe cu --must."
        )
    return None


def sentence(text: str) -> str:
    """Majusculă la început și punct la final — descriptorii vin din liste."""
    text = text.strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    # Două puncte sau punct-virgulă închid deja rândul: un punct în plus ar da „:.”
    if text[-1] not in ".!?:;":
        text += "."
    return text


def render(sections: list[Section], heading: str = "##") -> str:
    blocks = [render_section(s, heading) for s in sections]
    return "\n\n".join(block for block in blocks if block.strip())


def _clone(section: Section) -> Section:
    return Section(
        title=section.title,
        lines=list(section.lines),
        priority=section.priority,
        bullet=section.bullet,
        droppable=section.droppable,
        min_lines=section.min_lines,
        lead=section.lead,
        expansions=list(section.expansions),
    )


def fit(
    sections: list[Section],
    min_words: int,
    max_words: int,
    reserve: list[Section] | None = None,
    renderer: Callable[[list[Section]], str] | None = None,
) -> tuple[list[Section], str]:
    """Ajustează setul de secțiuni ca textul să cadă în intervalul cerut.

    `renderer` trebuie să fie exact funcția care produce textul final: fiecare
    model-țintă are altă redare (etichete, titluri, paragraf continuu), iar o
    măsurare făcută pe altă formă decât cea livrată ratează limitele.

    Întoarce secțiunile păstrate și textul redat.
    """
    draw = renderer or (lambda secs: render(secs))
    chosen = [_clone(s) for s in sections]
    pool = [_clone(s) for s in (reserve or [])]

    def total() -> int:
        return count_words(draw(chosen))

    # 1. Completare până la minim: întâi secțiuni întregi din rezervă.
    while pool and total() < min_words:
        chosen.append(pool.pop(0))

    # 2. Dacă tot e prea scurt, se adaugă extensiile — pe rând, câte una din
    #    fiecare secțiune, ca promptul să crească echilibrat, nu într-un singur loc.
    if total() < min_words:
        round_index = 0
        while total() < min_words:
            added = False
            for section in chosen:
                if round_index < len(section.expansions):
                    section.lines.append(section.expansions[round_index])
                    added = True
                    if total() >= min_words:
                        break
            if not added:
                break     # s-au epuizat extensiile
            round_index += 1

    # 3. Scurtare: prioritatea mare (cel mai puțin important) se sacrifică prima.
    #    În interiorul aceleiași priorități, secțiunile de la final cedează primele.
    def sacrifice_order() -> list[int]:
        return sorted(
            (i for i, s in enumerate(chosen) if s.droppable and s.lines),
            key=lambda i: (-chosen[i].priority, -i),
        )

    for index in sacrifice_order():
        section = chosen[index]
        while total() > max_words and len(section.lines) > max(section.min_lines, 1):
            section.lines.pop()
        if total() <= max_words:
            break

    # 4. Dacă tot nu încape, se elimină secțiunile care pot lipsi cu totul.
    if total() > max_words:
        for index in sacrifice_order():
            if chosen[index].min_lines == 0:
                chosen[index].lines = []
            if total() <= max_words:
                break

    chosen = [s for s in chosen if s.lines]
    return chosen, draw(chosen)
