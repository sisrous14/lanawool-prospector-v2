"""Lanțuri de prompturi, pentru lucrări care nu încap într-unul singur.

Un prompt are o limită practică de 3000 de cuvinte. Când cererea are nevoie de
mai mult, programul nu taie: împarte lucrarea într-un lanț de prompturi, fiecare
continuând exact de unde s-a oprit precedentul, până la finalizarea rezultatului.
Dacă sunt necesare o sută de prompturi, se generează o sută.

Legătura dintre verigi e un bloc de stare pe care partea K îl produce la final
și pe care îl lipești în partea K+1. Programul nu vede rezultatele — deci nu
poate transporta el conținutul — dar impune protocolul prin care se transportă
singur, fără repetări și fără reluări.
"""

from __future__ import annotations

import math
from dataclasses import replace

from .assembly import count_words, fit
from .models import (
    Brief,
    CHAIN_OVERHEAD,
    GeneratedPrompt,
    MAX_LINKS,
    MODE_SEO,
    MODE_TEXT,
    PROMPT_WORD_CAP,
    Section,
)
from .targets import TEXT_TARGETS, default_text_target
from .text_engine import render_sections

# Cât încape efectiv într-o verigă, după ce scădem protocolul de continuare.
_CHAIN_OVERHEAD = CHAIN_OVERHEAD
_LINK_CEILING = PROMPT_WORD_CAP - CHAIN_OVERHEAD
MAX_TOTAL_WORDS = _LINK_CEILING * MAX_LINKS

# Sub atât o verigă nu are cum să încapă: structura minimă a unui prompt plus
# protocolul de continuare. Cerută mai mică, o ridicăm și spunem că am ridicat-o.
LINK_FLOOR = 300 + CHAIN_OVERHEAD + 40

CHAINABLE = (MODE_TEXT, MODE_SEO)

_TAGS = {
    "LUCRARE ÎN MAI MULTE PĂRȚI": "lucrare_in_parti",
    "WORK IN MULTIPLE PARTS": "lucrare_in_parti",
    "CONTINUARE": "continuare",
    "CONTINUATION": "continuare",
    "CONTEXTUL LUCRĂRII": "context_lucrare",
    "THE WORK SO FAR": "context_lucrare",
    "BLOC DE STARE": "bloc_stare",
    "STATE BLOCK": "bloc_stare",
    "ÎNCHEIERE": "incheiere",
    "CLOSING": "closing",
}

_STATE_TEMPLATE = """<<<STARE>>>
PARTEA: {part} din {total}
PLAN: (planul numerotat al părților, pe scurt, așa cum a fost stabilit în partea 1)
ACOPERIT: (ce ai scris efectiv în această parte, în două rânduri)
ULTIMA FRAZĂ: (ultimele 15 cuvinte scrise, textual, ca următoarea parte să știe exact unde s-a oprit)
URMEAZĂ: (ce intră în partea {next_part})
<<<SFÂRȘIT STARE>>>"""

_STATE_TEMPLATE_EN = """<<<STATE>>>
PART: {part} of {total}
PLAN: (the numbered plan of parts, briefly, as fixed in part 1)
COVERED: (what you actually wrote in this part, in two lines)
LAST SENTENCE: (the last 15 words written, verbatim, so the next part knows exactly where it stopped)
NEXT: (what goes into part {next_part})
<<<END STATE>>>"""


class ChainError(ValueError):
    """Lanțul nu poate fi construit așa cum s-a cerut."""


def plan_links(
    min_words: int, max_words: int, parts: int | None = None
) -> tuple[int, int, int]:
    """Câte verigi are lanțul și cât are fiecare.

    Două situații diferite. Când ceri un număr de părți, fiecare verigă rămâne
    de mărimea pe care ai cerut-o: vrei cinci prompturi întregi, nu cinci
    ciopârțite. Când ceri un total de cuvinte, el se împarte la verigi.

    Întoarce (numărul de verigi, minimul, maximul pe verigă).
    """
    ceiling = _LINK_CEILING

    if parts is not None:
        if parts < 1:
            raise ChainError("Un lanț are cel puțin o verigă.")
        if parts > MAX_LINKS:
            raise ChainError(
                f"Maximum {MAX_LINKS} de verigi. Peste atât, lucrarea trebuie "
                f"împărțită altfel, nu lungită."
            )
        per_link_max = min(max(max_words, LINK_FLOOR if parts > 1 else 0), ceiling)
        per_link_min = min(min_words, per_link_max - 50)
        return parts, max(300, per_link_min), per_link_max

    if max_words > MAX_TOTAL_WORDS:
        raise ChainError(
            f"{max_words} de cuvinte ar cere peste {MAX_LINKS} de prompturi. "
            f"Maximul e {MAX_TOTAL_WORDS}."
        )
    links = max(1, math.ceil(max_words / ceiling))
    floor = LINK_FLOOR if links > 1 else 350
    per_link_max = min(ceiling, max(floor, math.ceil(max_words / links)))
    per_link_min = max(300, int(per_link_max * 0.8))
    if per_link_min >= per_link_max:
        per_link_min = per_link_max - 50
    return links, per_link_min, per_link_max


def _state_block(part: int, total: int, lang: str) -> str:
    template = _STATE_TEMPLATE if lang == "ro" else _STATE_TEMPLATE_EN
    return template.format(part=part, total=total, next_part=min(part + 1, total))


def _first_link_sections(total: int, lang: str) -> list[Section]:
    """Blocurile care se adaugă primei verigi."""
    if lang == "ro":
        title = "LUCRARE ÎN MAI MULTE PĂRȚI"
        lines = [
            f"Rezultatul complet nu încape într-un singur răspuns. Îl produci în {total} părți, "
            f"iar aceasta este partea 1.",
            f"Începe cu planul numerotat al celor {total} părți, în maximum 12 rânduri. Planul "
            f"rămâne fix: părțile următoare se vor referi la el, așa că fă-l acum bine.",
            "Apoi scrie integral partea 1. Nu rezuma părțile următoare, nu le anticipa și nu "
            "scrie o introducere despre ce va urma.",
            "Oprește-te la finalul părții 1, nu la un număr de cuvinte, și încheie cu blocul de "
            "stare cerut mai jos, exact în forma dată.",
        ]
        state_title = "BLOC DE STARE"
        state_lead = (
            "Ultimul lucru din răspunsul tău, după conținut, este exact acest bloc, completat:"
        )
    else:
        title = "WORK IN MULTIPLE PARTS"
        lines = [
            f"The complete result does not fit in one response. You produce it in {total} parts, "
            f"and this is part 1.",
            f"Start with the numbered plan of all {total} parts, in at most 12 lines. The plan is "
            f"fixed: later parts will refer to it, so get it right now.",
            "Then write part 1 in full. Do not summarise the later parts, do not anticipate them, "
            "and do not write an introduction about what is coming.",
            "Stop at the end of part 1, not at a word count, and finish with the state block "
            "below, exactly in the form given.",
        ]
        state_title = "STATE BLOCK"
        state_lead = "The last thing in your response, after the content, is exactly this block, filled in:"

    return [
        Section(title, lines, priority=1, bullet="1."),
        Section(state_title, [_state_block(1, total, lang)], priority=1, lead=state_lead),
    ]


def _later_link_sections(
    part: int, total: int, brief: Brief, lang: str
) -> tuple[list[Section], list[Section]]:
    """Secțiunile unei verigi de continuare, plus rezerva ei."""
    from .depth import text_depth

    last = part == total

    if lang == "ro":
        context = Section(
            "CONTEXTUL LUCRĂRII",
            [
                f"Cererea inițială, neschimbată: „{brief.idea}”.",
                f"Lucrarea se scrie în {total} părți. Planul lor a fost stabilit în partea 1 și "
                f"nu se schimbă acum.",
            ],
            priority=1,
        )
        continuation = Section(
            "CONTINUARE",
            [
                f"Aceasta este partea {part} din {total}.",
                "Lipește imediat sub acest rând blocul de stare produs de partea "
                f"{part - 1}, apoi continuă de acolo:",
                "",
                "⟨lipește aici blocul <<<STARE>>> din partea anterioară⟩",
                "",
                "Continui exact din punctul indicat de „ULTIMA FRAZĂ”. Nu reiei, nu rezumi ce "
                "s-a scris deja, nu scrii introducere și nu repeți planul.",
                "Prima ta propoziție se leagă direct de ultima propoziție anterioară, ca și cum "
                "ai fi scris tot textul dintr-o suflare.",
            ],
            priority=1,
        )
        if last:
            closing = Section(
                "ÎNCHEIERE",
                [
                    "Aceasta este ultima parte. Închei lucrarea complet: nicio secțiune din plan "
                    "nu rămâne nescrisă.",
                    "După conținut, adaugă maximum trei rânduri cu ce a rămas totuși neacoperit, "
                    "dacă a rămas ceva. Dacă nu a rămas nimic, scrie „complet”.",
                ],
                priority=1,
                bullet="-",
            )
        else:
            closing = Section(
                "BLOC DE STARE",
                [_state_block(part, total, lang)],
                priority=1,
                lead="Ultimul lucru din răspunsul tău, după conținut, este exact acest bloc, completat:",
            )
    else:
        context = Section(
            "THE WORK SO FAR",
            [
                f'The original request, unchanged: "{brief.idea}".',
                f"The work is written in {total} parts. Their plan was fixed in part 1 and does "
                f"not change now.",
            ],
            priority=1,
        )
        continuation = Section(
            "CONTINUATION",
            [
                f"This is part {part} of {total}.",
                f"Paste the state block produced by part {part - 1} immediately below this line, "
                f"then continue from there:",
                "",
                "⟨paste the <<<STATE>>> block from the previous part here⟩",
                "",
                "Continue exactly from the point marked by `LAST SENTENCE`. Do not restart, do not "
                "summarise what was written, do not write an introduction and do not repeat the plan.",
                "Your first sentence connects directly to the previous last sentence, as if the "
                "whole text had been written in one go.",
            ],
            priority=1,
        )
        if last:
            closing = Section(
                "CLOSING",
                [
                    "This is the final part. Finish the work completely: no section of the plan is "
                    "left unwritten.",
                    "After the content, add at most three lines on what remains uncovered, if "
                    "anything. If nothing remains, write `complete`.",
                ],
                priority=1,
                bullet="-",
            )
        else:
            closing = Section(
                "STATE BLOCK",
                [_state_block(part, total, lang)],
                priority=1,
                lead="The last thing in your response, after the content, is exactly this block, filled in:",
            )

    # Fiecare verigă primește altă felie din materialul de adâncime, ca să aducă
    # ceva nou, nu să repete îndrumarea din prima.
    depth = text_depth(lang)
    stride = max(1, len(depth) // max(1, total))
    start = ((part - 1) * stride) % len(depth)
    reserve = depth[start:] + depth[:start]

    return [context, continuation, closing], reserve


def build(brief: Brief, parts: int | None = None) -> list[GeneratedPrompt]:
    """Împarte lucrarea într-un lanț de prompturi care se continuă unul pe altul."""
    from . import generate

    if brief.mode not in CHAINABLE:
        raise ChainError(
            f"Lanțul are sens doar pentru moduri cu rezultat continuu ({', '.join(CHAINABLE)}). "
            f"Pentru {brief.mode} folosește `serie`, care dă mai multe prompturi independente."
        )

    total, per_min, per_max = plan_links(brief.min_words, brief.max_words, parts)
    target = brief.target or default_text_target()
    if target not in TEXT_TARGETS:
        raise ChainError(f"Țintă necunoscută: {target!r}.")
    style = TEXT_TARGETS[target]["style"]
    lang = brief.lang

    if total == 1:
        return [generate(brief)]

    results: list[GeneratedPrompt] = []
    chain_notes: list[str] = []
    if per_max > brief.max_words:
        chain_notes.append(
            f"Verigile au {per_max} de cuvinte în loc de {brief.max_words}: sub atât nu "
            f"încap structura promptului și protocolul de continuare."
        )

    # Prima verigă e promptul complet, plus protocolul de lanț. Bugetul cerut
    # motorului scade cu exact cât ocupă protocolul, ca veriga să nu iasă din
    # limita pe care am promis-o.
    head_max = max(320, per_max - _CHAIN_OVERHEAD)
    head_min = min(per_min, head_max - 50)
    head_brief = replace(brief, min_words=max(300, head_min), max_words=head_max)
    head = generate(head_brief)
    chain_text = render_sections(_first_link_sections(total, lang), style, lang, _TAGS)
    head.prompt = f"{head.prompt}\n\n{chain_text}"
    head.word_count = count_words(head.prompt)
    head.variant = 1
    head.notes = (
        [f"Veriga 1 din {total}. Cere planul lucrării, apoi scrie partea 1."]
        + chain_notes + head.notes
    )
    results.append(head)

    # Verigile următoare sunt prompturi de continuare, cu altă felie de îndrumare.
    for part in range(2, total + 1):
        sections, reserve = _later_link_sections(part, total, brief, lang)
        _, prompt = fit(
            sections, per_min, per_max, reserve,
            renderer=lambda secs: render_sections(secs, style, lang, _TAGS),
        )
        note = (
            f"Veriga {part} din {total}. Lipește blocul de stare din partea {part - 1} "
            f"acolo unde promptul îți cere."
        )
        results.append(GeneratedPrompt(
            prompt=prompt,
            mode=brief.mode,
            domain=head.domain,
            target=target,
            word_count=count_words(prompt),
            variant=part,
            notes=[note] + chain_notes + list(TEXT_TARGETS[target].get("notes", [])),
        ))

    return results
