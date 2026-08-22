"""Fluxul complet: de la poze și linkuri până la promptul final.

Leagă cele trei straturi — încărcarea surselor (`media`), analiza cu modelul
(`vision`) și generarea locală (`image_engine` / `text_engine`).

Analiza dă doar câmpurile descriptive; promptul este construit tot local, din
ele. Așa păstrăm structura, formatul cerut de modelul-țintă și limita de
cuvinte, indiferent cât de liber ar fi răspuns modelul.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import generate_many
from .llm import DEFAULT_EFFORT, DEFAULT_MODEL, Sender
from .media import ImageRef, MediaError, PageRef, load_source
from .models import Brief, GeneratedPrompt, MODE_IMAGE, MODE_TEXT
from .vision import VisionError, analyze_images, analyze_page


@dataclass
class SourceBundle:
    """Sursele încărcate, separate pe tipuri."""

    images: list[ImageRef]
    pages: list[PageRef]

    @property
    def empty(self) -> bool:
        return not self.images and not self.pages

    def describe(self) -> str:
        parts = []
        if self.images:
            parts.append(f"{len(self.images)} " + ("imagine" if len(self.images) == 1 else "imagini"))
        if self.pages:
            parts.append(f"{len(self.pages)} " + ("pagină" if len(self.pages) == 1 else "pagini"))
        return " și ".join(parts)


def load_all(sources: list[str]) -> SourceBundle:
    """Încarcă sursele date, oricare ar fi ele, și le grupează."""
    if not sources:
        raise MediaError("Nu ai dat nicio sursă.")

    images: list[ImageRef] = []
    pages: list[PageRef] = []
    for index, source in enumerate(sources, start=1):
        loaded = load_source(source, label=f"imaginea {index}")
        if isinstance(loaded, PageRef):
            pages.append(loaded)
            # O pagină cu imagine de previzualizare aduce și imaginea în analiză.
            if loaded.preview_image:
                images.append(
                    ImageRef(
                        label=f"imaginea {len(images) + 1}",
                        origin=loaded.preview_image,
                        url=loaded.preview_image,
                    )
                )
        else:
            loaded.label = f"imaginea {len(images) + 1}"
            images.append(loaded)

    return SourceBundle(images=images, pages=pages)


def analyze(
    bundle: SourceBundle,
    instruction: str = "",
    *,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    sender: Sender | None = None,
) -> dict:
    """Obține câmpurile descriptive din surse."""
    if bundle.images:
        return analyze_images(
            bundle.images, instruction, model=model, effort=effort, sender=sender
        )
    if bundle.pages:
        return analyze_page(bundle.pages[0], model=model, effort=effort, sender=sender)
    raise VisionError("Nu am nimic de analizat.")


def brief_from_analysis(
    fields: dict,
    bundle: SourceBundle,
    instruction: str = "",
    *,
    mode: str = MODE_IMAGE,
    **options,
) -> Brief:
    """Construiește briefull pornind de la câmpurile obținute din analiză."""
    idea = instruction.strip() or fields.get("subject") or bundle.describe() or "sursă vizuală"

    if mode == MODE_IMAGE:
        overrides = {
            key: value for key, value in fields.items()
            if isinstance(value, str) and key not in ("transfer", "negative")
        }
        return Brief(
            idea=idea,
            mode=MODE_IMAGE,
            overrides=overrides,
            transfer=fields.get("transfer", ""),
            extra_negatives=list(fields.get("negative", [])),
            **options,
        )

    # Pentru un prompt de text, analiza e doar contextul din care pornim.
    context = fields.get("subject", "")
    if bundle.pages:
        page = bundle.pages[0]
        context = f"{page.title}. {page.text[:800]}".strip(". ")
    combined = f"{idea} — pe baza următorului context: {context}" if context else idea
    return Brief(idea=combined, mode=MODE_TEXT, **options)


def from_bundle(
    bundle: SourceBundle,
    instruction: str = "",
    *,
    mode: str = MODE_IMAGE,
    variants: int = 1,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    sender: Sender | None = None,
    **options,
) -> tuple[Brief, list[GeneratedPrompt]]:
    """Ca `from_sources`, dar pentru surse deja încărcate.

    Interfața web primește pozele direct din formular, deci nu are ce încărca
    de pe disc sau din rețea.
    """
    fields = analyze(bundle, instruction, model=model, effort=effort, sender=sender)
    brief = brief_from_analysis(fields, bundle, instruction, mode=mode, **options)
    results = generate_many(brief, variants)

    origin = ", ".join([image.origin for image in bundle.images] +
                       [page.origin for page in bundle.pages])
    for result in results:
        result.notes.insert(0, f"Generat din {bundle.describe()}: {origin}")
    return brief, results


def from_sources(
    sources: list[str],
    instruction: str = "",
    **kwargs,
) -> tuple[Brief, list[GeneratedPrompt]]:
    """Poze sau linkuri, plus o instrucțiune, în prompturi gata de folosit.

    `instruction` e locul în care spui ce vrei: «ia lumina și paleta din
    imaginea 1 și pune-le peste subiectul din imaginea 2».
    """
    return from_bundle(load_all(sources), instruction, **kwargs)
