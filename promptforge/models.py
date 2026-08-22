"""Structurile de date folosite în tot pachetul."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

MODE_TEXT = "text"
MODE_IMAGE = "image"

DEFAULT_MIN_WORDS = 300
DEFAULT_MAX_WORDS = 500


@dataclass
class Brief:
    """Cererea utilizatorului: ideea brută plus opțiunile de generare."""

    idea: str
    mode: str = MODE_TEXT
    domain: str | None = None          # None => detecție automată
    target: str | None = None          # modelul-țintă (vezi targets.py)
    audience: str | None = None
    tone: str | None = None
    style: str | None = None           # doar pentru imagine: stil impus
    aspect: str | None = None          # doar pentru imagine
    subject: str | None = None         # doar pentru imagine: subiectul, formulat în engleză
    overrides: dict[str, str] = field(default_factory=dict)  # câmpuri venite din analiza unei imagini
    transfer: str = ""                 # ce s-a preluat din care imagine, la combinarea a două poze
    extra_negatives: list[str] = field(default_factory=list)
    must: list[str] = field(default_factory=list)   # cerințe obligatorii extra
    avoid: list[str] = field(default_factory=list)  # interdicții extra
    lang: str | None = None            # limba promptului; None = automat
    seed: int = 0
    min_words: int = DEFAULT_MIN_WORDS
    max_words: int = DEFAULT_MAX_WORDS

    def __post_init__(self) -> None:
        if not self.idea or not self.idea.strip():
            raise ValueError("Ideea nu poate fi goală.")
        self.idea = " ".join(self.idea.split())
        if self.mode not in (MODE_TEXT, MODE_IMAGE):
            raise ValueError(f"Mod necunoscut: {self.mode!r} (folosește 'text' sau 'image').")
        if self.lang is None:
            # Prompturile de text sunt implicit în română, cele de imagine în
            # engleză: modelele de imagine sunt antrenate pe termeni englezești.
            self.lang = "en" if self.mode == MODE_IMAGE else "ro"
        if self.lang not in ("ro", "en"):
            raise ValueError(f"Limbă nesuportată: {self.lang!r} (folosește 'ro' sau 'en').")
        if self.min_words < 50:
            raise ValueError("min_words trebuie să fie cel puțin 50.")
        if self.max_words <= self.min_words:
            raise ValueError("max_words trebuie să fie mai mare decât min_words.")


@dataclass
class Section:
    """O secțiune a promptului final.

    `priority` mai mic înseamnă mai important: la depășirea limitei de cuvinte
    se taie întâi secțiunile cu prioritate mare. `min_lines` este podeaua sub
    care o listă nu mai are sens — o listă de criterii cu un singur punct arată
    a text tăiat, nu a cerință. Când `min_lines` este 0, secțiunea poate
    dispărea de tot.
    """

    title: str
    lines: list[str]
    priority: int = 1
    bullet: str = ""       # "" = paragraf, "-" = listă, "1." = listă numerotată
    droppable: bool = False
    min_lines: int = 1
    lead: str = ""         # rând introductiv, nemarcat și niciodată tăiat


@dataclass
class GeneratedPrompt:
    """Rezultatul generării."""

    prompt: str
    mode: str
    domain: str
    target: str
    word_count: int
    variant: int = 1
    negative_prompt: str = ""
    parameters: str = ""
    notes: list[str] = field(default_factory=list)
    refined_by: str = ""   # numele modelului, dacă promptul a trecut prin --refine

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def full_text(self) -> str:
        """Promptul plus anexele (negative prompt, parametri), gata de copiat."""
        parts = [self.prompt.strip()]
        if self.negative_prompt:
            parts.append(f"Negative prompt: {self.negative_prompt}")
        if self.parameters:
            parts.append(self.parameters)
        return "\n\n".join(parts)
