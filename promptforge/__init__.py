"""PromptForge — generator de prompturi detaliate pentru text și imagine.

Utilizare de bibliotecă:

    from promptforge import Brief, generate

    brief = Brief(idea="o aplicație care îmi urmărește cheltuielile", mode="text")
    print(generate(brief).full_text())
"""

from __future__ import annotations

from . import image_engine, text_engine
from .models import (
    Brief,
    DEFAULT_MAX_WORDS,
    DEFAULT_MIN_WORDS,
    GeneratedPrompt,
    MODE_IMAGE,
    MODE_TEXT,
)

__version__ = "1.0.0"


def generate(brief: Brief, variant: int = 1) -> GeneratedPrompt:
    """Generează un prompt, alegând motorul după modul cerut."""
    if brief.mode == MODE_IMAGE:
        return image_engine.generate(brief, variant)
    return text_engine.generate(brief, variant)


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
    "DEFAULT_MIN_WORDS",
    "DEFAULT_MAX_WORDS",
    "__version__",
]
