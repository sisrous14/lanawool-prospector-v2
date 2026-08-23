"""PromptForge — generator de prompturi detaliate pentru text și imagine.

Utilizare de bibliotecă:

    from promptforge import Brief, generate

    brief = Brief(idea="o aplicație care îmi urmărește cheltuielile", mode="text")
    print(generate(brief).full_text())
"""

from __future__ import annotations

from . import image_engine, seo_engine, text_engine, video_engine
from .models import (
    Brief,
    MAX_LINKS,
    PROMPT_WORD_CAP,
    DEFAULT_MAX_WORDS,
    DEFAULT_MIN_WORDS,
    GeneratedPrompt,
    MODE_IMAGE,
    MODE_TEXT,
    MODE_SEO,
    MODE_VIDEO,
)

__version__ = "1.4.2"


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează un prompt, alegând motorul după modul cerut.

    Peste plafonul unui singur prompt, cererea aparține lanțului: `generate` nu
    taie tăcut la 3000, ci trimite explicit spre `generate_chain`.
    """
    if brief.max_words > PROMPT_WORD_CAP:
        raise ValueError(
            f"{brief.max_words} de cuvinte depășesc plafonul unui singur prompt "
            f"({PROMPT_WORD_CAP}). Folosește generate_chain(), care împarte lucrarea "
            f"într-un lanț de prompturi ce se continuă unul pe altul."
        )
    if brief.mode == MODE_IMAGE:
        return image_engine.generate(brief, variant)
    if brief.mode == MODE_VIDEO:
        return video_engine.generate(brief, variant)
    if brief.mode == MODE_SEO:
        return seo_engine.generate(brief, variant)
    return text_engine.generate(brief, variant)


def generate_chain(brief: Brief, parts: int | None = None) -> list[GeneratedPrompt]:
    """Împarte o lucrare prea mare pentru un prompt într-un lanț de prompturi.

    Fiecare verigă continuă exact de unde s-a oprit precedenta, până la
    finalizarea rezultatului — oricâte ar fi nevoie, până la limita de
    o sută.
    """
    from .chain import build

    return build(brief, parts)


def generate_many(brief: Brief, count: int = 3) -> list[GeneratedPrompt]:
    """Generează mai multe variante ale aceleiași idei.

    Fiecare variantă folosește alt seed, deci altă direcție creativă — util
    mai ales pentru imagini, unde iluminarea și unghiul schimbă mult rezultatul.
    """
    if count < 1:
        raise ValueError("count trebuie să fie cel puțin 1.")
    return [generate(brief, variant=i) for i in range(1, count + 1)]


__all__ = [
    "Brief",
    "GeneratedPrompt",
    "generate",
    "generate_many",
    "MODE_TEXT",
    "MODE_IMAGE",
    "MODE_VIDEO",
    "MODE_SEO",
    "generate_chain",
    "PROMPT_WORD_CAP",
    "MAX_LINKS",
    "DEFAULT_MIN_WORDS",
    "DEFAULT_MAX_WORDS",
    "__version__",
]
