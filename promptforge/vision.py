"""Analiza imaginilor și a paginilor web, ca sursă pentru prompturi.

Modelul e folosit doar ca ochi: descrie ce vede, într-un set fix de câmpuri.
Promptul final e construit tot de motorul local, din câmpurile primite — așa
păstrăm structura, formatul potrivit modelului-țintă și limita de cuvinte,
care sunt garanții pe care un răspuns liber nu le-ar da.
"""

from __future__ import annotations

import json
import re

from .llm import DEFAULT_EFFORT, DEFAULT_MODEL, ModelUnavailable, Sender, resolve_sender
from .media import ImageRef, PageRef
from .vocab import IMAGE_DOMAINS

# Câmpurile pe care le cerem modelului. Corespund exact blocurilor din
# `image_engine`, ca să poată fi folosite direct ca suprascrieri.
FIELDS = (
    "subject", "environment", "composition", "camera", "lens", "lighting",
    "palette", "mood", "style", "detail", "extra",
)

_SYSTEM = """\
Ești director de imagine și analizezi fotografii pentru a reconstrui promptul \
care le-ar putea produce.

Descrii doar ce se vede. Nu inventezi detalii care nu sunt în imagine și nu \
presupui context din afara cadrului. Când un element nu poate fi determinat \
(de exemplu obiectivul folosit), dai estimarea cea mai plauzibilă pe baza \
perspectivei și a adâncimii de câmp, nu o certitudine.

Scrii în engleză, cu vocabular tehnic de fotografie: modelele de imagine sunt \
antrenate pe engleză, iar termenii de optică și de iluminare nu se traduc.

Nu identifici persoane reale după nume și nu deduci identitatea cuiva dintr-o \
fotografie. Descrii aparența vizibilă, atât.

Răspunzi exclusiv cu un obiect JSON valid, fără text în jurul lui.\
"""

_SCHEMA = """\
Răspunde cu un singur obiect JSON, cu exact aceste chei:

{
  "domain": "unul dintre: %(domains)s",
  "subject": "subiectul principal, descris în 25-45 de cuvinte, concret și vizual",
  "environment": "decorul și fundalul, 15-30 de cuvinte",
  "composition": "încadrarea și așezarea în cadru, 15-30 de cuvinte",
  "camera": "tipul de cadru și unghiul, 10-20 de cuvinte",
  "lens": "estimarea obiectivului și a diafragmei, ex. '85mm at f/1.8, shallow depth of field'",
  "lighting": "schema de lumini: direcție, calitate, sursă, 15-30 de cuvinte",
  "palette": "paleta cromatică, cu nuanțe numite, 15-30 de cuvinte",
  "mood": "atmosfera, 3-8 cuvinte",
  "style": "stilul și mediul, 10-25 de cuvinte",
  "detail": "textura și nivelul de detaliu, 10-25 de cuvinte",
  "extra": "un singur detaliu care contează și nu intră mai sus",
  "aspect": "raportul de aspect observat, ex. '3:2'",
  "negative": ["3-6 defecte de evitat la regenerare"],
  "transfer": "ÎN ROMÂNĂ: ce ai luat din care imagine; șir gol dacă e o singură imagine"
}
""" % {"domains": ", ".join(sorted(IMAGE_DOMAINS))}


class VisionError(RuntimeError):
    """Analiza a rulat, dar răspunsul nu a putut fi folosit."""


def _extract_json(raw: str) -> dict:
    """Scoate obiectul JSON din răspuns, tolerând text sau garduri în jur."""
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise VisionError(f"Modelul nu a răspuns cu JSON. A răspuns: {raw[:200]}")
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise VisionError(f"JSON invalid de la model: {exc}") from exc
    if not isinstance(parsed, dict):
        raise VisionError("Modelul a răspuns cu JSON, dar nu cu un obiect.")
    return parsed


def _clean(parsed: dict) -> dict:
    """Păstrează doar câmpurile cunoscute și le aduce la tipurile așteptate."""
    result: dict[str, object] = {}

    for field in FIELDS:
        value = parsed.get(field)
        if isinstance(value, str) and value.strip():
            result[field] = " ".join(value.split())

    domain = parsed.get("domain")
    if isinstance(domain, str) and domain.strip() in IMAGE_DOMAINS:
        result["domain"] = domain.strip()

    aspect = parsed.get("aspect")
    if isinstance(aspect, str) and re.fullmatch(r"\d{1,2}:\d{1,2}", aspect.strip()):
        result["aspect"] = aspect.strip()

    negative = parsed.get("negative")
    if isinstance(negative, list):
        cleaned = [" ".join(str(item).split()) for item in negative if str(item).strip()]
        if cleaned:
            result["negative"] = cleaned[:8]

    transfer = parsed.get("transfer")
    if isinstance(transfer, str) and transfer.strip():
        result["transfer"] = " ".join(transfer.split())

    if not any(field in result for field in FIELDS):
        raise VisionError("Răspunsul modelului nu conținea niciun câmp util.")
    return result


def _instruction_block(images: list[ImageRef], instruction: str) -> str:
    lines = [
        f"Ai primit {len(images)} " + ("imagine." if len(images) == 1 else "imagini, în ordine."),
    ]
    for image in images:
        lines.append(f"- {image.label}: {image.origin}")

    if instruction:
        lines += [
            "",
            "Instrucțiunea utilizatorului, care are prioritate asupra a ce vezi:",
            instruction,
            "",
            "Construiește un singur set de câmpuri care descrie imaginea CERUTĂ de "
            "instrucțiune, nu una dintre cele primite: combină elementele indicate "
            "din fiecare imagine. În câmpul „transfer” scrie, într-o propoziție, ce "
            "ai luat din care imagine.",
        ]
    elif len(images) > 1:
        lines += [
            "",
            "Nu ai primit o instrucțiune de combinare. Descrie prima imagine și "
            "folosește-le pe celelalte doar ca referință de stil.",
        ]
    else:
        lines += [
            "",
            "Descrie această imagine astfel încât un model generativ să poată "
            "produce una echivalentă.",
        ]

    return "\n".join(lines)


def analyze_images(
    images: list[ImageRef],
    instruction: str = "",
    *,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    sender: Sender | None = None,
) -> dict:
    """Analizează una sau mai multe imagini și întoarce câmpurile descriptive.

    Cu mai multe imagini și o instrucțiune de tipul «ia lumina din prima și
    pune-o peste subiectul din a doua», câmpurile întoarse descriu deja
    rezultatul combinat.
    """
    if not images:
        raise VisionError("Nu am primit nicio imagine de analizat.")

    send = resolve_sender(sender)
    content: list[dict] = []
    for image in images:
        content.append({"type": "text", "text": f"[{image.label}]"})
        content.append(image.to_block())
    content.append({"type": "text", "text": _instruction_block(images, instruction)})
    content.append({"type": "text", "text": _SCHEMA})

    raw = send(system=_SYSTEM, content=content, model=model, effort=effort)
    return _clean(_extract_json(raw))


def analyze_page(
    page: PageRef,
    *,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    sender: Sender | None = None,
) -> dict:
    """Propune câmpurile unei imagini care ar ilustra o pagină web."""
    send = resolve_sender(sender)
    content = [{
        "type": "text",
        "text": (
            f"Pagina: {page.origin}\nTitlu: {page.title}\n\n"
            f"Conținut:\n{page.text}\n\n"
            "Propune imaginea care ar ilustra cel mai bine acest conținut și "
            "descrie-o în câmpurile de mai jos. Câmpul „transfer” rămâne gol."
        ),
    }, {"type": "text", "text": _SCHEMA}]
    raw = send(system=_SYSTEM, content=content, model=model, effort=effort)
    return _clean(_extract_json(raw))


__all__ = [
    "analyze_images",
    "analyze_page",
    "VisionError",
    "ModelUnavailable",
    "FIELDS",
]
